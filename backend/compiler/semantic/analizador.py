from compiler.errors import agregar_error
from compiler.semantic.tabla_simbolos import TablaSimbolos, Simbolo
from compiler.ast.nodos import Identificador, AccesoIndice

NUMERICOS = ('i32', 'f64')

COMPARABLES = {
    ('i32', 'i32'), ('i32', 'f64'), ('f64', 'i32'), ('f64', 'f64'),
    ('i32', 'char'), ('char', 'i32'), ('char', 'char'),
    ('bool', 'bool'), ('String', 'String'),
}


def valor_por_defecto(tipo):
    return {'i32': 0, 'f64': 0.0, 'bool': False, 'String': ''}.get(tipo)


def tipo_binario(op, izq, der):
    """Devuelve el tipo resultante segun las tablas del enunciado, o None si no es valido."""
    if op in ('+', '-', '*', '/', '%'):
        if izq in NUMERICOS and der in NUMERICOS:
            return 'f64' if 'f64' in (izq, der) else 'i32'
        if op == '+' and izq == 'String' and der == 'String':
            return 'String'
        if op == '*' and {izq, der} == {'i32', 'String'}:
            return 'String'
        return None
    if op in ('==', '!=', '<', '>', '<=', '>='):
        return 'bool' if (izq, der) in COMPARABLES else None
    if op in ('&&', '||'):
        return 'bool' if izq == 'bool' and der == 'bool' else None
    return None


