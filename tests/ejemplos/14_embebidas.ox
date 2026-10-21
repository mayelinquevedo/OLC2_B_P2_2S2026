fn main() {
    let texto = String::from("Hola Mundo");
    let mut numeros = [10, 20, 30];
    println!("Hola Mundo");
    println!(texto);
    println!("Texto: {}", texto);
    println!("Longitud: {}", texto.len());
    println!(typeof(texto));
    println!(texto.len());
    println!(texto.contains("Mundo"));
    println!(texto.replace("Mundo", "Rust"));
    println!(texto.to_uppercase());
    println!(texto.to_lowercase());
    println!(texto.split(" "));
    numeros.reverse();
    println!(numeros);
}
