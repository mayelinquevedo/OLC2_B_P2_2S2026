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


class GeneradorARM64:
    def __init__(self):
        self.datos = []
        self.texto = []
        self.num_strings = 0

    # utilidades para emitir codigo 
    def emitir(self, instruccion):
        self.texto.append("    " + instruccion)

    def comentario(self, texto):
        self.texto.append("    # " + texto)

    def etiqueta(self, nombre):
        self.texto.append(nombre + ":")

    def nuevo_string(self, contenido):
        nombre = f"str_{self.num_strings}"
        self.num_strings += 1
        escapado, largo = escapar_ascii(contenido)
        self.datos.append(f'{nombre}: .ascii "{escapado}"')
        return nombre, largo

    #  punto de entrada 
    def generar(self, programa):
        programa.aceptar(self)
        salida = ["# Codigo generado por OxigenNative", ".section .data"]
        salida += self.datos
        salida += [".section .text", ".global _start", "_start:",
                   "    bl fn_main",
                   "    mov x0, #0",
                   "    mov x8, #93",
                   "    svc #0", ""]
        salida += self.texto
        return "\n".join(salida) + "\n"

    #  visitantes 
    def visitar_Programa(self, nodo):
        for f in nodo.funciones:
            f.aceptar(self)

    def visitar_Function(self, nodo):
        self.comentario(f"----- inicio de la funcion {nodo.nombre} -----")
        self.etiqueta(f"fn_{nodo.nombre}")
        self.comentario("prologo: guardar frame pointer y link register")
        self.emitir("stp x29, x30, [sp, #-16]!")
        self.emitir("mov x29, sp")
        nodo.cuerpo.aceptar(self)
        self.comentario("epilogo: restaurar registros y retornar")
        self.emitir("ldp x29, x30, [sp], #16")
        self.emitir("ret")
        self.comentario(f"----- fin de la funcion {nodo.nombre} -----")

    def visitar_Bloque(self, nodo):
        for s in nodo.sentencias:
            s.aceptar(self)

    def visitar_LlamadaPrintln(self, nodo):
        if nodo.formato is None or nodo.argumentos:
            raise NotImplementedError("println! con argumentos se implementa en el siguiente paso")
        texto, _ = escapar_ascii(nodo.formato)
        self.comentario(f'println!("{texto}")')
        nombre, largo = self.nuevo_string(nodo.formato + "\n")
        self.emitir("mov x0, #1")
        self.emitir(f"adrp x1, {nombre}")
        self.emitir(f"add x1, x1, :lo12:{nombre}")
        self.emitir(f"mov x2, #{largo}")
        self.emitir("mov x8, #64")
        self.emitir("svc #0")
