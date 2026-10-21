fn main() {
    println!("{}", 3 < 4);
    println!("{}", 3 >= 4);
    println!("{}", 3.5 > 2);
    println!("{}", 2 == 2.0);
    println!("{}", 'a' == 'a');
    println!("{}", 'a' < 'b');
    println!("{}", true == false);
    println!("{}", true != false);
    let s1 = String::from("hola");
    let s2 = String::from("hola");
    println!("{}", s1 == s2);
    println!("{}", s1 != s2);
    println!("{}", String::from("a") < String::from("b"));
    println!("{}", 5 == 'a');
    let c: char = 'Z';
    println!("{}", c);
    println!("{}", typeof(c));
    println!("{}", typeof(3));
    println!("{}", typeof(3.0));
    println!("{}", typeof(true));
    println!("{}", true && false || !false);
}
