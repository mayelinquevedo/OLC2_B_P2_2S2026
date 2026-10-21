fn main() {
    let mut i = 0;
    loop {
        i = i + 1;
        if i == 2 { continue; }
        if i > 4 { break; }
        println!("i={}", i);
    }
    'outer: loop {
        let mut j = 0;
        'inner: loop {
            j += 1;
            if j == 3 { break 'outer; }
            println!("j={}", j);
        }
    }
    let mut n = 3;
    while n > 0 { println!("n={}", n); n -= 1; }
}
