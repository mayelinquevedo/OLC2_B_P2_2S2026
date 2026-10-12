from compiler.parser.parser import parser
from compiler.semantic.analizador import AnalizadorSemantico
from compiler.codegen.generador import GeneradorARM64
from compiler.errors import limpiar_errores, hay_errores, imprimir_reporte
from runtime.ejecutor import ejecutar

valores100 = ", ".join(str(i) for i in range(100))
valores600 = ", ".join(str(i % 100) for i in range(600))

codigo = '''
fn main() {
    let numeros: [i32; 5] = [10, 20, 30, 40, 50];
    println!("{}", numeros[0]);
    println!("{}", numeros[4]);
    println!("len = {}", numeros.len());
    let mut suma = 0;
    let mut i = 0;
    while i < numeros.len() {
        suma += numeros[i];
        i += 1;
    }
    println!("suma = {}", suma);

    let mut m: [[i32; 3]; 2] = [[1, 2, 3], [4, 5, 6]];
    m[1][2] = 7;
    m[0][0] += 10;
    println!("{}", m[1][2]);
    println!("{}", m[0][0]);
    println!("{}", m[1][0]);
    println!("filas = {} cols = {}", m.len(), m[0].len());

    let cubo: [[[i32; 2]; 2]; 2] = [[[1, 2], [3, 4]], [[5, 6], [7, 8]]];
    println!("{}", cubo[1][0][1]);
    println!("{}", cubo[0][1][0]);
    println!("{}", cubo[1][1][1]);

    let mut r = [1, 2, 3, 4, 5];
    r.reverse();
    println!("{} {} {}", r[0], r[2], r[4]);

    let mut total = 0;
    let mut a = 0;
    while a < 2 {
        let mut b = 0;
        while b < 3 {
            total += m[a][b];
            b += 1;
        }
        a += 1;
    }
    println!("total = {}", total);

    let flags = [true, false, true];
    println!("{}", flags[1]);
    let z: [i32; 3];
    println!("{}", z[2]);

    let grande: [i32; 100] = [VALORES100];
    println!("{}", grande[99]);
    let enorme: [i32; 600] = [VALORES600];
    println!("{}", enorme[599]);
    let tras = 7;
    println!("{}", tras);
}
'''.replace("VALORES100", valores100).replace("VALORES600", valores600)

esperado = ("10\n50\nlen = 5\nsuma = 150\n7\n11\n4\nfilas = 2 cols = 3\n6\n3\n8\n5 3 1\n"
            "total = 32\nfalse\n0\n99\n99\n7\n")

limpiar_errores()
ast = parser.parse(codigo)
if ast is not None:
    AnalizadorSemantico().analizar(ast)

if ast is None or hay_errores():
    imprimir_reporte()
else:
    resultado = ejecutar(GeneradorARM64().generar(ast))
    if resultado["ok"]:
        print(resultado["salida"], end="")
        print("---")
        print("COINCIDE" if resultado["salida"] == esperado else "NO COINCIDE")
    else:
        print("Fallo en", resultado["fase"])
        print(resultado["error"])
