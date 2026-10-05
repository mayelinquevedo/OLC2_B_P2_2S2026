

class Nodo:
    def __init__(self, linea=0, columna=0):
        self.linea = linea
        self.columna = columna

    def aceptar(self, visitor):
        nombre_metodo = f"visitar_{type(self).__name__}"
        metodo = getattr(visitor, nombre_metodo)
        return metodo(self)



# EXPRESIONES 
class Literal(Nodo):
    """Un valor literal: entero, flotante, string, char, bool."""
    def __init__(self, valor, tipo, linea=0, columna=0):
        super().__init__(linea, columna)
        self.valor = valor
        self.tipo = tipo  # 'i32', 'f64', 'String', 'char', 'bool'

    def __repr__(self):
        return f"Literal({self.valor}: {self.tipo})"

class Identificador(Nodo): 
    """Referencia a una variable por su nombre."""
    def __init__(self, nombre, linea=0, columna=0):
        super().__init__(linea, columna)
        self.nombre = nombre

    def __repr__(self):
        return f"Identificador({self.nombre})"


class OperacionBinaria(Nodo): 
    def __init__(self, izquierda, operador, derecha, linea=0, columna=0):
        super().__init__(linea, columna)
        self.izquierda = izquierda
        self.operador = operador  # '+', '-', '==', '&&', etc.
        self.derecha = derecha

    def __repr__(self):
        return f"({self.izquierda} {self.operador} {self.derecha})"


class OperacionUnaria(Nodo):
    def __init__(self, operador, operando, linea=0, columna=0):
        super().__init__(linea, columna)
        self.operador = operador
        self.operando = operando

    def __repr__(self):
        return f"({self.operador}{self.operando})"

       
# DECLARACIONES Y SENTENCIAS
class DeclaracionVariable(Nodo):
    def __init__(self, nombre, tipo, mutable, valor_inicial, linea=0, columna=0):
        super().__init__(linea, columna)
        self.nombre = nombre
        self.tipo = tipo
        self.mutable = mutable
        self.valor_inicial = valor_inicial

    def __repr__(self):
        mut = "mut " if self.mutable else ""
        return f"let {mut}{self.nombre}: {self.tipo} = {self.valor_inicial}"


class Asignacion(Nodo):
    def __init__(self, nombre, operador, valor, linea=0, columna=0):
        super().__init__(linea, columna)
        self.nombre = nombre
        self.operador = operador
        self.valor = valor

    def __repr__(self):
        return f"{self.nombre} {self.operador} {self.valor}"


class Bloque(Nodo):
    """Secuencia de sentencias entre llaves { }"""
    def __init__(self, sentencias, linea=0, columna=0):
        super().__init__(linea, columna)
        self.sentencias = sentencias

    def __repr__(self):
        return f"Bloque({len(self.sentencias)} sentencias)"


class LlamadaPrintln(Nodo):
    def __init__(self, formato, argumentos, linea=0, columna=0):
        super().__init__(linea, columna)
        self.formato = formato
        self.argumentos = argumentos

    def __repr__(self):
        return f'println!("{self.formato}", {self.argumentos})'