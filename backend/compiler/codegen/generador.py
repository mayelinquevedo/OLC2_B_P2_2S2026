from math import prod

from compiler.ast.nodos import Identificador, AccesoIndice, Arreglo, Literal

CONDICIONES = {"==": "eq", "!=": "ne", "<": "lt", ">": "gt", "<=": "le", ">=": "ge"}
TIPOS_ESCALARES = ("i32", "bool")
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


RUTINA_PRINT_INT = """print_int:
    # imprime x0 como entero con signo, sin salto de linea
    stp x29, x30, [sp, #-16]!
    mov x29, sp
    sub sp, sp, #32
    mov x1, sp
    add x1, x1, #32
    mov x2, #0
    mov x3, #0
    cmp x0, #0
    b.ge 1f
    mov x3, #1
    neg x0, x0
1:
    mov x4, #10
2:
    udiv x5, x0, x4
    msub x6, x5, x4, x0
    add x6, x6, #48
    sub x1, x1, #1
    strb w6, [x1]
    add x2, x2, #1
    mov x0, x5
    cbnz x0, 2b
    cbz x3, 3f
    sub x1, x1, #1
    mov w6, #45
    strb w6, [x1]
    add x2, x2, #1
3:
    mov x0, #1
    mov x8, #64
    svc #0
    mov sp, x29
    ldp x29, x30, [sp], #16
    ret
"""

RUTINA_PRINT_BOOL = """print_bool:
    # imprime x0 como true o false, sin salto de linea
    cbz x0, 1f
    adrp x1, txt_true
    add x1, x1, :lo12:txt_true
    mov x2, #4
    b 2f
1:
    adrp x1, txt_false
    add x1, x1, :lo12:txt_false
    mov x2, #5
2:
    mov x0, #1
    mov x8, #64
    svc #0
    ret
"""


