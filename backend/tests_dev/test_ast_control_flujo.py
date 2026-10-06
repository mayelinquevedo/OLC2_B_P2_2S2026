from compiler.ast.nodos import (
    Literal, Identificador, OperacionBinaria, Bloque,
    If, While, Loop, Match, CasoMatch,
    Break, Continue, Return
)

condicion_if = OperacionBinaria(Identificador("x"), ">", Literal(0, "i32"))
nodo_if = If(
    condicion=condicion_if,
    bloque_entonces=Bloque([]),
    bloque_sino=Bloque([]),
    linea=1, columna=1
)
print("IF:", nodo_if)

nodo_while = While(
    condicion=OperacionBinaria(Identificador("x"), ">", Literal(0, "i32")),
    bloque=Bloque([]),
    linea=1, columna=1
)
print("WHILE:", nodo_while)


nodo_loop = Loop(
    bloque=Bloque([Break(etiqueta="outer")]),
    etiqueta="outer",
    linea=1, columna=1
)
print("LOOP:", nodo_loop)
print("  contenido:", nodo_loop.bloque.sentencias)

nodo_match = Match(
    expresion=Identificador("numero"),
    casos=[
        CasoMatch(patron=Literal(1, "i32"), bloque=Bloque([])),
        CasoMatch(patron=None, bloque=Bloque([])),
    ],
    linea=1, columna=1
)
print("MATCH:", nodo_match)
for caso in nodo_match.casos:
    print("  caso:", caso)

nodo_return = Return(
    valor=OperacionBinaria(Identificador("x"), "+", Literal(1, "i32"))
)
print("RETURN:", nodo_return)