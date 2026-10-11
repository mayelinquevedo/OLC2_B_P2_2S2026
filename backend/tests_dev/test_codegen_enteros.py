from compiler.parser.parser import parser
from compiler.semantic.analizador import AnalizadorSemantico
from compiler.codegen.generador import GeneradorARM64
from compiler.errors import limpiar_errores, hay_errores, imprimir_reporte
from runtime.ejecutor import ejecutar

codigo = '''
fn main() {
    let a: i32 = 10;
    let mut b = 3;
    println!("a = {}, b = {}", a, b);
    b = b * a + 2;
    b += 5;
    println!("b = {}", b);
    println!("{}", -b);
    println!("division: {} resto: {}", a / 3, a % 3);
    let c = (a + b) * 2 - 1;
    println!("c = {}", c);
}
'''

esperado = "a = 10, b = 3\nb = 37\n-37\ndivision: 3 resto: 1\nc = 93\n"

limpiar_errores()
ast = parser.parse(codigo)
if ast is not None:
    AnalizadorSemantico().analizar(ast)

if ast is None or hay_errores():
    imprimir_reporte()
else:
    asm = GeneradorARM64().generar(ast)
    resultado = ejecutar(asm)
    if resultado["ok"]:
        print(resultado["salida"], end="")
        print("---")
        print("COINCIDE" if resultado["salida"] == esperado else "NO COINCIDE")
    else:
        print("Fallo en", resultado["fase"])
        print(resultado["error"])
