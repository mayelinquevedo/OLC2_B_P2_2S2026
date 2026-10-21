fn suma(a: [i32; 3]) -> i32 { return a[0] + a[1] + a[2]; }
fn primero(s: &[i32]) -> i32 { return s[0]; }
fn main() {
    let a = [1, 2, 3];
    println!("{}", suma(a));
    println!("{}", a[0]);
    let b = a;
    println!("{:?}", b);
    let m = [[1, 2], [3, 4]];
    println!("{:?}", m);
    println!("{}", m);
    println!("{}", m[1][0]);
    let fs = [1.5, 2.5];
    let cs = ['a', 'b'];
    let ss = [String::from("x"), String::from("y")];
    let bs = [true, false];
    println!("{:?} {:?} {:?} {:?}", fs, cs, ss, bs);
    let s = &a[1..3];
    println!("{} {} {}", s.len(), s[0], s[1]);
    println!("{}", primero(s));
    println!("{}", s.contains(3));
    println!("{}", s.contains(1));
    let t = &s[1..2];
    println!("{:?}", t);
    println!("{}", a.contains(2));
    println!("{}", fs.contains(2.5));
    println!("{}", ss.contains(String::from("y")));
    println!("{}", cs.contains('z'));
    println!("{:?} {:?}", String::from("hi"), 'q');
    println!("{{}} llaves {{{}}}", 5);
    let mut ms = [5, 6, 7];
    let v = &ms[0..2];
    println!("{:?}", v);
    let e = &a[1..1];
    println!("{:?} {}", e, e.len());
}
