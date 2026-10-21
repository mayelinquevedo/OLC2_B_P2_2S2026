import struct
from math import prod

from compiler.ast.nodos import Identificador, AccesoIndice, Arreglo, Literal
from compiler.codegen.rutinas import (RUTINAS, DEPENDENCIAS, MENSAJES_ERROR,
                                      ORDEN_RUTINAS, HEAP_BYTES)
from compiler.formato import partir_formato

CONDICIONES = {"==": "eq", "!=": "ne", "<": "lt", ">": "gt", "<=": "le", ">=": "ge"}
# para fcmp: "menor que" es mi y "menor o igual" es ls (asi se comporta bien con NaN)
CONDICIONES_F64 = {"==": "eq", "!=": "ne", "<": "mi", "<=": "ls", ">": "gt", ">=": "ge"}
ENTEROS = ("i32", "bool", "char")          # viajan en x0
TIPOS_ESCALARES = ("i32", "bool", "char", "f64", "String")   # f64 viaja en d0; String es un puntero en x0
COMPARABLES_ENTEROS = {("i32", "i32"), ("bool", "bool"), ("char", "char"),
                       ("i32", "char"), ("char", "i32")}
ESCAPES_CHAR = {"n": 10, "t": 9, "r": 13, "0": 0, "\\": 92, "'": 39, '"': 34}


def codigo_char(valor):
    """El lexer entrega el contenido del literal tal cual: 'a' -> 'a', '\\n' -> dos caracteres."""
    if len(valor) == 2 and valor[0] == "\\" and valor[1] in ESCAPES_CHAR:
        return ESCAPES_CHAR[valor[1]]
    return ord(valor)


# rutina "pe_*" que imprime un elemento (por su direccion) segun el tipo del elemento
RUTINA_ELEMENTO = {"i32": "pe_i32", "bool": "pe_bool", "char": "pe_char",
                   "f64": "pe_f64", "String": "pe_str"}
MODO_CONTAINS = {"f64": 1, "String": 2}      # 0 = entero/bool/char


def es_slice(tipo):
    """'&[i32]' -> True. Un slice es un puntero (x0) a un descriptor [longitud][datos]."""
    return isinstance(tipo, str) and tipo.startswith("&[")


def es_arreglo(tipo):
    return bool(dims_arreglo(tipo)[1])


def es_valor(tipo):
    """Tipos que viajan en un registro y ocupan un solo slot de 8 bytes."""
    return tipo in TIPOS_ESCALARES or es_slice(tipo)

MAX_PARAMETROS = 8
BYTES_ELEMENTO = 8


def escapar_ascii(texto):
    """Convierte un string de Python al contenido de una directiva .ascii.
    Devuelve (texto_escapado, cantidad_de_bytes)."""
    datos = texto.encode("utf-8")
    partes = []
    for b in datos:
        if b == 10:
            partes.append("\\n")
        elif b == 34:
            partes.append('\\"')
        elif b == 92:
            partes.append("\\\\")
        elif 32 <= b < 127:
            partes.append(chr(b))
        else:
            partes.append("\\%03o" % b)
    return "".join(partes), len(datos)


def dims_arreglo(tipo):
    """'[[i32; 3]; 2]' -> ('i32', [2, 3]).  Si no es arreglo -> (tipo, [])."""
    dims = []
    while isinstance(tipo, str) and tipo.startswith("["):
        i = tipo.rfind(";")
        dims.append(int(tipo[i + 1:-1]))
        tipo = tipo[1:i]
    return tipo, dims


def hojas_arreglo(nodo):
    """Elementos escalares de un literal de arreglo, en orden row-major."""
    resultado = []
    for e in nodo.elementos:
        if isinstance(e, Arreglo):
            resultado += hojas_arreglo(e)
        else:
            resultado.append(e)
    return resultado


