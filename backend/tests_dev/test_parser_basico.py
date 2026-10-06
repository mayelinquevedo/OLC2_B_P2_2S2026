from compiler.parser.parser import parser
from compiler.errors import limpiar_errores, hay_errores, imprimir_reporte

codigo = '''
fn sumar(a: i32, b: i32) -> i32 {}

fn main() {}
'''

limpiar_errores()
resultado = parser.parse(codigo)

print("=== AST ===")
print(resultado)
for f in resultado.funciones:
    print(" ->", f)

print("\n=== ERRORES ===")
if hay_errores():
    imprimir_reporte()
else:
    print("Sin errores sintácticos.")