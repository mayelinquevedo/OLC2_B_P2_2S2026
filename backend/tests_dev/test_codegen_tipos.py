from compiler.parser.parser import parser
from compiler.semantic.analizador import AnalizadorSemantico
from compiler.codegen.generador import GeneradorARM64
from compiler.errors import limpiar_errores, hay_errores, imprimir_reporte
from runtime.ejecutor import ejecutar

codigo = r'''
fn media(a: f64, b: f64) -> f64 {
    return (a + b) / 2.0;
}

fn mezcla(n: i32, x: f64, m: i32, y: f64) -> f64 {
    return n * x + m + y;
}

fn cuadrado(x: f64) -> f64 {
    return x * x;
}

fn siguiente(c: char) -> char {
    return c;
}

fn main() {
    let pi: f64 = 3.14;
    println!("{}", pi);
    let a = 10;
    let b = 2.5;
    println!("{}", a + b);
    println!("{}", 10.0 / 4.0);
    println!("{}", 10 / 4.0);
    println!("{}", 7.5 % 2.0);
    println!("{}", -7.5 % 2.0);
    println!("{}", -7.25);
    println!("{}", 2.0 * 3.0);
    println!("{} {} {}", 1.5 < 2, 3 == 3.0, 2.5 >= 2.6);
    let mut x = 1.5;
    x *= 2;
    x += 0.25;
    println!("{}", x);
    let sin_valor: f64;
    println!("{}", sin_valor);
    println!("{}", media(3.0, 4.0));
    println!("{}", mezcla(2, 1.5, 10, 0.5));
    println!("{}", cuadrado(cuadrado(1.5)));
    let mut v = [1.5, 2.5, 3.5];
    v[1] = 9.75;
    v[2] += 1;
    println!("{} {} {}", v[0], v[1], v[2]);
    let mut i = 0;
    let mut suma = 0.0;
    while i < 3 {
        suma += v[i];
        i += 1;
    }
    println!("suma = {}", suma);
    println!("{}", 'a');
    println!("{}", 'ñ');
    println!("{}", '€');
    println!("{}", '');
    println!("[{}]", '\n');
    println!("{} {} {}", 'a' == 97, 'a' < 'b', 98 > 'a');
    match 'b' {
        'a' => println!("es a"),
        'b' => println!("es b"),
        _ => println!("otro"),
    }
    println!("{}", siguiente('z'));
    let letras = ['h', 'o', 'l', 'a'];
    println!("{}{}{}{}", letras[0], letras[1], letras[2], letras[3]);
}
'''

esperado = ("3.14\n12.5\n2.5\n2.5\n1.5\n-1.5\n-7.25\n6.0\ntrue true false\n3.25\n0.0\n3.5\n13.5\n5.0625\n"
            "1.5 9.75 4.5\nsuma = 15.75\na\nñ\n€\n\n[\n]\ntrue true true\nes b\nz\nhola\n")

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
