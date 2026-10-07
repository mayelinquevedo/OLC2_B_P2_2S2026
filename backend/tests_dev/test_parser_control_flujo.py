from compiler.parser.parser import parser
from compiler.errors import limpiar_errores, hay_errores, imprimir_reporte

codigo = '''
fn main() {
    if x > 0 {
        let a = 1;
    } else {
        let b = 2;
    }

    while x > 0 {
        let c = 3;
    }

    loop {
        let d = 4;
    }

    'outer: loop {
        let e = 5;
    }

    match numero {
        1 => { let r = 1; },
        _ => { let r = 0; },
    }
}
'''

limpiar_errores()
resultado = parser.parse(codigo)

print("\n=== ERRORES ===")
if hay_errores():
    imprimir_reporte()
else:
    print("Sin errores.")

print("\n=== AST ===")
if resultado:
    for s in resultado.funciones[0].cuerpo.sentencias:
        print(" ->", s)
else:
    print("El parser devolvio None (fallo completo).")