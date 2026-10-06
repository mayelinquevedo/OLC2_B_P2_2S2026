from compiler.parser.parser import parser
from compiler.errors import limpiar_errores, hay_errores, imprimir_reporte

codigo = '''
fn main() {
    let x: i32 = 10;
    let mut y = 20;
    let z: f64;
    y = 30;
}
'''

limpiar_errores()
resultado = parser.parse(codigo)

print("=== AST ===")
funcion_main = resultado.funciones[0]
print(funcion_main)
for s in funcion_main.cuerpo.sentencias:
    print(" -", s)

print("\n=== ERRORES ===")
if hay_errores():
    imprimir_reporte()
else:
    print("Sin errores sintácticos.")