class GeneradorARM64:
    def __init__(self):
        self.datos = []
        self.texto = []
        self.num_strings = 0
        self.num_etiquetas = 0
        self.usadas = set()
        self.scopes = []
        self.offset = 0
        self.max_offset = 0
        self.bucles = []
        self.etiqueta_retorno = None


    def __getattr__(self, nombre):
        if nombre.startswith("visitar_"):
            def no_implementado(nodo):
                raise NotImplementedError(f"El generador aun no soporta {nombre[8:]}")
            return no_implementado
        raise AttributeError(nombre)

    # ---- utilidades para emitir codigo ----
    def emitir(self, instruccion):
        self.texto.append("    " + instruccion)

    def comentario(self, texto):
        self.texto.append("    # " + texto)

    def etiqueta(self, nombre):
        self.texto.append(nombre + ":")

    def nueva_etiqueta(self, prefijo):
        self.num_etiquetas += 1
        return f".L{prefijo}_{self.num_etiquetas}"

    def usar(self, nombre):
        """Marca una rutina de apoyo (y las que necesita) para incluirla al final."""
        if nombre in self.usadas:
            return
        self.usadas.add(nombre)
        for dependencia in DEPENDENCIAS.get(nombre, []):
            self.usar(dependencia)

    def nuevo_string_valor(self, contenido):
        """Bloque de String en .data: [longitud: 8 bytes][bytes]. Devuelve su etiqueta."""
        nombre = f"str_{self.num_strings}"
        self.num_strings += 1
        escapado, largo = escapar_ascii(contenido)
        self.datos.append(".balign 8")
        self.datos.append(f"{nombre}: .quad {largo}")
        self.datos.append(f'    .ascii "{escapado}"')
        return nombre

    def cargar_direccion(self, reg, etiqueta):
        self.emitir(f"adrp {reg}, {etiqueta}")
        self.emitir(f"add {reg}, {reg}, :lo12:{etiqueta}")

    def cargar_string_vacio(self):
        self.usadas.add("str_vacio")
        self.cargar_direccion("x0", "str_vacio")

    def nuevo_string(self, contenido):
        nombre = f"str_{self.num_strings}"
        self.num_strings += 1
        escapado, largo = escapar_ascii(contenido)
        self.datos.append(f'{nombre}: .ascii "{escapado}"')
        return nombre, largo

    def escribir_texto(self, texto):
        self.comentario('escribir "' + texto.replace("\n", "\\n") + '"')
        nombre, largo = self.nuevo_string(texto)
        self.emitir("mov x0, #1")
        self.emitir(f"adrp x1, {nombre}")
        self.emitir(f"add x1, x1, :lo12:{nombre}")
        self.emitir(f"mov x2, #{largo}")
        self.emitir("mov x8, #64")
        self.emitir("svc #0")


    def cargar_inmediato(self, reg, valor):
        if valor <= 0xFFFF:
            self.emitir(f"mov {reg}, #{valor}")
        else:
            self.emitir(f"movz {reg}, #{valor & 0xFFFF}")
            self.emitir(f"movk {reg}, #{(valor >> 16) & 0xFFFF}, lsl #16")

    def direccion_local(self, reg, offset):
        """reg = x29 - offset (direccion de un slot del frame)."""
        if offset <= 4095:
            self.emitir(f"sub {reg}, x29, #{offset}")
        else:
            self.cargar_inmediato("x9", offset)
            self.emitir(f"sub {reg}, x29, x9")

    def cargar_local(self, reg, offset, nota=""):
        sufijo = f"    // {nota}" if nota else ""
        if offset <= 256:
            self.emitir(f"ldr {reg}, [x29, #-{offset}]{sufijo}")
        else:
            self.direccion_local("x9", offset)
            self.emitir(f"ldr {reg}, [x9]{sufijo}")

    def guardar_local(self, reg, offset):
        if offset <= 256:
            self.emitir(f"str {reg}, [x29, #-{offset}]")
        else:
            self.direccion_local("x9", offset)
            self.emitir(f"str {reg}, [x9]")

    def lineas_reserva_frame(self, tamano):
        if tamano <= 4095:
            return [f"    sub sp, sp, #{tamano}    // reservar espacio para variables locales"]
        lineas = []
        if tamano <= 0xFFFF:
            lineas.append(f"    mov x9, #{tamano}")
        else:
            lineas.append(f"    movz x9, #{tamano & 0xFFFF}")
            lineas.append(f"    movk x9, #{(tamano >> 16) & 0xFFFF}, lsl #16")
        lineas.append("    sub sp, sp, x9    // reservar espacio para variables locales")
        return lineas

    # ---- variables locales (stack) ----
    def entrar_scope(self):
        self.scopes.append({"vars": {}, "offset_previo": self.offset})

    def salir_scope(self):
        s = self.scopes.pop()
        self.offset = s["offset_previo"]

    def reservar(self, tamano):
        """Reserva 'tamano' bytes en el frame y devuelve el offset del slot.
        El slot ocupa [x29 - offset, x29 - offset + tamano)."""
        self.offset += tamano
        self.max_offset = max(self.max_offset, self.offset)
        return self.offset

    def registrar_variable(self, nombre, tipo, offset):
        self.scopes[-1]["vars"][nombre] = (offset, tipo)

    def declarar_variable(self, nombre, tipo):
        offset = self.reservar(8)
        self.registrar_variable(nombre, tipo, offset)
        return offset

    def buscar_variable(self, nombre):
        for s in reversed(self.scopes):
            if nombre in s["vars"]:
                return s["vars"][nombre]
        raise RuntimeError(f"variable '{nombre}' no encontrada en el generador")

    # ---- rutinas de error en ejecucion ----
    def rutina_error(self, etiqueta, mensaje):
        nombre, largo = self.nuevo_string(mensaje)
        return (f"{etiqueta}:\n"
                f"    mov x0, #1\n"
                f"    adrp x1, {nombre}\n"
                f"    add x1, x1, :lo12:{nombre}\n"
                f"    mov x2, #{largo}\n"
                f"    mov x8, #64\n"
                f"    svc #0\n"
                f"    mov x0, #1\n"
                f"    mov x8, #93\n"
                f"    svc #0\n")

    # ---- punto de entrada ----
    def generar(self, programa):
        programa.aceptar(self)
        rutinas = []
        for nombre in ORDEN_RUTINAS:
            if nombre in self.usadas:
                if nombre in MENSAJES_ERROR:
                    rutinas.append(self.rutina_error(nombre, MENSAJES_ERROR[nombre]))
                else:
                    rutinas.append(RUTINAS[nombre])
        datos = list(self.datos)
        if "print_bool" in self.usadas:
            datos += ['txt_true: .ascii "true"', 'txt_false: .ascii "false"']
        if "print_f64" in self.usadas:
            datos += ['txt_nan: .ascii "NaN"', 'txt_inf: .ascii "inf"', 'txt_ninf: .ascii "-inf"']
        if "str_vacio" in self.usadas:
            datos += [".balign 8", "str_vacio: .quad 0"]
        salida = ["# Codigo generado por OxigenNative", ".section .data"]
        salida += datos
        salida += [".section .text", ".global _start", "_start:",
                   "    bl fn_main",
                   "    mov x0, #0",
                   "    mov x8, #93",
                   "    svc #0", ""]
        salida += self.texto
        salida += rutinas
        if "heap_alloc" in self.usadas:
            salida += [".section .bss", ".balign 16",
                       f"heap_base: .skip {HEAP_BYTES}", "heap_ptr: .skip 8"]
        return "\n".join(salida) + "\n"

    # ---- estructura ----
    def visitar_Programa(self, nodo):
        for f in nodo.funciones:
            f.aceptar(self)

    def visitar_Function(self, nodo):
        self.scopes = []
        self.bucles = []
        self.offset = 0
        self.max_offset = 0
        self.etiqueta_retorno = f".Lret_{nodo.nombre}"
        self.comentario(f"----- inicio de la funcion {nodo.nombre} -----")
        self.etiqueta(f"fn_{nodo.nombre}")
        self.comentario("prologo: guardar frame pointer y link register")
        self.emitir("stp x29, x30, [sp, #-16]!")
        self.emitir("mov x29, sp")
        pos_reserva = len(self.texto)
        self.emitir("")
        self.entrar_scope()
        for reg, p in zip(self.registros_de([p.tipo for p in nodo.parametros]), nodo.parametros):
            offset = self.declarar_variable(p.nombre, p.tipo)
            self.guardar_local(reg, offset)
        nodo.cuerpo.aceptar(self)
        self.salir_scope()
        tamano = ((self.max_offset + 15) // 16) * 16
        if tamano:
            self.texto[pos_reserva] = "\n".join(self.lineas_reserva_frame(tamano))
        else:
            self.texto[pos_reserva] = "    # sin variables locales"
        self.etiqueta(self.etiqueta_retorno)
        self.comentario("epilogo: liberar variables, restaurar registros y retornar")
        self.emitir("mov sp, x29")
        self.emitir("ldp x29, x30, [sp], #16")
        self.emitir("ret")
        self.comentario(f"----- fin de la funcion {nodo.nombre} -----")

    def visitar_Bloque(self, nodo):
        self.entrar_scope()
        for s in nodo.sentencias:
            s.aceptar(self)
        self.salir_scope()

    def visitar_Return(self, nodo):
        self.comentario("return")
        if nodo.valor is not None:
            if not es_valor(nodo.valor.tipo_resultado):
                raise NotImplementedError(f"retornar {nodo.valor.tipo_resultado}: siguiente rebanada")
            nodo.valor.aceptar(self)      # el valor queda en x0 (o en d0 si es f64)
        self.emitir(f"b {self.etiqueta_retorno}")


    def direccion_de_arreglo(self, expr):
        """Deja en x0 la direccion del primer elemento de un arreglo (variable o fila de una matriz)."""
        if isinstance(expr, Identificador):
            offset, _ = self.buscar_variable(expr.nombre)
            self.direccion_local("x0", offset)
        elif isinstance(expr, AccesoIndice):
            _, restantes = self.calcular_direccion(expr)
            if not restantes:
                raise RuntimeError("se esperaba un arreglo y se obtuvo un elemento")
        else:
            raise NotImplementedError("usar este arreglo como valor: guardelo primero en una variable")

    # ---- llamadas a funciones del usuario ----
    def registros_de(self, tipos):
        """Registro que le toca a cada parametro/argumento (AAPCS64): los enteros
        usan x0..x7 y los f64 usan d0..d7, cada grupo con su propio contador."""
        regs = []
        ni = nf = 0
        for tipo in tipos:
            if tipo not in TIPOS_ESCALARES:
                raise NotImplementedError(f"parametros/argumentos de tipo {tipo}: siguiente rebanada")
            if tipo == "f64":
                regs.append(f"d{nf}")
                nf += 1
            else:
                regs.append(f"x{ni}")
                ni += 1
        if ni > MAX_PARAMETROS or nf > MAX_PARAMETROS:
            raise NotImplementedError("mas de 8 parametros de un mismo tipo: no soportado")
        return regs

    def evaluar_en_registros(self, nodos):
        """Evalua cada nodo (cada uno deja su valor en x0) y los reparte en x0, x1, ..."""
        for n in nodos:
            n.aceptar(self)
            self.emitir("str x0, [sp, #-16]!    // apilar argumento")
        for i in reversed(range(len(nodos))):
            self.emitir(f"ldr x{i}, [sp], #16")

    def visitar_LlamadaFuncion(self, nodo):
        if nodo.nombre == "String::from":
            nodo.argumentos[0].aceptar(self)       # el literal ya es un bloque String valido
            return
        if nodo.nombre == "String::new":
            self.cargar_string_vacio()
            return
        if nodo.nombre == "typeof":
            # el tipo se conoce al compilar: se devuelve como un String constante
            self.comentario("typeof")
            self.cargar_direccion("x0", self.nuevo_string_valor(str(nodo.argumentos[0].tipo_resultado)))
            return
        if nodo.nombre == "random":
            self.evaluar_en_registros(nodo.argumentos)
            self.usar("rt_random")
            self.emitir("bl rt_random")
            return
        if "::" in nodo.nombre:
            raise NotImplementedError(f"{nodo.nombre}: siguiente rebanada")
        regs = self.registros_de([a.tipo_resultado for a in nodo.argumentos])
        self.comentario(f"llamada a {nodo.nombre}")
        for a, reg in zip(nodo.argumentos, regs):
            a.aceptar(self)
            origen = "d0" if reg.startswith("d") else "x0"
            self.emitir(f"str {origen}, [sp, #-16]!    // apilar argumento")
        for reg in reversed(regs):
            self.emitir(f"ldr {reg}, [sp], #16")
        self.emitir(f"bl fn_{nodo.nombre}")

    # ---- declaraciones y asignaciones ----
    def visitar_DeclaracionVariable(self, nodo):
        if nodo.valor_inicial is not None:
            tipo = nodo.tipo or nodo.valor_inicial.tipo_resultado
        else:
            tipo = nodo.tipo
        elemento, dims = dims_arreglo(tipo)
        if dims:
            self.declarar_arreglo(nodo, tipo, elemento, dims)
            return
        if not es_valor(tipo):
            raise NotImplementedError(f"variables de tipo {tipo}: siguiente rebanada")
        self.comentario(f"let {'mut ' if nodo.mutable else ''}{nodo.nombre}: {tipo}")
        reg = "d0" if tipo == "f64" else "x0"
        if nodo.valor_inicial is not None:
            nodo.valor_inicial.aceptar(self)
        elif tipo == "String":
            self.cargar_string_vacio()    # un String sin valor inicial es ""
            reg = "x0"
        else:
            self.emitir("mov x0, #0")     # los bits en cero son 0, false, '\\0' y 0.0
            reg = "x0"
        # se declara DESPUES de evaluar el valor: "let x = x + 1" usa la x anterior
        offset = self.declarar_variable(nodo.nombre, tipo)
        self.guardar_local(reg, offset)

    def declarar_arreglo(self, nodo, tipo, elemento, dims):
        if elemento not in TIPOS_ESCALARES:
            raise NotImplementedError(f"arreglos de {elemento}: siguiente rebanada")
        total = prod(dims)
        self.comentario(f"let {'mut ' if nodo.mutable else ''}{nodo.nombre}: {tipo}  ({total} elementos, row-major)")
        # se reserva el espacio ANTES de evaluar y se registra el nombre DESPUES
        offset = self.reservar(total * BYTES_ELEMENTO)
        if nodo.valor_inicial is None:
            if elemento == "String":
                self.cargar_string_vacio()
            else:
                self.emitir("mov x0, #0")
            valores = [None] * total
        else:
            if not isinstance(nodo.valor_inicial, Arreglo):
                raise NotImplementedError("inicializar un arreglo con algo que no es un literal: siguiente rebanada")
            valores = hojas_arreglo(nodo.valor_inicial)
            if len(valores) != total:
                raise RuntimeError("el literal no coincide con las dimensiones declaradas")
        for k, hoja in enumerate(valores):
            reg = "x0"
            if hoja is not None:
                hoja.aceptar(self)
                if hoja.tipo_resultado == "f64":
                    reg = "d0"
            # el elemento k vive en la direccion base + k*8 = x29 - (offset - k*8)
            self.guardar_local(reg, offset - k * BYTES_ELEMENTO)
        self.registrar_variable(nodo.nombre, tipo, offset)

    def visitar_Asignacion(self, nodo):
        op = nodo.operador
        if isinstance(nodo.destino, Identificador):
            offset, tipo = self.buscar_variable(nodo.destino.nombre)
            if not es_valor(tipo):
                raise NotImplementedError(f"asignar a una variable de tipo {tipo}: siguiente rebanada")
            self.comentario(f"{nodo.destino.nombre} {op} ...")
            if tipo == "f64":
                # en "x += 1" el 1 (i32) se promueve a f64
                self.evaluar_como_f64(nodo.valor)
                if op != "=":
                    self.emitir("fmov d1, d0")
                    self.cargar_local("d0", offset)
                    self.operar_f64(op[0])
                self.guardar_local("d0", offset)
            else:
                nodo.valor.aceptar(self)
                if op != "=":
                    self.emitir("mov x1, x0")
                    self.cargar_local("x0", offset)
                    self.operar_generico(op[0], tipo, nodo.valor.tipo_resultado)
                self.guardar_local("x0", offset)
        elif isinstance(nodo.destino, AccesoIndice):
            tipo = nodo.destino.tipo_resultado
            if tipo not in TIPOS_ESCALARES:
                raise NotImplementedError(f"asignar elementos de tipo {tipo}: siguiente rebanada")
            es_f64 = (tipo == "f64")
            self.comentario(f"elemento de arreglo {op} ...")
            if es_f64:
                self.evaluar_como_f64(nodo.valor)
                self.emitir("str d0, [sp, #-16]!    // apilar el valor a asignar")
            else:
                nodo.valor.aceptar(self)
                self.emitir("str x0, [sp, #-16]!    // apilar el valor a asignar")
            _, restantes = self.calcular_direccion(nodo.destino)
            if restantes:
                raise NotImplementedError("asignar una fila completa: siguiente rebanada")
            self.emitir("mov x3, x0                // x3 = direccion del elemento")
            if es_f64:
                self.emitir("ldr d1, [sp], #16         // d1 = valor")
                if op == "=":
                    self.emitir("fmov d0, d1")
                else:
                    self.emitir("ldr d0, [x3]")
                    self.operar_f64(op[0])
                self.emitir("str d0, [x3]")
            else:
                self.emitir("ldr x1, [sp], #16         // x1 = valor")
                if op == "=":
                    self.emitir("mov x0, x1")
                else:
                    self.emitir("ldr x0, [x3]")
                    if tipo == "String":
                        # las rutinas de cadenas usan x3 como registro de trabajo:
                        # la direccion del elemento se guarda en la pila durante la llamada
                        self.emitir("str x3, [sp, #-16]!    // guardar la direccion del elemento")
                        self.operar_generico(op[0], tipo, nodo.valor.tipo_resultado)
                        self.emitir("ldr x3, [sp], #16")
                    else:
                        self.operar_generico(op[0], tipo, nodo.valor.tipo_resultado)
                self.emitir("str x0, [x3]")
        else:
            raise NotImplementedError("destino de asignacion no soportado")

    # ---- expresiones: el resultado queda siempre en x0 ----
    def cargar_f64(self, valor):
        """d0 = valor. Se arma el patron de 64 bits en x9 y se pasa a d0."""
        bits = struct.unpack("<Q", struct.pack("<d", valor))[0]
        if bits == 0:
            self.emitir("fmov d0, xzr")
            return
        self.emitir(f"movz x9, #{bits & 0xFFFF}")
        for desplazamiento in (16, 32, 48):
            trozo = (bits >> desplazamiento) & 0xFFFF
            if trozo:
                self.emitir(f"movk x9, #{trozo}, lsl #{desplazamiento}")
        self.emitir(f"fmov d0, x9    // {valor!r}")

    def evaluar_como_f64(self, expr):
        """Evalua expr y deja el resultado en d0 (si era i32, lo convierte)."""
        expr.aceptar(self)
        if expr.tipo_resultado == "i32":
            self.emitir("scvtf d0, x0    // promocion i32 -> f64")

    def visitar_Literal(self, nodo):
        if nodo.tipo == "bool":
            self.emitir(f"mov x0, #{1 if nodo.valor else 0}")
        elif nodo.tipo == "char":
            self.cargar_inmediato("x0", codigo_char(nodo.valor))
        elif nodo.tipo == "f64":
            self.cargar_f64(nodo.valor)
        elif nodo.tipo == "i32":
            self.cargar_inmediato("x0", nodo.valor)
        elif nodo.tipo == "String":
            self.cargar_direccion("x0", self.nuevo_string_valor(nodo.valor))
        else:
            raise NotImplementedError(f"literales {nodo.tipo}: siguiente rebanada")

    def visitar_Identificador(self, nodo):
        offset, tipo = self.buscar_variable(nodo.nombre)
        if not es_valor(tipo):
            raise NotImplementedError(f"usar '{nodo.nombre}' ({tipo}) como valor: use sus elementos o imprimalo con println!")
        self.cargar_local("d0" if tipo == "f64" else "x0", offset, nodo.nombre)


    def operar(self, op):
        """x0 = x0 (op) x1, con resultado recortado a i32."""
        if op == "+":
            self.emitir("add x0, x0, x1")
        elif op == "-":
            self.emitir("sub x0, x0, x1")
        elif op == "*":
            self.emitir("mul x0, x0, x1")
        elif op in ("/", "%"):
            self.usar("rt_div_cero")
            self.emitir("cbz x1, rt_div_cero    // division entre cero: error de ejecucion")
            if op == "/":
                self.emitir("sdiv x0, x0, x1")
            else:
                self.emitir("sdiv x2, x0, x1")
                self.emitir("msub x0, x2, x1, x0")
        else:
            raise NotImplementedError(f"operador {op}: siguiente rebanada")
        self.emitir("sxtw x0, w0")

    def operar_string(self, op, ti, td):
        """x0 = x0 (op) x1 cuando algun operando es String (x0 = izquierdo, x1 = derecho)."""
        if op == "+" and (ti, td) == ("String", "String"):
            self.usar("str_concat")
            self.emitir("bl str_concat")
        elif op == "*" and (ti, td) == ("String", "i32"):
            self.usar("str_repeat")
            self.emitir("bl str_repeat")
        elif op == "*" and (ti, td) == ("i32", "String"):
            self.usar("str_repeat")
            self.emitir("mov x2, x0")
            self.emitir("mov x0, x1")
            self.emitir("mov x1, x2")
            self.emitir("bl str_repeat")
        else:
            raise NotImplementedError(f"operador {op} entre {ti} y {td}: siguiente rebanada")

    def operar_generico(self, op, ti, td):
        if "String" in (ti, td):
            self.operar_string(op, ti, td)
        else:
            self.operar(op)

    def binaria_string(self, nodo, ti, td):
        op = nodo.operador
        nodo.izquierda.aceptar(self)
        self.emitir("str x0, [sp, #-16]!    // apilar operando izquierdo")
        nodo.derecha.aceptar(self)
        self.emitir("mov x1, x0")
        self.emitir("ldr x0, [sp], #16      // recuperar operando izquierdo")
        if op in CONDICIONES and (ti, td) == ("String", "String"):
            self.usar("str_cmp")
            self.emitir("bl str_cmp             // -1, 0 o 1")
            self.emitir("cmp x0, #0")
            self.emitir(f"cset x0, {CONDICIONES[op]}")
        else:
            self.operar_string(op, ti, td)

    def operar_f64(self, op):
        """d0 = d0 (op) d1."""
        if op == "+":
            self.emitir("fadd d0, d0, d1")
        elif op == "-":
            self.emitir("fsub d0, d0, d1")
        elif op == "*":
            self.emitir("fmul d0, d0, d1")
        elif op in ("/", "%"):
            self.usar("rt_div_cero")
            self.emitir("fcmp d1, #0.0")
            self.emitir("b.eq rt_div_cero    // division entre cero: error de ejecucion")
            if op == "/":
                self.emitir("fdiv d0, d0, d1")
            else:
                # a % b = a - trunc(a / b) * b
                self.emitir("fdiv d2, d0, d1")
                self.emitir("frintz d2, d2")
                self.emitir("fmsub d0, d2, d1, d0")
        else:
            raise NotImplementedError(f"operador {op}: siguiente rebanada")

    def binaria_f64(self, nodo):
        op = nodo.operador
        self.evaluar_como_f64(nodo.izquierda)
        self.emitir("str d0, [sp, #-16]!    // apilar operando izquierdo (f64)")
        self.evaluar_como_f64(nodo.derecha)
        self.emitir("fmov d1, d0")
        self.emitir("ldr d0, [sp], #16      // recuperar operando izquierdo")
        if op in CONDICIONES_F64:
            self.emitir("fcmp d0, d1")
            self.emitir(f"cset x0, {CONDICIONES_F64[op]}")
        else:
            self.operar_f64(op)

    def cortocircuito(self, nodo):
        fin = self.nueva_etiqueta("fin_logico")
        nodo.izquierda.aceptar(self)
        if nodo.operador == "&&":
            self.emitir(f"cbz x0, {fin}      // si es falso, el resultado ya es 0")
        else:
            self.emitir(f"cbnz x0, {fin}     // si es verdadero, el resultado ya es 1")
        nodo.derecha.aceptar(self)
        self.etiqueta(fin)

    def visitar_OperacionBinaria(self, nodo):
        op = nodo.operador
        if op in ("&&", "||"):
            self.cortocircuito(nodo)
            return
        ti = nodo.izquierda.tipo_resultado
        td = nodo.derecha.tipo_resultado
        if "String" in (ti, td):
            self.binaria_string(nodo, ti, td)
            return
        if "f64" in (ti, td):
            self.binaria_f64(nodo)
            return
        if op in CONDICIONES:
            if (ti, td) not in COMPARABLES_ENTEROS:
                raise NotImplementedError(f"comparar {ti} con {td}: siguiente rebanada")
        elif ti != "i32" or td != "i32":
            raise NotImplementedError("operaciones que no son entre i32: siguiente rebanada")
        nodo.izquierda.aceptar(self)
        self.emitir("str x0, [sp, #-16]!    // apilar operando izquierdo")
        nodo.derecha.aceptar(self)
        self.emitir("mov x1, x0")
        self.emitir("ldr x0, [sp], #16      // recuperar operando izquierdo")
        if op in CONDICIONES:
            self.emitir("cmp x0, x1")
            self.emitir(f"cset x0, {CONDICIONES[op]}")
        else:
            self.operar(op)

    def visitar_OperacionUnaria(self, nodo):
        t = nodo.operando.tipo_resultado
        if nodo.operador == "-" and t == "i32":
            nodo.operando.aceptar(self)
            self.emitir("neg x0, x0")
            self.emitir("sxtw x0, w0")
        elif nodo.operador == "-" and t == "f64":
            nodo.operando.aceptar(self)
            self.emitir("fneg d0, d0")
        elif nodo.operador == "!" and t == "bool":
            nodo.operando.aceptar(self)
            self.emitir("eor x0, x0, #1")
        else:
            raise NotImplementedError("operador unario: siguiente rebanada")

    # ---- arreglos ----
    def aplanar_acceso(self, nodo):
        """matrix[i][j] -> (Identificador matrix, [i, j])"""
        indices = []
        while isinstance(nodo, AccesoIndice):
            indices.insert(0, nodo.indice)
            nodo = nodo.arreglo
        return nodo, indices

    def indice_con_limite(self, expr, limite):
        """Evalua el indice en x0 y verifica en ejecucion que este en [0, limite)."""
        expr.aceptar(self)
        # un literal ya fue validado por el analisis semantico
        if not (isinstance(expr, Literal) and expr.tipo == "i32"):
            if limite <= 4095:
                self.emitir(f"cmp x0, #{limite}")
            else:
                self.cargar_inmediato("x9", limite)
                self.emitir("cmp x0, x9")
            self.emitir("b.hs rt_indice    // sin signo: tambien atrapa los negativos")
            self.usar("rt_indice")

    def calcular_direccion(self, nodo):
        """Deja en x0 la direccion de nodo (un acceso arr[i][j]...).
        Devuelve (tipo_elemento, dimensiones_que_quedan_sin_indexar).

        Row-major: indice_lineal = ((i1 * D2) + i2) * D3 + i3 ...
        direccion  = base + indice_lineal * 8"""
        base, indices = self.aplanar_acceso(nodo)
        if es_slice(base.tipo_resultado):
            return self.direccion_en_slice(base, indices)
        if not isinstance(base, Identificador):
            raise NotImplementedError("indexar algo que no es una variable: siguiente rebanada")
        offset, tipo = self.buscar_variable(base.nombre)
        elemento, dims = dims_arreglo(tipo)
        if not dims or len(indices) > len(dims):
            raise RuntimeError(f"'{base.nombre}' no se puede indexar {len(indices)} veces")
        self.comentario(f"direccion de {base.nombre}" + "".join("[..]" for _ in indices) + " (row-major)")
        self.indice_con_limite(indices[0], dims[0])
        for t in range(1, len(indices)):
            self.emitir("str x0, [sp, #-16]!    // apilar indice acumulado")
            self.indice_con_limite(indices[t], dims[t])
            self.emitir("mov x1, x0")
            self.emitir("ldr x0, [sp], #16")
            self.cargar_inmediato("x2", dims[t])
            self.emitir("mul x0, x0, x2")
            self.emitir("add x0, x0, x1         // acumulado * D + indice")
        restantes = dims[len(indices):]
        if restantes:
            self.cargar_inmediato("x2", prod(restantes))
            self.emitir("mul x0, x0, x2         // acceso parcial: saltar sub-arreglos completos")
        self.emitir("lsl x0, x0, #3             // * 8 bytes por elemento")
        self.direccion_local("x1", offset)
        self.emitir("add x0, x1, x0")
        return elemento, restantes

    def direccion_en_slice(self, base, indices):
        """x0 = direccion de slice[i]. El slice es un puntero a [longitud][datos]."""
        if len(indices) != 1:
            raise NotImplementedError("slices de varias dimensiones: siguiente rebanada")
        elemento = base.tipo_resultado[2:-1]
        self.comentario("direccion de slice[i] (con verificacion de limites)")
        base.aceptar(self)                          # x0 = descriptor
        self.emitir("str x0, [sp, #-16]!    // apilar descriptor del slice")
        indices[0].aceptar(self)                    # x0 = indice
        self.emitir("ldr x1, [sp], #16      // x1 = descriptor")
        self.emitir("ldr x2, [x1]           // x2 = longitud")
        self.emitir("cmp x0, x2")
        self.emitir("b.hs rt_indice         // sin signo: tambien atrapa los negativos")
        self.usar("rt_indice")
        self.emitir("ldr x3, [x1, #8]       // x3 = direccion del primer elemento")
        self.emitir("add x0, x3, x0, lsl #3")
        return elemento, []

    def visitar_Slice(self, nodo):
        """&arreglo[a..b]  ->  descriptor [longitud][direccion] en el heap (sin copiar elementos)."""
        tipo_base = nodo.arreglo.tipo_resultado
        base_es_slice = es_slice(tipo_base)
        if base_es_slice:
            elemento = tipo_base[2:-1]
        else:
            elemento, dims = dims_arreglo(tipo_base)
            if len(dims) != 1 or not isinstance(nodo.arreglo, Identificador):
                raise NotImplementedError("slices de matrices o de expresiones: siguiente rebanada")
        if elemento not in TIPOS_ESCALARES:
            raise NotImplementedError(f"slices de {elemento}: siguiente rebanada")
        self.comentario(f"slice &[{nodo.inicio}..{nodo.fin}] (vista del arreglo, sin copiar)")
        if base_es_slice:
            nodo.arreglo.aceptar(self)
            self.emitir("str x0, [sp, #-16]!    // apilar el slice original")
        nodo.inicio.aceptar(self)
        self.emitir("str x0, [sp, #-16]!    // apilar inicio")
        nodo.fin.aceptar(self)
        self.emitir("mov x1, x0             // x1 = fin")
        self.emitir("ldr x0, [sp], #16      // x0 = inicio")
        if base_es_slice:
            self.emitir("ldr x4, [sp], #16      // x4 = descriptor original")
            self.emitir("ldr x3, [x4]           // x3 = longitud")
            self.emitir("ldr x2, [x4, #8]       // x2 = datos")
        else:
            offset, _ = self.buscar_variable(nodo.arreglo.nombre)
            self.direccion_local("x2", offset)
            self.cargar_inmediato("x3", dims[0])
        self.usar("rt_indice")
        self.emitir("cmp x1, x3")
        self.emitir("b.hi rt_indice         // fin > longitud")
        self.emitir("cmp x0, x1")
        self.emitir("b.hi rt_indice         // inicio > fin")
        self.emitir("stp x0, x1, [sp, #-32]!")
        self.emitir("str x2, [sp, #16]")
        self.emitir("mov x0, #16            // el descriptor ocupa 16 bytes")
        self.usar("heap_alloc")
        self.emitir("bl heap_alloc")
        self.emitir("ldp x4, x5, [sp]")
        self.emitir("ldr x2, [sp, #16]")
        self.emitir("add sp, sp, #32")
        self.emitir("sub x6, x5, x4         // longitud = fin - inicio")
        self.emitir("str x6, [x0]")
        self.emitir("add x2, x2, x4, lsl #3 // datos = base + inicio * 8")
        self.emitir("str x2, [x0, #8]")
    def visitar_AccesoIndice(self, nodo):
        elemento, restantes = self.calcular_direccion(nodo)
        if restantes:
            raise NotImplementedError("usar una fila completa como valor: siguiente rebanada")
        self.emitir("ldr d0, [x0]" if elemento == "f64" else "ldr x0, [x0]")

    def metodo_string(self, nodo):
        m = nodo.nombre
        self.comentario(f"String.{m}()")
        if m == "len":
            nodo.objeto.aceptar(self)
            self.emitir("ldr x0, [x0]           // la longitud esta en el encabezado")
        elif m == "contains":
            self.evaluar_en_registros([nodo.objeto] + nodo.argumentos)
            self.usar("str_contains")
            self.emitir("bl str_contains")
        elif m in ("to_uppercase", "to_lowercase"):
            rutina = "str_upper" if m == "to_uppercase" else "str_lower"
            nodo.objeto.aceptar(self)
            self.usar(rutina)
            self.emitir(f"bl {rutina}")
        elif m == "replace":
            self.evaluar_en_registros([nodo.objeto] + nodo.argumentos)
            self.usar("str_replace")
            self.emitir("bl str_replace")
        else:
            raise NotImplementedError(f"String.{m}(): siguiente rebanada")
            
    def metodo_slice(self, nodo, tipo):
        m = nodo.nombre
        if m == "len":
            self.comentario("slice.len()")
            nodo.objeto.aceptar(self)
            self.emitir("ldr x0, [x0]           // la longitud esta en el descriptor")
        else:
            raise NotImplementedError(f"metodo {m} sobre {tipo}: siguiente rebanada")

    def visitar_LlamadaMetodo(self, nodo):
        tipo = nodo.objeto.tipo_resultado
        if tipo == "String":
            self.metodo_string(nodo)
            return
        elemento, dims = dims_arreglo(tipo)
        if es_slice(tipo):
            self.metodo_slice(nodo, tipo)
            return
        if dims and nodo.nombre == "len":
            # los arreglos tienen tamano fijo: la longitud se conoce al compilar
            self.comentario(f"len() = {dims[0]}")
            self.cargar_inmediato("x0", dims[0])
            return
        if dims and nodo.nombre == "reverse":
            if len(dims) != 1 or not isinstance(nodo.objeto, Identificador):
                raise NotImplementedError("reverse en arreglos multidimensionales: siguiente rebanada")
            n = dims[0]
            self.comentario(f"reverse() de {nodo.objeto.nombre}")
            if n < 2:
                return
            offset, _ = self.buscar_variable(nodo.objeto.nombre)
            inicio = self.nueva_etiqueta("rev_inicio")
            fin = self.nueva_etiqueta("rev_fin")
            self.direccion_local("x0", offset)
            self.cargar_inmediato("x9", (n - 1) * BYTES_ELEMENTO)
            self.emitir("add x2, x0, x9         // x0 = primer elemento, x2 = ultimo")
            self.etiqueta(inicio)
            self.emitir("cmp x0, x2")
            self.emitir(f"b.hs {fin}")
            self.emitir("ldr x3, [x0]")
            self.emitir("ldr x4, [x2]")
            self.emitir("str x4, [x0]")
            self.emitir("str x3, [x2]")
            self.emitir("add x0, x0, #8")
            self.emitir("sub x2, x2, #8")
            self.emitir(f"b {inicio}")
            self.etiqueta(fin)
            return
        raise NotImplementedError(f"metodo {nodo.nombre} sobre {tipo}: siguiente rebanada")

    # ---- control de flujo ----
    def visitar_If(self, nodo):
        fin = self.nueva_etiqueta("if_fin")
        nodo.condicion.aceptar(self)
        if nodo.bloque_sino is None:
            self.emitir(f"cbz x0, {fin}")
            nodo.bloque_entonces.aceptar(self)
        else:
            sino = self.nueva_etiqueta("if_else")
            self.emitir(f"cbz x0, {sino}")
            nodo.bloque_entonces.aceptar(self)
            self.emitir(f"b {fin}")
            self.etiqueta(sino)
            nodo.bloque_sino.aceptar(self)
        self.etiqueta(fin)

    def visitar_While(self, nodo):
        inicio = self.nueva_etiqueta("while_inicio")
        fin = self.nueva_etiqueta("while_fin")
        self.etiqueta(inicio)
        nodo.condicion.aceptar(self)
        self.emitir(f"cbz x0, {fin}")
        self.bucles.append({"etiqueta": None, "inicio": inicio, "fin": fin})
        nodo.bloque.aceptar(self)
        self.bucles.pop()
        self.emitir(f"b {inicio}")
        self.etiqueta(fin)

    def visitar_Loop(self, nodo):
        inicio = self.nueva_etiqueta("loop_inicio")
        fin = self.nueva_etiqueta("loop_fin")
        self.etiqueta(inicio)
        self.bucles.append({"etiqueta": nodo.etiqueta, "inicio": inicio, "fin": fin})
        nodo.bloque.aceptar(self)
        self.bucles.pop()
        self.emitir(f"b {inicio}")
        self.etiqueta(fin)

    def _buscar_bucle(self, etiqueta):
        if etiqueta is None:
            return self.bucles[-1]
        for b in reversed(self.bucles):
            if b["etiqueta"] == etiqueta:
                return b
        raise RuntimeError(f"etiqueta '{etiqueta}' no encontrada en el generador")

    def visitar_Break(self, nodo):
        self.comentario("break")
        self.emitir(f"b {self._buscar_bucle(nodo.etiqueta)['fin']}")

    def visitar_Continue(self, nodo):
        self.comentario("continue")
        self.emitir(f"b {self._buscar_bucle(nodo.etiqueta)['inicio']}")

    def visitar_Match(self, nodo):
        t = nodo.expresion.tipo_resultado
        if t not in ENTEROS:
            raise NotImplementedError(f"match sobre {t}: siguiente rebanada")
        fin = self.nueva_etiqueta("match_fin")
        self.comentario("match")
        # el valor evaluado se guarda en una variable local (no en la pila
        # temporal) para que un break/continue dentro de un caso no la desbalancee
        self.entrar_scope()
        offset = self.declarar_variable("$match", t)
        nodo.expresion.aceptar(self)
        self.guardar_local("x0", offset)
        for caso in nodo.casos:
            if caso.patron is None:
                self.comentario("caso comodin _")
                caso.bloque.aceptar(self)
                self.emitir(f"b {fin}")
            else:
                if caso.patron.tipo_resultado != t:
                    raise NotImplementedError("patron de otro tipo: siguiente rebanada")
                siguiente = self.nueva_etiqueta("match_sig")
                caso.patron.aceptar(self)
                self.cargar_local("x1", offset)
                self.emitir("cmp x1, x0")
                self.emitir(f"b.ne {siguiente}")
                caso.bloque.aceptar(self)
                self.emitir(f"b {fin}")
                self.etiqueta(siguiente)
        self.etiqueta(fin)
        self.salir_scope()
    # ---- println! ----
    def imprimir_slice(self, elemento):
        """x0 = descriptor del slice -> imprime [a, b, c]"""
        if elemento not in RUTINA_ELEMENTO:
            raise NotImplementedError(f"imprimir slices de {elemento}: siguiente rebanada")
        rutina = RUTINA_ELEMENTO[elemento]
        self.usar(rutina)
        self.usar("print_arr")
        self.emitir("ldr x1, [x0]           // cantidad de elementos")
        self.emitir("ldr x0, [x0, #8]       // direccion del primer elemento")
        self.emitir(f"adrp x2, {rutina}")
        self.emitir(f"add x2, x2, :lo12:{rutina}")
        self.emitir("bl print_arr")

    def imprimir_estatico(self, elemento, dims):
        """x0 = direccion de un arreglo (row-major) -> imprime [[1, 2], [3, 4]]"""
        if elemento not in RUTINA_ELEMENTO:
            raise NotImplementedError(f"imprimir arreglos de {elemento}: siguiente rebanada")
        if len(dims) == 1:
            rutina = RUTINA_ELEMENTO[elemento]
            self.usar(rutina)
            self.usar("print_arr")
            self.cargar_inmediato("x1", dims[0])
            self.emitir(f"adrp x2, {rutina}")
            self.emitir(f"add x2, x2, :lo12:{rutina}")
            self.emitir("bl print_arr")
            return
        paso = prod(dims[1:]) * BYTES_ELEMENTO       # bytes que ocupa cada sub-arreglo
        self.emitir("str x0, [sp, #-16]!    // apilar la direccion base")
        self.escribir_texto("[")
        for k in range(dims[0]):
            if k > 0:
                self.escribir_texto(", ")
            self.emitir("ldr x0, [sp]")
            if k > 0:
                self.cargar_inmediato("x9", k * paso)
                self.emitir("add x0, x0, x9")
            self.imprimir_estatico(elemento, dims[1:])
        self.escribir_texto("]")
        self.emitir("add sp, sp, #16")

    def imprimir_valor(self, arg, debug=False):
        """Evalua arg y lo imprime segun su tipo (sin salto de linea).
        Los arreglos y slices siempre se muestran como [a, b, c]."""
        tipo = arg.tipo_resultado
        if es_slice(tipo):
            arg.aceptar(self)
            self.imprimir_slice(tipo[2:-1])
            return
        elemento, dims = dims_arreglo(tipo)
        if dims:
            self.direccion_de_arreglo(arg)
            self.imprimir_estatico(elemento, dims)
            return
        arg.aceptar(self)
        if debug and tipo in ("String", "char"):
            # {:?}: String entre "..." y char entre '...'  (las rutinas pe_* reciben una direccion)
            rutina = RUTINA_ELEMENTO[tipo]
            self.usar(rutina)
            self.emitir("str x0, [sp, #-16]!")
            self.emitir("mov x0, sp")
            self.emitir(f"bl {rutina}")
            self.emitir("add sp, sp, #16")
            return
        rutina = {"i32": "print_int", "bool": "print_bool", "char": "print_char",
                  "f64": "print_f64", "String": "print_string"}.get(tipo)
        if rutina is None:
            raise NotImplementedError(f"imprimir valores {tipo}: siguiente rebanada")
        self.usar(rutina)
        self.emitir(f"bl {rutina}")

    def visitar_LlamadaPrintln(self, nodo):
        if nodo.formato is None:
            # println!(valor): sin cadena de formato, se imprimen los argumentos
            for i, arg in enumerate(nodo.argumentos):
                if i > 0:
                    self.escribir_texto(" ")
                self.imprimir_valor(arg)
            self.escribir_texto("\n")
            return
        piezas = partir_formato(nodo.formato)
        if sum(1 for tipo, _ in piezas if tipo == "arg") != len(nodo.argumentos):
            raise RuntimeError("marcadores y argumentos no coinciden")
        argumentos = iter(nodo.argumentos)
        pendiente = ""
        for tipo, valor in piezas:
            if tipo == "txt":
                pendiente += valor
                continue
            if pendiente:
                self.escribir_texto(pendiente)
                pendiente = ""
            self.imprimir_valor(next(argumentos), debug=valor)
        self.escribir_texto(pendiente + "\n")