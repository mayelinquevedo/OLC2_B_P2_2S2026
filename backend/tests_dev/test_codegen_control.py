from compiler.parser.parser import parser
from compiler.semantic.analizador import AnalizadorSemantico
from compiler.codegen.generador import GeneradorARM64
from compiler.errors import limpiar_errores, hay_errores, imprimir_reporte
from runtime.ejecutor import ejecutar

codigo = '''
fn main() {
    let mut i = 0;
    let mut suma = 0;
    while i < 10 {
        i += 1;
        if i % 2 == 0 {
            continue;
        }
        if i > 7 {
            break;
        }
        suma += i;
    }
    println!("suma = {}", suma);

    let a = 5;
    let b = 10;
    let flag = a < b && b != 0;
    println!("{}", flag);
    println!("{}", !flag || a == 5);

    let mut n = 0;
    'externo: loop {
        loop {
            n += 1;
            if n == 3 {
                break 'externo;
            }
        }
    }
    println!("n = {}", n);

    if a > b {
        println!("a mayor");
    } else if a == b {
        println!("iguales");
    } else {
        println!("b mayor");
    }
}
'''

esperado = "suma = 16\ntrue\ntrue\nn = 3\nb mayor\n"

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
