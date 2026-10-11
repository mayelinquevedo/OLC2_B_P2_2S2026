from compiler.parser.parser import parser
from compiler.semantic.analizador import AnalizadorSemantico
from compiler.codegen.generador import GeneradorARM64
from compiler.errors import limpiar_errores, hay_errores, imprimir_reporte
from runtime.ejecutor import ejecutar

codigo = '''
fn sumar(a: i32, b: i32) -> i32 {
    return a + b;
}

fn fact(n: i32) -> i32 {
    if n <= 1 {
        return 1;
    }
    return n * fact(n - 1);
}

fn fib(n: i32) -> i32 {
    if n < 2 {
        return n;
    }
    return fib(n - 1) + fib(n - 2);
}

fn saludar(veces: i32) {
    let mut i = 0;
    while i < veces {
        println!("hola {}", i);
        i += 1;
    }
}

fn suma3(a: i32, b: i32, c: i32) -> i32 {
    return a + b + c;
}

fn main() {
    let r = sumar(10, 5);
    println!("sumar = {}", r);
    println!("fact(5) = {}", fact(5));
    println!("fib(10) = {}", fib(10));
    println!("{}", sumar(sumar(1, 2), sumar(3, 4)));
    println!("suma3 = {}", suma3(1, 20, 300));
    saludar(2);
    let x = 2;
    match x {
        1 => println!("uno"),
        2 => println!("dos"),
        _ => println!("otro"),
    }
    match x + 5 {
        1 => println!("uno"),
        _ => println!("comodin"),
    }
    let mut k = 0;
    loop {
        k += 1;
        match k {
            3 => { break; },
            _ => { },
        }
    }
    println!("k = {}", k);
}
'''

esperado = ("sumar = 15\nfact(5) = 120\nfib(10) = 55\n10\nsuma3 = 321\nhola 0\nhola 1\n"
            "dos\ncomodin\nk = 3\n")

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
