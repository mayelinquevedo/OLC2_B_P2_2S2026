from compiler.ast.nodos import Literal, Identificador, OperacionBinaria, OperacionUnaria

# Simulamos el AST de: x + 5 * -2
nodo = OperacionBinaria(
    izquierda=Identificador("x", linea=1, columna=1),
    operador="+",
    derecha=OperacionBinaria(
        izquierda=Literal(5, "i32", linea=1, columna=5),
        operador="*",
        derecha=OperacionUnaria("-", Literal(2, "i32", linea=1, columna=9), linea=1, columna=8)
    ),
    linea=1, columna=1
)

print(nodo)