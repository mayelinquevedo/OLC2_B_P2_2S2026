fn main() {
    let s = String::from("b");
    match s.len() {
        0 => println!("cero"),
        1 => { println!("uno"); println!("otra linea"); },
        _ => println!("muchos"),
    }
    let c = 'x';
    match c { 'x' => println!("equis"), _ => println!("otro") }
    let b = true;
    match b { true => println!("T"), false => println!("F"), _ => println!("?") }
}
