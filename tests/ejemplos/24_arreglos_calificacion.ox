// =====================================================================
//  OxigenNative - Proyecto 2 - Archivo de calificacion UNIFICADO: 5_arreglos
//  SECCION 5 - Arreglos (19 pts)
//
//  Reune los archivos por criterio de entradas/. Cada criterio tiene su banner y
//  sus bloques CASO; cada bloque usa variables propias, asi que se puede borrar
//  un criterio completo (o un caso) sin romper el resto.
//  Salida esperada: calificacion/esperadas/5_arreglos.esperado.txt
//
//  Criterios incluidos:
//    - 5.1: Declaracion inmutable explicita e inferida (0.5 c/u = 1 pt)
//    - 5.2: Declaracion mutable explicita e inferida (0.5 c/u = 1 pt)
//    - 5.3: Asignacion y acceso a elemento (0.5 c/u = 1 pt)
//    - 5.4: Declaracion de slices (1 pt)
//    - 5.5: find_max(arr) -> i32 (3 pts)
//    - 5.6: sort_array(arr) (3 pts) - ordenamiento burbuja ascendente
//    - 5.7: compare_arrays(a, b) -> bool (4 pts)
//    - 5.8: multiply_matrix(a, b) (5 pts)
// =====================================================================
// ---- Funciones del criterio 5.5: find_max(arr) -> i32 (3 pts) ----
fn find_max(datos: [i32; 6]) -> i32 {
    let mut maximo: i32 = datos[0];
    let mut i: i32 = 1;
    while i < datos.len() {
        if datos[i] > maximo {
            maximo = datos[i];
        }
        i += 1;
    }
    return maximo;
}
// ---- Funciones del criterio 5.6: sort_array(arr) (3 pts) - ordenamiento burbuja ascendente ----
fn sort_array(datos: [i32; 6]) -> [i32; 6] {
    let mut res: [i32; 6] = [0, 0, 0, 0, 0, 0];
    let mut k: i32 = 0;
    while k < 6 {
        res[k] = datos[k];
        k += 1;
    }

    let mut i: i32 = 0;
    while i < 5 {
        let mut j: i32 = 0;
        while j < 5 - i {
            if res[j] > res[j + 1] {
                let temporal: i32 = res[j];
                res[j] = res[j + 1];
                res[j + 1] = temporal;
            }
            j += 1;
        }
        i += 1;
    }
    return res;
}
// ---- Funciones del criterio 5.7: compare_arrays(a, b) -> bool (4 pts) ----
fn compare_arrays(a: [i32; 5], b: [i32; 5]) -> bool {
    if a.len() != b.len() {
        return false;
    }
    let mut i: i32 = 0;
    while i < a.len() {
        if a[i] != b[i] {
            return false;
        }
        i += 1;
    }
    return true;
}
// ---- Funciones del criterio 5.8: multiply_matrix(a, b) (5 pts) ----
fn multiply_matrix(a: [[i32; 3]; 2], b: [[i32; 2]; 3]) -> [[i32; 2]; 2] {
    let mut r: [[i32; 2]; 2] = [[0, 0], [0, 0]];
    let mut i: i32 = 0;
    while i < 2 {
        let mut j: i32 = 0;
        while j < 2 {
            let mut k: i32 = 0;
            while k < 3 {
                r[i][j] = r[i][j] + a[i][k] * b[k][j];
                k += 1;
            }
            j += 1;
        }
        i += 1;
    }
    return r;
}

fn multiply_matrix_2x2(a: [[i32; 2]; 2], b: [[i32; 2]; 2]) -> [[i32; 2]; 2] {
    let mut r: [[i32; 2]; 2] = [[0, 0], [0, 0]];
    let mut i: i32 = 0;
    while i < 2 {
        let mut j: i32 = 0;
        while j < 2 {
            let mut k: i32 = 0;
            while k < 2 {
                r[i][j] = r[i][j] + a[i][k] * b[k][j];
                k += 1;
            }
            j += 1;
        }
        i += 1;
    }
    return r;
}

