from compiler.ast.nodos import (
    Literal, Identificador, OperacionBinaria, Bloque,
    Parametro, Function, LlamadaFuncion,
    Arreglo, AccesoIndice, Slice, Programa,
    DeclaracionVariable, LlamadaPrintln, Return
)

funcion_sumar = Function(
    nombre="sumar",
    parametros=[Parametro("a", "i32"), Parametro("b", "i32")],
    tipo_retorno="i32",
    cuerpo=Bloque([
        Return(OperacionBinaria(Identificador("a"), "+", Identificador("b")))
    ]),
    linea=1, columna=1
)
print("FUNCION:", funcion_sumar)

funcion_main = Function(
    nombre="main",
    parametros=[],
    tipo_retorno=None,
    cuerpo=Bloque([
        DeclaracionVariable("r", None, False, LlamadaFuncion("sumar", [Literal(10, "i32"), Literal(5, "i32")])),
        LlamadaPrintln("{}", [Identificador("r")])
    ]),
    linea=5, columna=1
)
print("MAIN:", funcion_main)

acceso_2d = AccesoIndice(AccesoIndice(Identificador("matrix"), Literal(1, "i32")), Literal(2, "i32"))
print("ACCESO 2D:", acceso_2d)

slice_nodo = Slice(Identificador("numeros"), Literal(1, "i32"), Literal(4, "i32"))
print("SLICE:", slice_nodo)

programa = Programa([funcion_sumar, funcion_main])
print("PROGRAMA:", programa)
for f in programa.funciones:
    print("  ->", f)