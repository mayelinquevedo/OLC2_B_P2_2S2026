"""Recuperacion ante errores: deja el AST en un estado seguro para generar codigo.

El enunciado pide que el compilador reporte los errores pero siga con el resto del programa
(salvo que el error impida continuar de forma segura). Despues del analisis semantico, este modulo
recorre el AST y, segun lo que marco el analizador (atributo `con_error` y `tipo_resultado is None`):

  * una EXPRESION con error pasa a ser un `ErrorExpr` (vale 0 y se imprime como `None`);
    un error dentro de una expresion contamina a las expresiones que la contienen;
  * una SENTENCIA inválida se omite (asignacion invalida, break fuera de un ciclo, return invalido, ...);
  * `let x: T = <invalido>;` conserva la variable con el valor por defecto de T;
  * `let x = <invalido>;` (sin tipo) se omite y sus usos pasan a ser `None`;
  * una condicion invalida (`if`/`while`) cuenta como falsa.
"""
from compiler.ast.nodos import (
    Nodo, Programa, Function, Bloque, DeclaracionVariable, Asignacion, LlamadaPrintln, If, While, Loop,
    Match, CasoMatch, Break, Continue, Return, Literal, Identificador, OperacionBinaria, OperacionUnaria,
    Arreglo, AccesoIndice, Slice, LlamadaFuncion, LlamadaMetodo, ErrorExpr)

EXPRESIONES = (Literal, Identificador, OperacionBinaria, OperacionUnaria, Arreglo, AccesoIndice,
               Slice, LlamadaFuncion, LlamadaMetodo)


def es_critico(programa):
    """Errores que impiden continuar de forma segura: no hay una unica funcion main."""
    return programa is None or getattr(programa, "con_error", False)


def _defectuoso(nodo):
    return getattr(nodo, "con_error", False) or getattr(nodo, "tipo_resultado", "?") is None


def _expr(e):
    """Devuelve la expresion saneada (o un ErrorExpr)."""
    if isinstance(e, ErrorExpr) or not isinstance(e, EXPRESIONES):
        return e
    if _defectuoso(e):
        return ErrorExpr(e.linea, e.columna)
    for nombre, valor in list(vars(e).items()):
        if isinstance(valor, Nodo):
            nuevo = _expr(valor)
            setattr(e, nombre, nuevo)
            if isinstance(nuevo, ErrorExpr):
                return ErrorExpr(e.linea, e.columna)
        elif isinstance(valor, list) and valor and all(isinstance(x, Nodo) for x in valor):
            nuevos = [_expr(x) for x in valor]
            setattr(e, nombre, nuevos)
            if any(isinstance(x, ErrorExpr) for x in nuevos):
                return ErrorExpr(e.linea, e.columna)
    return e


def _bloque(b):
    if b is None:
        return None
    b.sentencias = [n for n in (_sentencia(s) for s in b.sentencias) if n is not None]
    return b


def _sentencia(s):
    """Devuelve la sentencia saneada, o None si debe omitirse."""
    if isinstance(s, (EXPRESIONES, ErrorExpr)):
        return _expr(s)
    if isinstance(s, (Break, Continue)):
        return None if getattr(s, "con_error", False) else s
    if isinstance(s, Return):
        if getattr(s, "con_error", False):
            return None
        if s.valor is not None:
            s.valor = _expr(s.valor)
            if isinstance(s.valor, ErrorExpr):
                return None
        return s
    if isinstance(s, Asignacion):
        s.destino, s.valor = _expr(s.destino), _expr(s.valor)
        if getattr(s, "con_error", False) or isinstance(s.destino, ErrorExpr) or isinstance(s.valor, ErrorExpr):
            return None
        return s
    if isinstance(s, DeclaracionVariable):
        if s.valor_inicial is not None:
            s.valor_inicial = _expr(s.valor_inicial)
            if isinstance(s.valor_inicial, ErrorExpr):
                if s.tipo is None:
                    return None                  # let x = <invalido>;  -> sus usos seran 'None'
                s.valor_inicial = None           # let x: T = <invalido>;  -> valor por defecto de T
        elif s.tipo is None:
            return None                          # let x;  (sin tipo ni valor)
        return s
    if isinstance(s, LlamadaPrintln):
        if getattr(s, "con_error", False):
            return None
        s.argumentos = [_expr(a) for a in s.argumentos]
        return s
    if isinstance(s, If):
        s.condicion = _expr(s.condicion)
        s.bloque_entonces = _bloque(s.bloque_entonces)
        if s.bloque_sino is not None:
            s.bloque_sino = _bloque(s.bloque_sino) if isinstance(s.bloque_sino, Bloque) else _sentencia(s.bloque_sino)
        return s
    if isinstance(s, While):
        s.condicion = _expr(s.condicion)
        s.bloque = _bloque(s.bloque)
        return s
    if isinstance(s, Loop):
        s.bloque = _bloque(s.bloque)
        return s
    if isinstance(s, Bloque):
        return _bloque(s)
    if isinstance(s, Match):
        s.expresion = _expr(s.expresion)
        if isinstance(s.expresion, ErrorExpr):
            return None
        casos = []
        for c in s.casos:
            if c.patron is not None:
                c.patron = _expr(c.patron)
                if isinstance(c.patron, ErrorExpr):
                    continue
            c.bloque = _bloque(c.bloque)
            casos.append(c)
        s.casos = casos
        return s
    return s


def recuperar(programa):
    """Sanea el AST (ya analizado) en el mismo lugar y lo devuelve."""
    programa.funciones = [f for f in programa.funciones if not getattr(f, "con_error", False)]
    for f in programa.funciones:
        f.cuerpo = _bloque(f.cuerpo)
    return programa
