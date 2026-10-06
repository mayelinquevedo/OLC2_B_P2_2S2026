from compiler.parser.parser import parser
from compiler.errors import limpiar_errores, hay_errores, imprimir_reporte

codigo = '''
fn main() {
    let x: i32 = 10
    let y = 20;
    let z = 30;
}
'''

limpiar_errores()
resultado = parser.parse(codigo)

print("=== AST ===")
print(resultado)
if resultado:
    for f in resultado.funciones:
        print(" -", f)
        if f.cuerpo:
            for s in f.cuerpo.sentencias:
                print("    -", s)

print("\n=== ERRORES ===")
if hay_errores():
    imprimir_reporte()
else:
    print("Sin errores.")