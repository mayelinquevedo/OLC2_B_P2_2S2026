fn duplicar(a: [i32; 3]) -> [i32; 3] {
    let mut r = [0, 0, 0];
    let mut i = 0;
    while i < 3 { r[i] = a[i] * 2; i += 1; }
    return r;
}
fn temprano(a: [i32; 3], corto: bool) -> [i32; 3] {
    if corto { return a; }
    return duplicar(a);
}
fn fabrica(n: i32) -> [i32; 2] {
    return [n, n + 1];
}
fn suma(a: [i32; 3]) -> i32 { return a[0] + a[1] + a[2]; }
fn transpuesta(m: [[i32; 3]; 2]) -> [[i32; 2]; 3] {
    let mut t: [[i32; 2]; 3] = [[0, 0], [0, 0], [0, 0]];
    let mut i = 0;
    while i < 2 { let mut j = 0; while j < 3 { t[j][i] = m[i][j]; j += 1; } i += 1; }
    return t;
}
fn main() {
    let a = [1, 2, 3];
    println!("{:?}", duplicar(a));
    println!("{}", suma(duplicar(a)));
    println!("{:?}", temprano(a, true));
    println!("{:?}", temprano(a, false));
    println!("{:?}", duplicar(duplicar(a)));
    println!("{:?} {:?}", fabrica(10), fabrica(20));
    let b = fabrica(5);
    println!("{}", b[1]);
    println!("{:?}", transpuesta([[1, 2, 3], [4, 5, 6]]));
    let m = [[1, 2, 3], [4, 5, 6]];
    let t = transpuesta(m);
    println!("{:?} {}", t, t[2][1]);
    let mut k = 0;
    while k < 3 { let z = duplicar(a); println!("{}", z[k]); k += 1; }
    println!("{:?}", a);
}