class AnalizadorSemantico:
    def __init__(self):
        self.tabla = TablaSimbolos()
        self.funcion_actual = None

    def error(self, nodo, mensaje):
        agregar_error("Semantico", mensaje, nodo.linea, nodo.columna)

    def analizar(self, programa):
        programa.aceptar(self)

    def visitar_sentencias(self, sentencias):
        for s in sentencias:
            s.aceptar(self)

    # Programa y funciones 
    def visitar_Programa(self, nodo):
        # Pasada 1: registrar todas las funciones 
        for f in nodo.funciones:
            if self.tabla.existe_en_scope_actual(f.nombre):
                self.error(f, f"La función '{f.nombre}' ya fue declarada.")
                continue
            s = Simbolo(f.nombre, f.tipo_retorno or 'void', categoria="Funcion", linea=f.linea)
            s.parametros = f.parametros
            self.tabla.declarar(f.nombre, s)

        if sum(1 for f in nodo.funciones if f.nombre == 'main') != 1:
            self.error(nodo, "El programa debe definir una única función 'main'.")

        # Pasada 2: analizar cuerpos
        for f in nodo.funciones:
            f.aceptar(self)

    def visitar_Function(self, nodo):
        self.funcion_actual = nodo
        self.tabla.entrar_scope()
        for p in nodo.parametros:
            self.tabla.declarar(p.nombre, Simbolo(p.nombre, p.tipo, False, "Parametro", p.linea))
        self.visitar_sentencias(nodo.cuerpo.sentencias)
        self.tabla.salir_scope()
        self.funcion_actual = None

    def visitar_Bloque(self, nodo):
        self.tabla.entrar_scope()
        self.visitar_sentencias(nodo.sentencias)
        self.tabla.salir_scope()

    def visitar_Return(self, nodo):
        esperado = self.funcion_actual.tipo_retorno or 'void'
        obtenido = nodo.valor.aceptar(self) if nodo.valor is not None else 'void'
        if obtenido is not None and obtenido != esperado:
            self.error(nodo, f"La función '{self.funcion_actual.nombre}' debe retornar {esperado}, pero retorna {obtenido}.")

    #  Declaraciones y asignaciones 
    def visitar_DeclaracionVariable(self, nodo):
        tipo_valor = nodo.valor_inicial.aceptar(self) if nodo.valor_inicial is not None else None
        tipo = nodo.tipo

        if tipo is not None and nodo.valor_inicial is not None and tipo_valor is not None and tipo_valor != tipo:
            self.error(nodo, f"No es posible asignar un valor de tipo {tipo_valor} a una variable de tipo {tipo}.")
        elif tipo is None:
            if nodo.valor_inicial is None:
                self.error(nodo, f"No se puede inferir el tipo de '{nodo.nombre}': falta tipo o valor inicial.")
            tipo = tipo_valor  
        self.tabla.declarar(nodo.nombre, Simbolo(nodo.nombre, tipo, nodo.mutable, "Variable", nodo.linea))

    def _raiz(self, destino):
        while isinstance(destino, AccesoIndice):
            destino = destino.arreglo
        return destino

    def visitar_Asignacion(self, nodo):
        tipo_dest = nodo.destino.aceptar(self)
        tipo_val = nodo.valor.aceptar(self)

        raiz = self._raiz(nodo.destino)
        if isinstance(raiz, Identificador):
            s = self.tabla.buscar(raiz.nombre)
            if s is not None and not s.mutable:
                self.error(nodo, f"No es posible modificar la variable '{raiz.nombre}' porque fue declarada como inmutable.")

        if tipo_dest is None or tipo_val is None:
            return
        if nodo.operador == '=':
            if tipo_dest != tipo_val:
                self.error(nodo, f"No es posible asignar un valor de tipo {tipo_val} a una variable de tipo {tipo_dest}.")
        else:
            op = nodo.operador[0]  # '+=' -> '+'
            r = tipo_binario(op, tipo_dest, tipo_val)
            if r is None:
                self.error(nodo, f"No es posible aplicar el operador '{op}' entre los tipos {tipo_dest} y {tipo_val}.")
            elif r != tipo_dest:
                self.error(nodo, f"No es posible asignar un valor de tipo {r} a una variable de tipo {tipo_dest}.")

    #  Expresiones 
    def visitar_Literal(self, nodo):
        return nodo.tipo

    def visitar_Identificador(self, nodo):
        s = self.tabla.buscar(nodo.nombre)
        if s is None:
            self.error(nodo, f"La variable '{nodo.nombre}' no ha sido declarada.")
            return None
        return s.tipo

    def visitar_OperacionBinaria(self, nodo):
        izq = nodo.izquierda.aceptar(self)
        der = nodo.derecha.aceptar(self)
        if izq is None or der is None:
            return None
        r = tipo_binario(nodo.operador, izq, der)
        if r is None:
            self.error(nodo, f"No es posible aplicar el operador '{nodo.operador}' entre los tipos {izq} y {der}.")
        return r

    def visitar_OperacionUnaria(self, nodo):
        t = nodo.operando.aceptar(self)
        if t is None:
            return None
        if nodo.operador == '-' and t in NUMERICOS:
            return t
        if nodo.operador == '!' and t == 'bool':
            return 'bool'
        self.error(nodo, f"No es posible aplicar el operador '{nodo.operador}' al tipo {t}.")
        return None

    #  Llamadas
    def visitar_LlamadaFuncion(self, nodo):
        tipos_args = [a.aceptar(self) for a in nodo.argumentos]

        if nodo.nombre == 'String::new':
            return 'String'
        if nodo.nombre == 'String::from':
            if len(tipos_args) != 1 or (tipos_args[0] is not None and tipos_args[0] != 'String'):
                self.error(nodo, "String::from espera exactamente un argumento de tipo String.")
            return 'String'
        if nodo.nombre.startswith('String::'):
            self.error(nodo, f"El método '{nodo.nombre}' no existe.")
            return None

        s = self.tabla.buscar(nodo.nombre)
        if s is None or s.categoria != "Funcion":
            self.error(nodo, f"La función '{nodo.nombre}' no ha sido declarada.")
            return None

        if len(tipos_args) != len(s.parametros):
            self.error(nodo, f"La función '{nodo.nombre}' esperaba {len(s.parametros)} argumentos, pero recibió {len(tipos_args)}.")
        else:
            for param, t in zip(s.parametros, tipos_args):
                if t is not None and t != param.tipo:
                    self.error(nodo, f"El parámetro '{param.nombre}' de '{nodo.nombre}' espera {param.tipo}, pero recibió {t}.")
        return s.tipo

    def visitar_LlamadaPrintln(self, nodo):
        for a in nodo.argumentos:
            a.aceptar(self)
        if nodo.formato is not None:
            marcadores = nodo.formato.count('{}') + nodo.formato.count('{:?}')
            if marcadores != len(nodo.argumentos):
                self.error(nodo, f"println! tiene {marcadores} marcadores pero recibió {len(nodo.argumentos)} argumentos.")
        return 'void'