class GeneradorARM64:
    def __init__(self):
        self.datos = []
        self.texto = []
        self.num_strings = 0
        self.num_etiquetas = 0
        self.usa_print_int = False
        self.usa_print_bool = False
        self.usa_rt_div = False
        self.usa_rt_indice = False
        self.scopes = []
        self.offset = 0
        self.max_offset = 0
        self.bucles = []
        self.etiqueta_retorno = None

    # ---- si aparece un nodo que aun no soportamos, avisamos claro ----
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
        if self.usa_print_int:
            rutinas.append(RUTINA_PRINT_INT)
        if self.usa_print_bool:
            rutinas.append(RUTINA_PRINT_BOOL)
        if self.usa_rt_div:
            rutinas.append(self.rutina_error("rt_div_cero", "Error de ejecución: división entre cero\n"))
        if self.usa_rt_indice:
            rutinas.append(self.rutina_error("rt_indice", "Error de ejecución: índice fuera de los límites del arreglo\n"))
        datos = list(self.datos)
        if self.usa_print_bool:
            datos += ['txt_true: .ascii "true"', 'txt_false: .ascii "false"']
        salida = ["# Codigo generado por OxigenNative", ".section .data"]
        salida += datos
        salida += [".section .text", ".global _start", "_start:",
                   "    bl fn_main",
                   "    mov x0, #0",
                   "    mov x8, #93",
                   "    svc #0", ""]
        salida += self.texto
        salida += rutinas
        return "\n".join(salida) + "\n"

    # ---- estructura ----
    def visitar_Programa(self, nodo):
        for f in nodo.funciones:
            f.aceptar(self)

    def visitar_Function(self, nodo):
        if len(nodo.parametros) > MAX_PARAMETROS:
            raise NotImplementedError("mas de 8 parametros: no soportado")
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
        for i, p in enumerate(nodo.parametros):
            if p.tipo not in TIPOS_ESCALARES:
                raise NotImplementedError(f"parametros de tipo {p.tipo}: siguiente rebanada")
            offset = self.declarar_variable(p.nombre, p.tipo)
            self.guardar_local(f"x{i}", offset)
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
            if nodo.valor.tipo_resultado not in TIPOS_ESCALARES:
                raise NotImplementedError(f"retornar {nodo.valor.tipo_resultado}: siguiente rebanada")
            nodo.valor.aceptar(self)
        self.emitir(f"b {self.etiqueta_retorno}")

    # ---- llamadas a funciones del usuario ----
    def visitar_LlamadaFuncion(self, nodo):
        if "::" in nodo.nombre or nodo.nombre in ("typeof", "random"):
            raise NotImplementedError(f"{nodo.nombre}: siguiente rebanada")
        n = len(nodo.argumentos)
        if n > MAX_PARAMETROS:
            raise NotImplementedError("mas de 8 argumentos: no soportado")
        self.comentario(f"llamada a {nodo.nombre}")
        for a in nodo.argumentos:
            if a.tipo_resultado not in TIPOS_ESCALARES:
                raise NotImplementedError(f"argumentos {a.tipo_resultado}: siguiente rebanada")
            a.aceptar(self)
            self.emitir("str x0, [sp, #-16]!    // apilar argumento")
        for i in reversed(range(n)):
            self.emitir(f"ldr x{i}, [sp], #16")
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
        if tipo not in TIPOS_ESCALARES:
            raise NotImplementedError(f"variables de tipo {tipo}: siguiente rebanada")
        self.comentario(f"let {'mut ' if nodo.mutable else ''}{nodo.nombre}: {tipo}")
        if nodo.valor_inicial is not None:
            nodo.valor_inicial.aceptar(self)
        else:
            self.emitir("mov x0, #0")
        # se declara DESPUES de evaluar el valor: "let x = x + 1" usa la x anterior
        offset = self.declarar_variable(nodo.nombre, tipo)
        self.guardar_local("x0", offset)

    def declarar_arreglo(self, nodo, tipo, elemento, dims):
        if elemento not in TIPOS_ESCALARES:
            raise NotImplementedError(f"arreglos de {elemento}: siguiente rebanada")
        total = prod(dims)
        self.comentario(f"let {'mut ' if nodo.mutable else ''}{nodo.nombre}: {tipo}  ({total} elementos, row-major)")
        # se reserva el espacio ANTES de evaluar y se registra el nombre DESPUES
        offset = self.reservar(total * BYTES_ELEMENTO)
        if nodo.valor_inicial is None:
            self.emitir("mov x0, #0")
            valores = [None] * total
        else:
            if not isinstance(nodo.valor_inicial, Arreglo):
                raise NotImplementedError("inicializar un arreglo con algo que no es un literal: siguiente rebanada")
            valores = hojas_arreglo(nodo.valor_inicial)
            if len(valores) != total:
                raise RuntimeError("el literal no coincide con las dimensiones declaradas")
        for k, hoja in enumerate(valores):
            if hoja is not None:
                hoja.aceptar(self)
            # el elemento k vive en la direccion base + k*8 = x29 - (offset - k*8)
            self.guardar_local("x0", offset - k * BYTES_ELEMENTO)
        self.registrar_variable(nodo.nombre, tipo, offset)

    def visitar_Asignacion(self, nodo):
        if isinstance(nodo.destino, Identificador):
            offset, tipo = self.buscar_variable(nodo.destino.nombre)
            if tipo not in TIPOS_ESCALARES:
                raise NotImplementedError(f"asignar a una variable de tipo {tipo}: siguiente rebanada")
            self.comentario(f"{nodo.destino.nombre} {nodo.operador} ...")
            nodo.valor.aceptar(self)
            if nodo.operador != "=":
                self.emitir("mov x1, x0")
                self.cargar_local("x0", offset)
                self.operar(nodo.operador[0])
            self.guardar_local("x0", offset)
        elif isinstance(nodo.destino, AccesoIndice):
            self.comentario(f"elemento de arreglo {nodo.operador} ...")
            nodo.valor.aceptar(self)
            self.emitir("str x0, [sp, #-16]!    // apilar el valor a asignar")
            _, restantes = self.calcular_direccion(nodo.destino)
            if restantes:
                raise NotImplementedError("asignar una fila completa: siguiente rebanada")
            self.emitir("mov x3, x0                // x3 = direccion del elemento")
            self.emitir("ldr x1, [sp], #16         // x1 = valor")
            if nodo.operador == "=":
                self.emitir("mov x0, x1")
            else:
                self.emitir("ldr x0, [x3]")
                self.operar(nodo.operador[0])
            self.emitir("str x0, [x3]")
        else:
            raise NotImplementedError("destino de asignacion no soportado")

    # ---- expresiones: el resultado queda siempre en x0 ----
    def visitar_Literal(self, nodo):
        if nodo.tipo == "bool":
            self.emitir(f"mov x0, #{1 if nodo.valor else 0}")
            return
        if nodo.tipo != "i32":
            raise NotImplementedError(f"literales {nodo.tipo}: siguiente rebanada")
        self.cargar_inmediato("x0", nodo.valor)

    def visitar_Identificador(self, nodo):
        offset, tipo = self.buscar_variable(nodo.nombre)
        if tipo not in TIPOS_ESCALARES:
            raise NotImplementedError(f"usar '{nodo.nombre}' ({tipo}) como valor: siguiente rebanada")
        self.cargar_local("x0", offset, nodo.nombre)

    def operar(self, op):
        """x0 = x0 (op) x1, con resultado recortado a i32."""
        if op == "+":
            self.emitir("add x0, x0, x1")
        elif op == "-":
            self.emitir("sub x0, x0, x1")
        elif op == "*":
            self.emitir("mul x0, x0, x1")
        elif op in ("/", "%"):
            self.usa_rt_div = True
            self.emitir("cbz x1, rt_div_cero    // division entre cero: error de ejecucion")
            if op == "/":
                self.emitir("sdiv x0, x0, x1")
            else:
                self.emitir("sdiv x2, x0, x1")
                self.emitir("msub x0, x2, x1, x0")
        else:
            raise NotImplementedError(f"operador {op}: siguiente rebanada")
        self.emitir("sxtw x0, w0")

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
        if op in CONDICIONES:
            if (ti, td) not in (("i32", "i32"), ("bool", "bool")):
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
            self.usa_rt_indice = True

    def calcular_direccion(self, nodo):
        """Deja en x0 la direccion de nodo (un acceso arr[i][j]...).
        Devuelve (tipo_elemento, dimensiones_que_quedan_sin_indexar).

        Row-major: indice_lineal = ((i1 * D2) + i2) * D3 + i3 ...
        direccion  = base + indice_lineal * 8"""
        base, indices = self.aplanar_acceso(nodo)
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

    def visitar_AccesoIndice(self, nodo):
        _, restantes = self.calcular_direccion(nodo)
        if restantes:
            raise NotImplementedError("usar una fila completa como valor: siguiente rebanada")
        self.emitir("ldr x0, [x0]")

    def visitar_LlamadaMetodo(self, nodo):
        tipo = nodo.objeto.tipo_resultado
        elemento, dims = dims_arreglo(tipo)
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
        if t not in TIPOS_ESCALARES:
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
    def visitar_LlamadaPrintln(self, nodo):
        if nodo.formato is None:
            raise NotImplementedError("println! sin cadena de formato: siguiente rebanada")
        partes = nodo.formato.split("{}")
        if len(partes) - 1 != len(nodo.argumentos):
            raise RuntimeError("marcadores y argumentos no coinciden")
        for i, parte in enumerate(partes):
            ultimo = (i == len(partes) - 1)
            texto = parte + ("\n" if ultimo else "")
            if texto:
                self.escribir_texto(texto)
            if not ultimo:
                arg = nodo.argumentos[i]
                arg.aceptar(self)
                if arg.tipo_resultado == "i32":
                    self.usa_print_int = True
                    self.emitir("bl print_int")
                elif arg.tipo_resultado == "bool":
                    self.usa_print_bool = True
                    self.emitir("bl print_bool")
                else:
                    raise NotImplementedError(f"imprimir valores {arg.tipo_resultado}: siguiente rebanada")
