

class Nodo:
    def __init__(self, linea=0, columna=0):
        self.linea = linea
        self.columna = columna

    def aceptar(self, visitor):
        nombre_metodo = f"visitar_{type(self).__name__}"
        metodo = getattr(visitor, nombre_metodo)
        resultado = metodo(self)
        if getattr(visitor, "anota_tipos", False):
            self.tipo_resultado = resultado
        return resultado



# EXPRESIONES 
class Literal(Nodo):
    """Un valor literal: entero, flotante, string, char, bool."""
    def __init__(self, valor, tipo, linea=0, columna=0):
        super().__init__(linea, columna)
        self.valor = valor
        self.tipo = tipo  # 'i32', 'f64', 'String', 'char', 'bool'

    def __repr__(self):
        return f"Literal({self.valor}: {self.tipo})"

class ErrorExpr(Nodo):
    """Valor invalido: reemplaza a una expresion que tuvo un error semantico.
    Al ejecutar vale 0 y al imprimirse muestra 'None' (recuperacion ante errores)."""
    def __init__(self, linea=0, columna=0):
        super().__init__(linea, columna)
        self.tipo_resultado = 'None'

    def __repr__(self):
        return "ErrorExpr()"


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
    def __init__(self, destino, operador, valor, linea=0, columna=0):
        super().__init__(linea, columna)
        self.destino = destino      
        self.operador = operador
        self.valor = valor

    def __repr__(self):
        return f"{self.destino} {self.operador} {self.valor}"


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


# CONTROL DE FLUJO

class If(Nodo):
    def __init__(self, condicion, bloque_entonces, bloque_sino=None, linea=0, columna=0):
        super().__init__(linea, columna)
        self.condicion = condicion
        self.bloque_entonces = bloque_entonces
        self.bloque_sino = bloque_sino  

    def __repr__(self):
        return f"if {self.condicion} {{...}} else {{...}}"


class While(Nodo):
    def __init__(self, condicion, bloque, linea=0, columna=0):
        super().__init__(linea, columna)
        self.condicion = condicion
        self.bloque = bloque

    def __repr__(self):
        return f"while {self.condicion} {{...}}"


class Loop(Nodo):
    def __init__(self, bloque, etiqueta=None, linea=0, columna=0):
        super().__init__(linea, columna)
        self.bloque = bloque
        self.etiqueta = etiqueta  # None o string, ej: "outer"

    def __repr__(self):
        et = f"'{self.etiqueta}: " if self.etiqueta else ""
        return f"{et}loop {{...}}"


class CasoMatch(Nodo):
    def __init__(self, patron, bloque, linea=0, columna=0):
        super().__init__(linea, columna)
        self.patron = patron  # una expresión, o None para el comodín '_'
        self.bloque = bloque

    def __repr__(self):
        p = self.patron if self.patron is not None else "_"
        return f"{p} => {{...}}"


class Match(Nodo):
    def __init__(self, expresion, casos, linea=0, columna=0):
        super().__init__(linea, columna)
        self.expresion = expresion
        self.casos = casos  # lista de CasoMatch

    def __repr__(self):
        return f"match {self.expresion} {{ {len(self.casos)} casos }}"



# SENTENCIAS DE TRANSFERENCIA 
class Break(Nodo):
    """break;  /  break 'etiqueta;"""
    def __init__(self, etiqueta=None, linea=0, columna=0):
        super().__init__(linea, columna)
        self.etiqueta = etiqueta

    def __repr__(self):
        return f"break '{self.etiqueta}" if self.etiqueta else "break"


class Continue(Nodo):
    """continue;  /  continue 'etiqueta;"""
    def __init__(self, etiqueta=None, linea=0, columna=0):
        super().__init__(linea, columna)
        self.etiqueta = etiqueta

    def __repr__(self):
        return f"continue '{self.etiqueta}" if self.etiqueta else "continue"


class Return(Nodo):
    """return;  /  return expr;"""
    def __init__(self, valor=None, linea=0, columna=0):
        super().__init__(linea, columna)
        self.valor = valor  

    def __repr__(self):
        return f"return {self.valor}" if self.valor is not None else "return"


# FUNCIONES 
class Parametro(Nodo):
    """Un parámetro de función: nombre : tipo"""
    def __init__(self, nombre, tipo, linea=0, columna=0):
        super().__init__(linea, columna)
        self.nombre = nombre
        self.tipo = tipo

    def __repr__(self):
        return f"{self.nombre}: {self.tipo}"


class Function(Nodo):
    def __init__(self, nombre, parametros, tipo_retorno, cuerpo, linea=0, columna=0):
        super().__init__(linea, columna)
        self.nombre = nombre
        self.parametros = parametros        # lista de Parametro
        self.tipo_retorno = tipo_retorno    # puede ser None (sin retorno)
        self.cuerpo = cuerpo                # Bloque

    def __repr__(self):
        params = ", ".join(str(p) for p in self.parametros)
        ret = f" -> {self.tipo_retorno}" if self.tipo_retorno else ""
        return f"fn {self.nombre}({params}){ret} {{...}}"


class LlamadaFuncion(Nodo):
    """nombre(argumentos)"""
    def __init__(self, nombre, argumentos, linea=0, columna=0):
        super().__init__(linea, columna)
        self.nombre = nombre
        self.argumentos = argumentos  # lista de expresiones

    def __repr__(self):
        args = ", ".join(str(a) for a in self.argumentos)
        return f"{self.nombre}({args})"



# ARREGLOS Y SLICES 

class Arreglo(Nodo):
    """Literal de arreglo: [1, 2, 3]"""
    def __init__(self, elementos, linea=0, columna=0):
        super().__init__(linea, columna)
        self.elementos = elementos  # lista de expresiones

    def __repr__(self):
        return f"[{', '.join(str(e) for e in self.elementos)}]"


class AccesoIndice(Nodo):
    def __init__(self, arreglo, indice, linea=0, columna=0):
        super().__init__(linea, columna)
        self.arreglo = arreglo  # expresión (puede ser otro AccesoIndice, para multidim)
        self.indice = indice    # expresión

    def __repr__(self):
        return f"{self.arreglo}[{self.indice}]"


class Slice(Nodo):
    def __init__(self, arreglo, inicio, fin, linea=0, columna=0):
        super().__init__(linea, columna)
        self.arreglo = arreglo
        self.inicio = inicio
        self.fin = fin

    def __repr__(self):
        return f"&{self.arreglo}[{self.inicio}..{self.fin}]"


class LlamadaMetodo(Nodo):
    """objeto.metodo(argumentos)  Ej: texto.len(), numeros.reverse()"""
    def __init__(self, objeto, nombre, argumentos, linea=0, columna=0):
        super().__init__(linea, columna)
        self.objeto = objeto
        self.nombre = nombre
        self.argumentos = argumentos

    def __repr__(self):
        args = ", ".join(str(a) for a in self.argumentos)
        return f"{self.objeto}.{self.nombre}({args})"


# NODO RAÍZ
class Programa(Nodo):
    """Nodo raíz del AST: lista de funciones declaradas (incluye main)."""
    def __init__(self, funciones, linea=0, columna=0):
        super().__init__(linea, columna)
        self.funciones = funciones  # lista de Function

    def __repr__(self):
        return f"Programa({len(self.funciones)} funciones)"