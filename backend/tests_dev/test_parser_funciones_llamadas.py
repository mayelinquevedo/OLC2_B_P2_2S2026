from compiler.parser.parser import parser
from compiler.errors import limpiar_errores, hay_errores, imprimir_reporte

codigo = '''
fn sumar(a: i32, b: i32) -> i32 {
    return a + b;
}

fn main() {
    let r = sumar(10, 5);
    println!("{}", r);
    saludar(r);

    loop {
        break;
    }

    'outer: loop {
        continue 'outer;
    }
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
    for f in resultado.funciones:
        print("FUNCION:", f)
        for s in f.cuerpo.sentencias:
            print("  ->", s)