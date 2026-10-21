fn saludar(nombre: String) {
    println!("Hola " + nombre);
}
fn main() {
    let nombre = String::from("Ana");
    let edad = 20;
    println!(nombre);
    println!(edad);
    saludar(nombre);
}
