fn fib(n: i32) -> i32 {
    if n < 2 { return n; }
    return fib(n - 1) + fib(n - 2);
}
fn fact(n: i32) -> i32 {
    if n <= 1 { return 1; }
    return n * fact(n - 1);
}
fn media(a: f64, b: f64) -> f64 { return (a + b) / 2.0; }
fn main() {
    println!("fib(15)={}", fib(15));
    println!("fact(10)={}", fact(10));
    println!("{}", media(3.0, 4.0));
    let arr = [5, 3, 8, 1, 9, 2];
    let mut i = 0;
    let mut max = arr[0];
    while i < arr.len() { if arr[i] > max { max = arr[i]; } i += 1; }
    println!("max={}", max);
}
