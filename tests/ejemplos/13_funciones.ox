fn saludar(nombre: String) {
    println!("Hola, {}", nombre);
}
fn sumar(a: i32, b: i32) -> i32 {
    return a + b;
}
fn unNumero() -> i32 {
    println!("Hola, evaluando");
    return 16;
}
fn main() {
    saludar(String::from("Ana"));
    let resultado = sumar(10, 5);
    println!("Resultado: {}", resultado);
    let numero: i32 = unNumero();
    println!("El numero es {}", numero);
}
