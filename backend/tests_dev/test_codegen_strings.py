from compiler.parser.parser import parser
from compiler.semantic.analizador import AnalizadorSemantico
from compiler.codegen.generador import GeneradorARM64
from compiler.errors import limpiar_errores, hay_errores, imprimir_reporte
from runtime.ejecutor import ejecutar

codigo = r'''
fn saludar(n: String) -> String {
    return "Hola, " + n;
}

fn dos_veces(s: String, k: i32) -> String {
    return s * k;
}

fn main() {
    let nombre = String::from("Ana");
    println!("Hola {}", nombre);
    println!("{}", "Hola " + nombre);
    println!("{}", 2 * "ab");
    println!("{}", "ab" * 3);
    println!("{} {}", "Hola Mundo desde Rust".len(), "ñ".len());
    println!("{} {}", "Hola Mundo".contains("Mundo"), "Hola".contains("xyz"));
    println!("{}", "Hola Mundo".replace("Mundo", "Rust"));
    println!("{} {}", "Hola Mundo".to_uppercase(), "HOLA MUNDO".to_lowercase());
    println!("{} {} {}", "a" == "a", "abc" < "abd", "b" > "abc");
    let mut s = String::from("ab");
    s += "cd";
    s *= 2;
    println!("{}", s);
    let vacio: String;
    let nuevo = String::new();
    println!("[{}][{}]", vacio, nuevo);
    println!("{}", saludar(String::from("Pablo")));
    println!("{}", dos_veces("xy", 3));
    let mut arr = [String::from("uno"), String::from("dos"), String::from("tres")];
    arr[1] += "!";
    println!("{} {} {}", arr[0], arr[1], arr[2]);
    println!(nombre);
    println!("Hola " + nombre);
    println!("Hola Mundo".len());
    println!(typeof(nombre));
    println!(typeof(1));
    let r = random(1, 10);
    println!("{}", r >= 1 && r <= 10);
}
'''

esperado = ("Hola Ana\nHola Ana\nabab\nababab\n21 2\ntrue false\nHola Rust\nHOLA MUNDO hola mundo\n"
            "true true true\nabcdabcd\n[][]\nHola, Pablo\nxyxyxy\nuno dos! tres\nAna\nHola Ana\n10\n"
            "String\ni32\ntrue\n")

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
