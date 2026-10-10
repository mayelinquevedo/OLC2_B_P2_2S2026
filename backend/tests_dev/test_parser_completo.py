from compiler.parser.parser import parser
from compiler.errors import limpiar_errores, hay_errores, imprimir_reporte

codigo = '''
fn main() {
    let numeros: [i32; 5] = [10, 20, 30, 40, 50];
    let matrix: [[i32; 3]; 2] = [[1, 2, 3], [4, 5, 6]];
    matrix[1][2] = 7;
    let n = numeros.len();
    let total = 1 + numeros[0] * 2;
    let texto = String::from("Hola");
    let vacio = String::new();
    println!(texto);
    println!("{}", texto.len());
    println!("Hola " + texto);
    numeros.reverse();
    match n {
        1 => println!("uno"),
        _ => println!("otro"),
    }
    while i < numeros.len() {
        i += 1;
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
    for s in resultado.funciones[0].cuerpo.sentencias:
        print(" ->", s)