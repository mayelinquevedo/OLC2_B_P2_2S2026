from compiler.ast.nodos import Identificador

CONDICIONES = {"==": "eq", "!=": "ne", "<": "lt", ">": "gt", "<=": "le", ">=": "ge"}
TIPOS_ESCALARES = ("i32", "bool")


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
        self.scopes = []
        self.offset = 0
        self.max_offset = 0
        self.bucles = []

    #  si aparece un nodo que aun no soportamos
    def __getattr__(self, nombre):
        if nombre.startswith("visitar_"):
            def no_implementado(nodo):
                raise NotImplementedError(f"El generador aun no soporta {nombre[8:]}")
            return no_implementado
        raise AttributeError(nombre)

    # utilidades para emitir codigo 
    def emitir(self, instruccion):
        self.texto.append("    " + instruccion)

    def comentario(self, texto):
        self.texto.append("    // " + texto)

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

    #variables locales (stack)
    def entrar_scope(self):
        self.scopes.append({"vars": {}, "offset_previo": self.offset})

    def salir_scope(self):
        s = self.scopes.pop()
        self.offset = s["offset_previo"]

    def declarar_variable(self, nombre, tipo):
        self.offset += 8
        self.max_offset = max(self.max_offset, self.offset)
        self.scopes[-1]["vars"][nombre] = (self.offset, tipo)
        return self.offset

    def buscar_variable(self, nombre):
        for s in reversed(self.scopes):
            if nombre in s["vars"]:
                return s["vars"][nombre]
        raise RuntimeError(f"variable '{nombre}' no encontrada en el generador")

    #  punto de entrada 
    def generar(self, programa):
        programa.aceptar(self)
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
        if self.usa_print_int:
            salida.append(RUTINA_PRINT_INT)
        if self.usa_print_bool:
            salida.append(RUTINA_PRINT_BOOL)
        return "\n".join(salida) + "\n"

    # estructura 
    def visitar_Programa(self, nodo):
        for f in nodo.funciones:
            f.aceptar(self)

    def visitar_Function(self, nodo):
        if nodo.parametros:
            raise NotImplementedError("parametros de funcion: siguiente rebanada")
        self.scopes = []
        self.bucles = []
        self.offset = 0
        self.max_offset = 0
        self.comentario(f"----- inicio de la funcion {nodo.nombre} -----")
        self.etiqueta(f"fn_{nodo.nombre}")
        self.comentario("prologo: guardar frame pointer y link register")
        self.emitir("stp x29, x30, [sp, #-16]!")
        self.emitir("mov x29, sp")
        pos_reserva = len(self.texto)
        self.emitir("")
        nodo.cuerpo.aceptar(self)
        tamano = ((self.max_offset + 15) // 16) * 16
        if tamano:
            self.texto[pos_reserva] = f"    sub sp, sp, #{tamano}    // reservar espacio para variables locales"
        else:
            self.texto[pos_reserva] = "    // sin variables locales"
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

    # declaraciones y asignaciones
    def visitar_DeclaracionVariable(self, nodo):
        if nodo.valor_inicial is not None:
            tipo = nodo.tipo or nodo.valor_inicial.tipo_resultado
        else:
            tipo = nodo.tipo
        if tipo not in TIPOS_ESCALARES:
            raise NotImplementedError(f"variables de tipo {tipo}: siguiente rebanada")
        self.comentario(f"let {'mut ' if nodo.mutable else ''}{nodo.nombre}: {tipo}")
        if nodo.valor_inicial is not None:
            nodo.valor_inicial.aceptar(self)
        else:
            self.emitir("mov x0, #0")
        # se declara DESPUES de evaluar el valor: "let x = x + 1" usa la x anterior
        offset = self.declarar_variable(nodo.nombre, tipo)
        self.emitir(f"str x0, [x29, #-{offset}]")

    def visitar_Asignacion(self, nodo):
        if not isinstance(nodo.destino, Identificador):
            raise NotImplementedError("asignar a elementos de arreglo: siguiente rebanada")
        offset, tipo = self.buscar_variable(nodo.destino.nombre)
        self.comentario(f"{nodo.destino.nombre} {nodo.operador} ...")
        nodo.valor.aceptar(self)
        if nodo.operador != "=":
            self.emitir("mov x1, x0")
            self.emitir(f"ldr x0, [x29, #-{offset}]")
            self.operar(nodo.operador[0])
        self.emitir(f"str x0, [x29, #-{offset}]")

    #  expresiones: el resultado queda siempre en x0 
    def visitar_Literal(self, nodo):
        if nodo.tipo == "bool":
            self.emitir(f"mov x0, #{1 if nodo.valor else 0}")
            return
        if nodo.tipo != "i32":
            raise NotImplementedError(f"literales {nodo.tipo}: siguiente rebanada")
        v = nodo.valor
        if v <= 0xFFFF:
            self.emitir(f"mov x0, #{v}")
        else:
            self.emitir(f"movz x0, #{v & 0xFFFF}")
            self.emitir(f"movk x0, #{(v >> 16) & 0xFFFF}, lsl #16")

    def visitar_Identificador(self, nodo):
        offset, tipo = self.buscar_variable(nodo.nombre)
        self.emitir(f"ldr x0, [x29, #-{offset}]    // {nodo.nombre}")

    def operar(self, op):
        """x0 = x0 (op) x1, con resultado recortado a i32."""
        if op == "+":
            self.emitir("add x0, x0, x1")
        elif op == "-":
            self.emitir("sub x0, x0, x1")
        elif op == "*":
            self.emitir("mul x0, x0, x1")
        elif op == "/":
            self.emitir("sdiv x0, x0, x1")
        elif op == "%":
            self.emitir("sdiv x2, x0, x1")
            self.emitir("msub x0, x2, x1, x0")
        else:
            raise NotImplementedError(f"operador {op}: siguiente rebanada")
        self.emitir("sxtw x0, w0")

    def cortocircuito(self, nodo):
        fin = self.nueva_etiqueta("fin_logico")
        nodo.izquierda.aceptar(self)
        if nodo.operador == "&&":
            self.emitir(f"cbz x0, {fin}    // si es falso, el resultado ya es 0")
        else:
            self.emitir(f"cbnz x0, {fin}    // si es verdadero, el resultado ya es 1")
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
        self.emitir("ldr x0, [sp], #16    // recuperar operando izquierdo")
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

    # control de flujo
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

    #  println! 
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
