from compiler.parser.parser import parser
from compiler.semantic.analizador import AnalizadorSemantico
from compiler.errors import limpiar_errores, hay_errores, imprimir_reporte

codigo = '''
fn main() {
    let numeros: [i32; 5] = [10, 20, 30, 40, 50];
    let mut modificable = [1, 2, 3];
    let texto = String::from("Hola Mundo");

    let primero = numeros[0];
    let fuera = numeros[7];
    let parte = &numeros[1..4];
    let n = texto.len();
    let hay = texto.contains("Mundo");
    let mayus = texto.to_uppercase();
    modificable.reverse();
    numeros.reverse();

    let matrix: [[i32; 3]; 2] = [[1, 2, 3], [4, 5, 6]];
    let v = matrix[1][2];

    let x = 5;
    if x > 0 {
        let y = 1;
    } else {
        let z = 2;
    }
    if x {
        let w = 1;
    }

    let mut i = 0;
    while i < numeros.len() {
        i += 1;
    }

    'outer: loop {
        loop {
            break 'outer;
        }
        continue 'inexistente;
    }
    break;

    match x {
        1 => println!("uno"),
        "dos" => println!("dos"),
        _ => println!("otro"),
    }
    match x {
        1 => println!("uno"),
    }
    texto.volar();
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