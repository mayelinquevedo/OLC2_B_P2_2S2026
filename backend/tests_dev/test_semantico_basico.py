from compiler.parser.parser import parser
from compiler.semantic.analizador import AnalizadorSemantico
from compiler.errors import limpiar_errores, hay_errores, imprimir_reporte

codigo = '''
fn sumar(a: i32, b: i32) -> i32 {
    return a + b;
}

fn main() {
    let a: i32 = 10;
    let b: f64 = 2.5;
    let nombre = String::from("Mayelin");

    let r1 = a + b;
    let r2 = a * 5;
    let r3 = a + nombre;

    let edad = 20;
    edad = 21;

    let mut c = 0;
    c += 1;

    let d: i32 = "veinte";
    println!("{}", total);
    saludar();
    sumar(10);
    println!("{}", r1);
}
'''

limpiar_errores()
ast = parser.parse(codigo)

if hay_errores():
    print("Errores de parseo:")
    imprimir_reporte()
else:
    analizador = AnalizadorSemantico()
    analizador.analizar(ast)

    print("=== ERRORES SEMANTICOS ===")
    if hay_errores():
        imprimir_reporte()
    else:
        print("Sin errores.")

    print("=== SIMBOLOS ===")
    for s in analizador.tabla.simbolos_para_reporte:
        print(" ", s)