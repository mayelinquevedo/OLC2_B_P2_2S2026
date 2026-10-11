from compiler.parser.parser import parser
from compiler.semantic.analizador import AnalizadorSemantico
from compiler.codegen.generador import GeneradorARM64
from compiler.errors import limpiar_errores, hay_errores, imprimir_reporte
from runtime.ejecutor import ejecutar

codigo = '''
fn main() {
    println!("Hola Mundo");
    println!("Segunda línea con tilde");
}
'''

limpiar_errores()
ast = parser.parse(codigo)
if ast is not None:
    AnalizadorSemantico().analizar(ast)

if ast is None or hay_errores():
    imprimir_reporte()
else:
    asm = GeneradorARM64().generar(ast)
    print("=== ARM64 GENERADO ===")
    print(asm)
    resultado = ejecutar(asm)
    print("=== RESULTADO ===")
    if resultado["ok"]:
        print(resultado["salida"], end="")
        print(f"(codigo de salida {resultado['codigo']}, {resultado['tiempo']:.4f}s)")
    else:
        print("Fallo en", resultado["fase"])
        print(resultado["error"])