fn main() {
    // ######################################################################
    // ## CRITERIO 5.1: Declaracion inmutable explicita e inferida (0.5 c/u = 1 pt)
    // ######################################################################
    // ===== CASO 5.1-a: declaracion explicita [salida: 1 linea] =====
    let explicito: [i32; 5] = [10, 20, 30, 40, 50];
    println!("{:?}", explicito);

    // ===== CASO 5.1-b: declaracion inferida [salida: 1 linea] =====
    let inferido = [18, 20, 22];
    println!("{:?}", inferido);

    // ######################################################################
    // ## CRITERIO 5.2: Declaracion mutable explicita e inferida (0.5 c/u = 1 pt)
    // ######################################################################
    // ===== CASO 5.2-a: declaracion mutable explicita [salida: 1 linea] =====
    let mut m_explicito: [i32; 3] = [1, 2, 3];
    println!("{:?}", m_explicito);

    // ===== CASO 5.2-b: declaracion mutable inferida [salida: 1 linea] =====
    let mut m_inferido = [4, 5, 6];
    println!("{:?}", m_inferido);

    // ######################################################################
    // ## CRITERIO 5.3: Asignacion y acceso a elemento (0.5 c/u = 1 pt)
    // ######################################################################
    // ===== CASO 5.3-a: arreglo 1D, acceso y asignacion por indice [salida: 4 lineas] =====
    let mut datos: [i32; 4] = [10, 20, 30, 40];
    println!("{}", datos[0]);
    println!("{}", datos[3]);
    datos[1] = 99;
    println!("{}", datos[1]);
    println!("{:?}", datos);

    // ===== CASO 5.3-b: matriz 2D, acceso y asignacion por doble indice [salida: 4 lineas] =====
    let mut matriz: [[i32; 3]; 2] = [[1, 2, 3], [4, 5, 6]];
    println!("{}", matriz[1][2]);
    matriz[1][2] = 7;
    println!("{}", matriz[1][2]);
    println!("{}", matriz[0][0]);
    println!("{}", matriz[0][2]);

    // ######################################################################
    // ## CRITERIO 5.4: Declaracion de slices (1 pt)
    // ######################################################################
    // Preparacion comun a los 4 casos (no puntua por separado).
    let numeros: [i32; 5] = [10, 20, 30, 40, 50];

    // ===== CASO 5.4-a: slice interior [1..4] [salida: 1 linea] =====
    let parte = &numeros[1..4];
    println!("{:?}", parte);

    // ===== CASO 5.4-b: slice desde el inicio [0..2] [salida: 1 linea] =====
    let inicio = &numeros[0..2];
    println!("{:?}", inicio);

    // ===== CASO 5.4-c: slice hasta el final [3..5] [salida: 1 linea] =====
    let ultimos = &numeros[3..5];
    println!("{:?}", ultimos);

    // ===== CASO 5.4-d: el arreglo original no se modifica [salida: 1 linea] =====
    println!("{:?}", numeros);

    // ######################################################################
    // ## CRITERIO 5.5: find_max(arr) -> i32 (3 pts)
    // ######################################################################
    // ===== CASO 5.5-a: maximo en el medio [salida: 1 linea] =====
    let fm_a: [i32; 6] = [12, 45, 7, 89, 23, 56];
    println!("{}", find_max(fm_a));

    // ===== CASO 5.5-b: todos negativos [salida: 1 linea] =====
    let fm_b: [i32; 6] = [-5, -20, -3, -40, -1, -9];
    println!("{}", find_max(fm_b));

    // ===== CASO 5.5-c: maximo en la primera posicion [salida: 1 linea] =====
    let fm_c: [i32; 6] = [9, 1, 2, 3, 4, 5];
    println!("{}", find_max(fm_c));

    // ===== CASO 5.5-d: maximo en la ultima posicion [salida: 1 linea] =====
    let fm_d: [i32; 6] = [1, 2, 3, 4, 5, 9];
    println!("{}", find_max(fm_d));

    // ===== CASO 5.5-e: todos iguales [salida: 1 linea] =====
    let fm_e: [i32; 6] = [4, 4, 4, 4, 4, 4];
    println!("{}", find_max(fm_e));

    // ######################################################################
    // ## CRITERIO 5.6: sort_array(arr) (3 pts) - ordenamiento burbuja ascendente
    // ######################################################################
    // ===== CASO 5.6-a: desordenado [salida: 1 linea] =====
    let so_a: [i32; 6] = [45, 12, 89, 7, 56, 23];
    let ord_a: [i32; 6] = sort_array(so_a);
    println!("{:?}", ord_a);

    // ===== CASO 5.6-b: ya ordenado [salida: 1 linea] =====
    let so_b: [i32; 6] = [1, 2, 3, 4, 5, 6];
    let ord_b: [i32; 6] = sort_array(so_b);
    println!("{:?}", ord_b);

    // ===== CASO 5.6-c: en orden inverso [salida: 1 linea] =====
    let so_c: [i32; 6] = [6, 5, 4, 3, 2, 1];
    let ord_c: [i32; 6] = sort_array(so_c);
    println!("{:?}", ord_c);

    // ===== CASO 5.6-d: con negativos y repetidos [salida: 1 linea] =====
    let so_d: [i32; 6] = [3, -1, 3, 0, -5, 2];
    let ord_d: [i32; 6] = sort_array(so_d);
    println!("{:?}", ord_d);

    // ######################################################################
    // ## CRITERIO 5.7: compare_arrays(a, b) -> bool (4 pts)
    // ######################################################################
    // ===== CASO 5.7-a: arreglos iguales [salida: 1 linea] =====
    let ca1: [i32; 5] = [1, 2, 3, 4, 5];
    let ca2: [i32; 5] = [1, 2, 3, 4, 5];
    println!("{}", compare_arrays(ca1, ca2));

    // ===== CASO 5.7-b: difieren en una posicion intermedia [salida: 1 linea] =====
    let cb1: [i32; 5] = [1, 2, 3, 4, 5];
    let cb2: [i32; 5] = [1, 2, 9, 4, 5];
    println!("{}", compare_arrays(cb1, cb2));

    // ===== CASO 5.7-c: difieren en la primera posicion [salida: 1 linea] =====
    let cc1: [i32; 5] = [9, 2, 3, 4, 5];
    let cc2: [i32; 5] = [1, 2, 3, 4, 5];
    println!("{}", compare_arrays(cc1, cc2));

    // ===== CASO 5.7-d: difieren en la ultima posicion [salida: 1 linea] =====
    let cd1: [i32; 5] = [1, 2, 3, 4, 5];
    let cd2: [i32; 5] = [1, 2, 3, 4, 9];
    println!("{}", compare_arrays(cd1, cd2));

    // ===== CASO 5.7-e: iguales con negativos y ceros [salida: 1 linea] =====
    let ce1: [i32; 5] = [-1, 0, -3, 4, 0];
    let ce2: [i32; 5] = [-1, 0, -3, 4, 0];
    println!("{}", compare_arrays(ce1, ce2));

    // ######################################################################
    // ## CRITERIO 5.8: multiply_matrix(a, b) (5 pts)
    // ######################################################################
    // ===== CASO 5.8-a: 2x3 por 3x2 -> 2x2 [salida: 2 lineas] =====
    let ma: [[i32; 3]; 2] = [[1, 2, 3], [4, 5, 6]];
    let mb: [[i32; 2]; 3] = [[7, 8], [9, 10], [11, 12]];
    let mr: [[i32; 2]; 2] = multiply_matrix(ma, mb);
    println!("{} {}", mr[0][0], mr[0][1]);
    println!("{} {}", mr[1][0], mr[1][1]);

    // ===== CASO 5.8-b: 2x2 por 2x2 [salida: 2 lineas] =====
    let na: [[i32; 2]; 2] = [[1, 2], [3, 4]];
    let nb: [[i32; 2]; 2] = [[5, 6], [7, 8]];
    let nr: [[i32; 2]; 2] = multiply_matrix_2x2(na, nb);
    println!("{} {}", nr[0][0], nr[0][1]);
    println!("{} {}", nr[1][0], nr[1][1]);

    // ===== CASO 5.8-c: 2x2 por la identidad [salida: 2 lineas] =====
    let ia: [[i32; 2]; 2] = [[1, 2], [3, 4]];
    let ib: [[i32; 2]; 2] = [[1, 0], [0, 1]];
    let ir: [[i32; 2]; 2] = multiply_matrix_2x2(ia, ib);
    println!("{} {}", ir[0][0], ir[0][1]);
    println!("{} {}", ir[1][0], ir[1][1]);
}
