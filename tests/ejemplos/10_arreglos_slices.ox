fn main() {
    let numeros: [i32; 5] = [10, 20, 30, 40, 50];
    let edades = [18, 20, 22];
    println!("Primer elemento: {}", numeros[0]);
    println!("Tercer elemento: {}", numeros[2]);
    println!("Longitud de numeros: {}", numeros.len());
    println!("Longitud de edades: {}", edades.len());
    println!("\nElementos de numeros:");
    let mut i = 0;
    while i < numeros.len() {
        println!("{}", numeros[i]);
        i = i + 1;
    }
    let parte = &numeros[1..4];
    println!("\nSlice: {:?}", parte);
    println!("Primera edad: {}", edades[0]);
}
