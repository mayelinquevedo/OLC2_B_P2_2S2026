from compiler.parser.parser import parser
from compiler.semantic.analizador import AnalizadorSemantico
from compiler.codegen.generador import GeneradorARM64
from compiler.errors import limpiar_errores, hay_errores, imprimir_reporte
from runtime.ejecutor import ejecutar


def correr(nombre, codigo, salida_esperada, codigo_esperado):
    limpiar_errores()
    ast = parser.parse(codigo)
    if ast is not None:
        AnalizadorSemantico().analizar(ast)
    if ast is None or hay_errores():
        print(f"[{nombre}] errores de compilacion:")
        imprimir_reporte()
        return
    r = ejecutar(GeneradorARM64().generar(ast))
    if not r["ok"]:
        print(f"[{nombre}] fallo en {r['fase']}: {r['error']}")
        return
    bien = r["salida"] == salida_esperada and r["codigo"] == codigo_esperado
    print(f"[{nombre}] {'COINCIDE' if bien else 'NO COINCIDE'} (codigo {r['codigo']}) {r['salida']!r}")


correr("indice fuera de rango", '''
fn main() {
    let a = [1, 2, 3];
    let mut i = 5;
    println!("antes");
    println!("{}", a[i]);
    println!("despues");
}
''', "antes\nError de ejecución: índice fuera de los límites del arreglo\n", 1)

correr("indice negativo", '''
fn main() {
    let a = [1, 2, 3];
    let mut i = 0;
    i -= 1;
    println!("{}", a[i]);
}
''', "Error de ejecución: índice fuera de los límites del arreglo\n", 1)

correr("division entre cero", '''
fn main() {
    let mut d = 0;
    println!("antes");
    println!("{}", 10 / d);
}
''', "antes\nError de ejecución: división entre cero\n", 1)

correr("division valida", '''
fn main() {
    let d = 3;
    println!("{} {}", 10 / d, 10 % d);
}
''', "3 1\n", 0)

correr("division f64 entre cero", '''
fn main() {
    let z: f64;
    println!("antes");
    println!("{}", 1.0 / z);
}
''', "antes\nError de ejecución: división entre cero\n", 1)
