# OxigenNative — Manual de usuario


Nombre: Mayelin Lucía Quevedo Camey
carnet: 202307771

CURSO: Organizacion de lenguajes y compiladores 2
seccion: B

OxigenNative es un entorno web para escribir programas en un lenguaje inspirado en Rust, compilarlos a ensamblador
**ARM64** y ejecutarlos. Esta guía explica cómo instalar la herramienta, usar el editor e interpretar los reportes.



## 1. Instalación paso a paso

Requisitos: Linux (o Windows con WSL2 + Ubuntu), Python 3.10 o superior, Graphviz, QEMU user mode y las herramientas
binutils para ARM64.

1. Instale los paquetes del sistema:
   ```bash
   sudo apt update
   sudo apt install -y python3 python3-venv graphviz qemu-user binutils-aarch64-linux-gnu
   ```
2. Descargue el proyecto y entre a `backend/`:
   ```bash
   git clone https://github.com/mayelinquevedo/OLC2_B_P2_2S2026.git
   cd OLC2_B_P2_2S2026/backend
   ```
3. Cree el entorno virtual e instale las dependencias de Python:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
4. Compruebe que las herramientas ARM64 estén disponibles:
   ```bash
   aarch64-linux-gnu-as --version
   qemu-aarch64 --version
   dot -V
   ```
5. Inicie el servidor:
   ```bash
   python -m api.app
   ```
6. Abra **http://127.0.0.1:5000** en el navegador.

- ![inicio](img/captura_inicio.png) 

 

## 2. La interfaz

| Zona | Descripción |
|---|---|
| **Barra superior** | `Nuevo`, `Abrir`, `Guardar`, `Ejecutar` y el menú `Reportes ▾` |
| **Editor** | Área con numeración de líneas donde se escribe el programa |
| **Código ARM64 generado** | A la derecha del editor; es exactamente el ensamblador que se ejecuta en el servidor. Botón `Copiar` |
| **Consola de salida** | Abajo a la izquierda: mensajes de estado (*Compilación exitosa*), salida del programa, errores de ejecución y tiempo |
| **Panel de reportes** | Abajo a la derecha, en pestañas: **Errores**, **Tabla de símbolos**, **AST** |

![inicio](img/captura_interfaz.png)

![inicio](img/Nuevo_Abrir_Ejecutar.png)

![inicio](img/REPORTES.png)

## 3. Crear, editar y ejecutar código

1. **Nuevo**: limpia el editor para empezar un programa.

![inicio](img/nuevo.png)

2. **Abrir**: carga un archivo `.ox`, `.rs` o `.txt` desde su computador.

![inicio](img/abrir.png)

3. Escriba el programa. Todo programa necesita una función `main`:

![alt text](img/escritura.png)
   ```rust
   fn main() {
       let mut contador = 0;
       while contador < 3 {
           println!("Contador: {}", contador);
           contador += 1;
       }
   }
   ```



4. **Guardar**: descarga el contenido del editor como archivo `.ox`.

![alt text](img/guardar.png)


5. **Ejecutar** (o `Ctrl+Enter`): envía el código al servidor, que lo compila, lo ensambla, lo enlaza y lo ejecuta con QEMU.
   - Si todo sale bien, la consola muestra la salida y el panel ARM64 muestra el ensamblador.
   - Si hay errores, la consola los lista y **luego ejecuta el resto del programa**; el panel **Errores** muestra la tabla completa.
   - Solo se detiene sin ejecutar cuando el error es crítico (por ejemplo, no existe la función `main`).


![alt text](img/ejecutar.png)
![inicio](img/captura_ejecucion.png)

### Referencia rápida del lenguaje

| Elemento | Ejemplo |
|---|---|
| Tipos | `i32`, `f64`, `bool`, `char`, `String`, `[i32; 5]`, `[[i32; 3]; 2]` |
| Variables | `let x = 10;` (inmutable) · `let mut y: f64 = 2.5;` (mutable) · `let z: i32;` (valor por defecto) |
| Asignación | `=`, `+=`, `-=`, `*=`, `/=`, `%=` |
| Operadores | `+ - * / %` · `== != < > <= >=` · `&& \|\| !` (con cortocircuito) |
| Control | `if / else if / else`, `while`, `loop` (con `break`/`continue`, etiquetas `'outer:`), `match` con `_` |
| Funciones | `fn sumar(a: i32, b: i32) -> i32 { return a + b; }` |
| Salida | `println!("Valor: {}", x);` · `{:?}` para depurar · `{{` `}}` para llaves literales |
| Arreglos | `let a = [1, 2, 3];` · `a[0]` · `a.len()` · `a.contains(2)` · `a.reverse()` · `&a[1..3]` (slice) |
| Strings | `String::from("hola")`, `+`, `len`, `contains`, `replace`, `split`, `to_uppercase`, `to_lowercase` |
| Otros | `typeof(x)`, `random(1, 10)`, comentarios `//` y `/* */`, raw strings `r"C:\ruta"` |

