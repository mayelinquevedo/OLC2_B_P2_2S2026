fn saludar(valor: i32) -> bool {
    println!("Hola, evaluando");
    return valor > 0;
}
fn main() {
    let flag: bool = false;
    flag && saludar(10);
    let t: bool = true;
    t || saludar(5);
    let r = t && saludar(7);
    println!("{}", r);
    println!("{}", !r);
}
