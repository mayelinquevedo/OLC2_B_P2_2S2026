from compiler.parser.parser import parser
from compiler.errors import limpiar_errores, hay_errores, imprimir_reporte

codigo = '''
fn main() {
    let a = 2 + 3 * 4;
    let b = (2 + 3) * 4;
    let c = -5 + 2;
    let d = x > 0 && y < 10;
    let e = !flag || otro;
}
'''

limpiar_errores()
resultado = parser.parse(codigo)

print("=== AST ===")
for s in resultado.funciones[0].cuerpo.sentencias:
    print(" ->", s)

print("\n=== ERRORES ===")
if hay_errores():
    imprimir_reporte()
else:
    print("Sin errores.")