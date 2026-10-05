from compiler.ast.nodos import (
    Literal, Identificador, OperacionBinaria,
    DeclaracionVariable, Asignacion, Bloque, LlamadaPrintln
)

decl = DeclaracionVariable(
    nombre="x", tipo="i32", mutable=True,
    valor_inicial=Literal(10, "i32"),
    linea=1, columna=1
)

asign = Asignacion(
    nombre="x", operador="=",
    valor=OperacionBinaria(Identificador("x"), "+", Literal(1, "i32")),
    linea=2, columna=1
)

impresion = LlamadaPrintln(
    formato="{}", argumentos=[Identificador("x")],
    linea=3, columna=1
)

programa = Bloque([decl, asign, impresion], linea=1, columna=1)

print(programa)
for s in programa.sentencias:
    print(" ->", s)