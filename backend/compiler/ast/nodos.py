

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