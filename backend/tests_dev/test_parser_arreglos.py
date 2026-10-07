from compiler.parser.parser import parser
from compiler.errors import limpiar_errores, hay_errores, imprimir_reporte

codigo = '''
fn main() {
    let numeros = [10, 20, 30, 40, 50];
    let primero = numeros[0];
    let parte = &numeros[1..4];

    let matrix = [[1, 2, 3], [4, 5, 6]];
    let valor = matrix[1][2];

    let nombre = String::from("Ana");

    let mut contador = 0;
    contador += 1;
    contador -= 1;
    contador *= 2;
}
'''

limpiar_errores()
resultado = parser.parse(codigo)

print("=== ERRORES ===")
if hay_errores():
    imprimir_reporte()
else:
    print("Sin errores.")

print("\n=== AST ===")
if resultado:
    for s in resultado.funciones[0].cuerpo.sentencias:
        print(" ->", s)