## 4. Reportes

Se generan automáticamente en cada ejecución y se pueden ver en las pestañas del panel inferior derecho. El menú
**Reportes ▾** permite abrirlos en una pestaña nueva o descargarlos.

- ![alt text](img/REPORTES.png)

- ![alt text](img/errores_html.png)

- ![alt text](img/tabla_html.png)

- ![alt text](img/ast_html.png)



### 4.1 Reporte de errores

Tabla con **No, Tipo, Descripción, Línea, Columna y Fragmento** del código. Al hacer clic en una fila el editor salta a la
línea del error. Tipos: *Léxico* (carácter no reconocido, comentario de bloque sin cerrar), *Sintáctico* (`Se esperaba ';'`,
llaves sin cerrar) y *Semántico* (variable no declarada, tipos incompatibles, modificar una variable inmutable, índice fuera
de límites, función no declarada, número incorrecto de argumentos, ...). El compilador continúa tras un error para reportar
varios en una sola ejecución.

**El programa no se detiene por un error.** El compilador reporta el error y sigue con el resto del código:
una expresión inválida vale `None`, y una instrucción inválida (por ejemplo, modificar una variable inmutable) simplemente
no se ejecuta. Si falta un `;`, `)` o `}`, lo indica (`Se esperaba ';'`) y continúa como si estuviera escrito.

Ejemplo — el programa
```rust
fn main() {
    let edad: i32 = "veinte";
    println!(total);
}
```
produce en la consola:
```
Se encontraron 2 error(es); se ejecutó el resto del programa.
[Error Semántico] Línea 2, Columna 21
No es posible asignar un valor de tipo String a una variable de tipo i32.
[Error Semántico] Línea 3, Columna 14
La variable 'total' no ha sido declarada.
── Programa en ejecución ──
None
```
(`total` no existe, por eso se imprime `None`).

![inicio](img/captura_errores.png)

### 4.2 Tabla de símbolos

Una fila por cada variable, parámetro y función: **Identificador, Categoría, Tipo, Ámbito, Línea y Valor**. El ámbito es
`Global` o el nombre de la función donde se declaró; el valor aparece cuando es una constante conocida en compilación.

![alt text](img/tablasimbolos.png)

### 4.3 AST

Imagen del árbol de sintaxis abstracta generado con Graphviz. Tiene controles de zoom (`−`, `+`, `100%`). Desde el menú **Reportes ▾**
puede abrirse como SVG en una pestaña nueva o descargarse el archivo fuente `.dot`.

![inicio](img/captura_ast.png)

## 5. Ejemplo de sesión completa

1. Abra la aplicación y pulse **Nuevo**.
2. Escriba:
   ```rust
   fn main() {
       let numeros = [10, 20, 30, 40, 50];
       let parte = &numeros[1..4];
       println!("Slice: {:?}", parte);
       println!("Suma: {}", numeros[0] + numeros[4]);
   }
   ```
3. Pulse **Ejecutar**. La consola muestra:
   ```
   Slice: [20, 30, 40]
   Suma: 60
   ```
4. Revise el panel ARM64: verá la función `fn_main`, el prólogo con `stp x29, x30, [sp, #-16]!` y las llamadas a las
   rutinas de impresión.
5. Cambie `numeros[4]` por `numeros[9]` y ejecute otra vez: el compilador reporta *Índice fuera de los límites del arreglo*
   en la pestaña **Errores**, y el programa continúa imprimiendo `Slice: [20, 30, 40]` y `Suma: None`.

![inicio](img/captura_sesion.png)

## 6. Solución de problemas

| Síntoma | Causa y solución |
|---|---|
| `aarch64-linux-gnu-as: command not found` | Falta `sudo apt install binutils-aarch64-linux-gnu` |
| `qemu-aarch64: command not found` | Falta `sudo apt install qemu-user` |
| El panel AST aparece vacío | Falta Graphviz: `sudo apt install graphviz` |
| *El programa excedió 10 segundos* | Hay un bucle infinito (`loop` sin `break`) |
| La página no carga | Verifique que `python -m api.app` siga corriendo y que use el puerto 5000 |
