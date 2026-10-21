fn main() {
    let mensaje = String::from("Hola\nRust");
    let comillas = String::from("Él dijo: \"Hola\"");
    let ruta = String::from("C:\\Users\\Diego");
    println!("{}", mensaje);
    println!("{}", comillas);
    println!("{}", ruta);
    let ruta_raw = String::from(r"C:\Users\Diego");
    let texto = String::from(r#"Él dijo: "Hola Rust""#);
    println!("{}", ruta_raw);
    println!("{}", texto);
}
