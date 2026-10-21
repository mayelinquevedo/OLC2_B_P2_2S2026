fn main() {
    let mut matrix: [[i32; 3]; 2] = [[1, 2, 3],[4, 5, 6]];
    let cubo: [[[i32; 2]; 2]; 2] = [[[1, 2], [3, 4]],[[5, 6], [7, 8]]];
    matrix[1][2] = 7;
    println!("Valor modificado: {}", matrix[1][2]);
    println!("{}", cubo[1][0][1]);
    println!("{}", matrix.len());
}
