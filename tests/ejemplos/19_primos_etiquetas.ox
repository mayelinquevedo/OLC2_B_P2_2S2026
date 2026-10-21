fn es_primo(n: i32) -> bool {
    if n < 2 { return false; }
    let mut i = 2;
    while i * i <= n {
        if n % i == 0 { return false; }
        i += 1;
    }
    return true;
}
fn main() {
    let mut i = 1;
    while i <= 30 {
        if es_primo(i) { println!("{}", i); }
        i += 1;
    }
    let mut suma = 0;
    'a: loop {
        let mut j = 0;
        loop {
            j += 1;
            if j > 3 { continue 'a; }
            suma += j;
            if suma > 20 { break 'a; }
        }
    }
    println!("suma={}", suma);
}
