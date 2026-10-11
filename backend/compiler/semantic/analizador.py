from compiler.errors import agregar_error
from compiler.semantic.tabla_simbolos import TablaSimbolos, Simbolo
from compiler.ast.nodos import Identificador, AccesoIndice, Literal

NUMERICOS = ('i32', 'f64')

COMPARABLES = {
    ('i32', 'i32'), ('i32', 'f64'), ('f64', 'i32'), ('f64', 'f64'),
    ('i32', 'char'), ('char', 'i32'), ('char', 'char'),
    ('bool', 'bool'), ('String', 'String'),
}


def valor_por_defecto(tipo):
    return {'i32': 0, 'f64': 0.0, 'bool': False, 'String': ''}.get(tipo)

def info_arreglo(tipo):
    """Si el tipo es arreglo o slice devuelve (tipo_elemento, tamano); si no, None."""
    if tipo is None:
        return None
    if tipo.startswith('&['):          # slice: &[i32]
        return tipo[2:-1], None
    if tipo.startswith('['):           # arreglo: [i32; 5] o [[i32; 3]; 2]
        i = tipo.rfind(';')
        return tipo[1:i], int(tipo[i + 1:-1])
    return None

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
    anota_tipos = True

    def __init__(self):
        self.tabla = TablaSimbolos()
        self.funcion_actual = None
        self.bucles = []

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
        self.tabla.ambito_actual = nodo.nombre
        self.tabla.entrar_scope()
        for p in nodo.parametros:
            self.tabla.declarar(p.nombre, Simbolo(p.nombre, p.tipo, False, "Parametro", p.linea))
        self.visitar_sentencias(nodo.cuerpo.sentencias)
        self.tabla.salir_scope()
        self.tabla.ambito_actual = "Global"
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
            self.error(nodo.valor_inicial, f"No es posible asignar un valor de tipo {tipo_valor} a una variable de tipo {tipo}.")
        elif tipo is None:
            if nodo.valor_inicial is None:
                self.error(nodo, f"No se puede inferir el tipo de '{nodo.nombre}': falta tipo o valor inicial.")
            tipo = tipo_valor

        if nodo.valor_inicial is None:
            valor = valor_por_defecto(tipo)
        elif isinstance(nodo.valor_inicial, Literal):
            valor = nodo.valor_inicial.valor
        else:
            valor = None
        self.tabla.declarar(nodo.nombre, Simbolo(nodo.nombre, tipo, nodo.mutable, "Variable", nodo.linea, valor))
    
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

        if nodo.nombre == 'typeof':
            if len(tipos_args) != 1:
                self.error(nodo, "typeof espera exactamente un argumento.")
            return 'String'
        if nodo.nombre == 'random':
            if len(tipos_args) != 2 or any(t not in (None, 'i32') for t in tipos_args):
                self.error(nodo, "random espera dos argumentos de tipo i32.")
            return 'i32'

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


    def _exigir_bool(self, expr, nombre):
        t = expr.aceptar(self)
        if t is not None and t != 'bool':
            self.error(expr, f"La condición del {nombre} debe ser de tipo bool, pero es {t}.")

    def visitar_If(self, nodo):
        self._exigir_bool(nodo.condicion, "if")
        nodo.bloque_entonces.aceptar(self)
        if nodo.bloque_sino is not None:
            nodo.bloque_sino.aceptar(self)

    def visitar_While(self, nodo):
        self._exigir_bool(nodo.condicion, "while")
        self.bucles.append(None)
        nodo.bloque.aceptar(self)
        self.bucles.pop()

    def visitar_Loop(self, nodo):
        self.bucles.append(nodo.etiqueta)
        nodo.bloque.aceptar(self)
        self.bucles.pop()

    def _validar_salto(self, nodo, palabra):
        if not self.bucles:
            self.error(nodo, f"'{palabra}' solo puede usarse dentro de un bucle.")
        elif nodo.etiqueta is not None and nodo.etiqueta not in self.bucles:
            self.error(nodo, f"La etiqueta '{nodo.etiqueta}' no existe.")

    def visitar_Break(self, nodo):
        self._validar_salto(nodo, "break")

    def visitar_Continue(self, nodo):
        self._validar_salto(nodo, "continue")

    def visitar_Match(self, nodo):
        t = nodo.expresion.aceptar(self)
        tiene_comodin = False
        for caso in nodo.casos:
            if caso.patron is None:
                tiene_comodin = True
            else:
                tp = caso.patron.aceptar(self)
                if t is not None and tp is not None and tp != t:
                    self.error(caso.patron, f"El patrón es de tipo {tp}, pero se evalúa un valor de tipo {t}.")
            caso.bloque.aceptar(self)
        if not tiene_comodin:
            self.error(nodo, "El match debe incluir un caso comodín '_'.")

    #  Arreglos y slices 
    def visitar_Arreglo(self, nodo):
        tipos = [e.aceptar(self) for e in nodo.elementos]
        if not tipos:
            self.error(nodo, "No se puede inferir el tipo de un arreglo vacío.")
            return None
        if None in tipos:
            return None
        base = tipos[0]
        for t in tipos[1:]:
            if t != base:
                self.error(nodo, f"Todos los elementos del arreglo deben ser del mismo tipo: se esperaba {base} y se encontró {t}.")
                return None
        return f"[{base}; {len(tipos)}]"

    def visitar_AccesoIndice(self, nodo):
        t_arr = nodo.arreglo.aceptar(self)
        t_idx = nodo.indice.aceptar(self)
        if t_idx is not None and t_idx != 'i32':
            self.error(nodo, f"El índice debe ser de tipo i32, pero es {t_idx}.")
        if t_arr is None:
            return None
        info = info_arreglo(t_arr)
        if info is None:
            self.error(nodo, f"No es posible indexar un valor de tipo {t_arr}.")
            return None
        elemento, tam = info
        if tam is not None and isinstance(nodo.indice, Literal) and nodo.indice.tipo == 'i32':
            if nodo.indice.valor < 0 or nodo.indice.valor >= tam:
                self.error(nodo, "Índice fuera de los límites del arreglo.")
        return elemento

    def visitar_Slice(self, nodo):
        t_arr = nodo.arreglo.aceptar(self)
        for extremo in (nodo.inicio, nodo.fin):
            t = extremo.aceptar(self)
            if t is not None and t != 'i32':
                self.error(nodo, f"Los extremos del slice deben ser de tipo i32, pero se encontró {t}.")
        if t_arr is None:
            return None
        info = info_arreglo(t_arr)
        if info is None:
            self.error(nodo, f"No es posible crear un slice de un valor de tipo {t_arr}.")
            return None
        elemento, tam = info
        if tam is not None and isinstance(nodo.inicio, Literal) and isinstance(nodo.fin, Literal):
            if nodo.inicio.valor < 0 or nodo.fin.valor > tam or nodo.inicio.valor > nodo.fin.valor:
                self.error(nodo, "El rango del slice está fuera de los límites del arreglo.")
        return f"&[{elemento}]"

    #  Metodos 
    def visitar_LlamadaMetodo(self, nodo):
        t = nodo.objeto.aceptar(self)
        args = [a.aceptar(self) for a in nodo.argumentos]
        if t is None:
            return None
        m = nodo.nombre
        es_str = (t == 'String')
        info = info_arreglo(t)

        def aridad(n):
            if len(args) != n:
                self.error(nodo, f"El método '{m}' espera {n} argumentos, pero recibió {len(args)}.")
                return False
            return True

        if m == 'len' and (es_str or info):
            aridad(0)
            return 'i32'
        if m == 'contains' and (es_str or info):
            if aridad(1):
                esperado = 'String' if es_str else info[0]
                if args[0] is not None and args[0] != esperado:
                    self.error(nodo, f"contains espera un argumento de tipo {esperado}, pero recibió {args[0]}.")
            return 'bool'
        if es_str and m in ('to_uppercase', 'to_lowercase'):
            aridad(0)
            return 'String'
        if es_str and m == 'replace':
            if aridad(2) and any(a is not None and a != 'String' for a in args):
                self.error(nodo, "replace espera dos argumentos de tipo String.")
            return 'String'
        if es_str and m == 'split':
            if aridad(1) and args[0] not in (None, 'String'):
                self.error(nodo, "split espera un argumento de tipo String.")
            return '&[String]'
        if info and m == 'reverse':
            aridad(0)
            raiz = self._raiz(nodo.objeto)
            if isinstance(raiz, Identificador):
                s = self.tabla.buscar(raiz.nombre)
                if s is not None and not s.mutable:
                    self.error(nodo, f"No es posible modificar '{raiz.nombre}' porque fue declarada como inmutable.")
            return 'void'

        self.error(nodo, f"El tipo {t} no tiene un método '{m}'.")
        return None