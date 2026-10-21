fn main() {
    let texto = String::from("Hola Mundo desde Rust");
    let partes = texto.split(" ");
    println!("{}", partes.len());
    println!("{}", partes[2]);
    println!("{:?}", partes);
    let palabras: Vec<&str> = texto.split_whitespace().collect();
    let mut i = 0;
    while i < palabras.len() { println!("{}", palabras[i]); i = i + 1; }
    let csv = String::from("a,,b,");
    println!("{:?}", csv.split(","));
    println!("{:?}", csv.split("xyz"));
    println!("{:?}", String::from("  a   b  ").split_whitespace().collect());
    println!("{}", partes.contains(String::from("Rust")));
    let t = String::from("uno--dos--tres");
    println!("{:?}", t.split("--"));
}
