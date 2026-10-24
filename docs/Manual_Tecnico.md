# OxigenNative — Documentación técnica

Nombre: Mayelin Lucía Quevedo Camey
carnet: 202307771

CURSO: Organizacion de lenguajes y compiladores 2
seccion: B


Compilador de paso único para un lenguaje de sintaxis inspirada en Rust. Traduce el AST **directamente** a
ensamblador ARM64 (sin código de tres direcciones), ensambla, enlaza y ejecuta el resultado con QEMU user mode.

## 1. Arquitectura

Aplicación monolítica cliente/servidor con cuatro componentes 
- ![flujo](img/flujo.png)  

- ![módulos](img/modulos.png)

| Componente | Tecnología | Responsabilidad |
|---|---|---|
| Presentación | HTML/CSS/JS + React (sin build) | Editor con numeración de líneas, consola, panel ARM64 y pestañas de reportes |
| Lógica y servicios | Python + Flask | `POST /api/compilar` recibe el código y devuelve un JSON con errores, símbolos, ARM64, salida y AST |
| Definición del lenguaje | PLY (lex/yacc) | Reglas léxicas y gramática; construye un AST propio |
| Simulación ARM64 | binutils-aarch64 + QEMU | `as` → `ld` → `qemu-aarch64`; se captura stdout/stderr |

Pipeline (`compiler/pipeline.py`): **léxico → sintáctico (AST) → semántico → generación ARM64 → ensamblar → enlazar → ejecutar**.
Los reportes (errores, símbolos, AST) se generan siempre, incluso cuando hay errores. El código ARM64 mostrado en la GUI es
**exactamente** el archivo `programa.s` que se ensambla y ejecuta.

Diagramas: 
- ![flujo de procesamiento](img/flujo.png)

- ![clases del AST](img/clases.png) 

- ![módulos](img/modulos.png)

## 2. Gramática formal

### 2.1 Léxico

```
identifier ::= ( letter | "_" ) ( letter | digit | "_" )*     (case sensitive; "_" solo es el comodín de match)
integer    ::= digit+            decimal ::= digit+ "." digit+
string     ::= '"' ( char | escape )* '"'                       escapes: \n \t \r \0 \\ \" \'
raw_string ::= 'r"' ... '"' | 'r#"' ... '"#' | 'r##"' ... '"##'  (sin escapes)
char       ::= "'" ( char | escape ) "'"
label      ::= "'" identifier                                  ('outer, 'inner)
comment    ::= "//" ... fin de línea | "/*" ... "*/"           (descartados; "/*" sin cierre = error léxico)
palabras reservadas: fn let mut if else while loop match break continue return true false
tipos: i32 f64 bool char String
operadores: + - * / % == != > >= < <= && || ! = += -= *= /= %= .. & . :: -> =>
```

### 2.2 Sintaxis (tal como la implementa `parser.py`)

```
program      ::= function+
function     ::= "fn" id "(" [ param { "," param } ] ")" [ "->" type ] block
param        ::= id ":" type
type         ::= "i32" | "f64" | "bool" | "char" | "String"
               | "[" type ";" integer "]"          arreglo (recursivo: matrices N-dimensionales)
               | "&" "[" type "]"                  slice
               | "Vec" "<" "&" "str" ">"           (equivale a un slice de String)
block        ::= "{" statement* "}"
statement    ::= var_decl | assignment | if | while | loop | match
               | "break" [label] ";" | "continue" [label] ";" | "return" [expr] ";" | expr ";"
var_decl     ::= "let" ["mut"] id [ ":" type ] [ "=" expr ] ";"
assignment   ::= expr ( "=" | "+=" | "-=" | "*=" | "/=" | "%=" ) expr ";"
if           ::= "if" expr block [ "else" ( block | if ) ]          (sin paréntesis; la condición debe ser bool)
while        ::= "while" expr block
loop         ::= [ label ":" ] "loop" block
match        ::= "match" expr "{" arm { arm } "}"
arm          ::= ( expr | "_" ) "=>" ( block | expr ) [ "," ]      (la coma es opcional tras un bloque y en el último caso)
expr         ::= expr binop expr | "-" expr | "!" expr | "(" expr ")"
               | integer | decimal | string | char | "true" | "false" | id
               | id "(" args ")"                         llamada a función
               | id "!" "(" args ")"                     println!
               | "[" args "]"                            literal de arreglo
               | expr "[" expr "]"                       acceso por índice (encadenable: m[i][j])
               | "&" expr "[" expr ".." expr "]"         slice
               | expr "." id "(" args ")"                método: len contains replace split ...
               | "String" "::" id "(" args ")"           String::from / String::new
```

Precedencia (menor → mayor): `||`, `&&`, `== !=`, `< > <= >=`, `+ -`, `* / %`, unarios (`- !`), `[ ]` y `.`.
La gramática se compila con **0 conflictos shift/reduce** (`parser.out`). El `match` se modeló para aceptar coma final
opcional y bloques sin coma, igual que Rust; el comodín `_` es un token propio (`COMODIN`).

### 2.3 AST

Clases propias en `ast/nodos.py`

 ![diagrama](img/clases.png). 
 
 Todas heredan de `Nodo` (línea, columna, `tipo_resultado`)
y se recorren con el patrón **Visitor** (`nodo.aceptar(visitor)`); hay tres visitors: el analizador semántico, el generador
ARM64 y el generador del reporte DOT.

## 3. Análisis semántico

- **Tabla de símbolos con scopes anidados** (`semantic/tabla_simbolos.py`): una pila de diccionarios; `let` puede *sombrear*
  (shadowing) una variable previa incluso con otro tipo. Cada símbolo guarda nombre, categoría (variable/función/parámetro),
  tipo, ámbito, línea y valor; es el origen del reporte de símbolos.
- **Tipado estático con inferencia**: `let x = 10;` → `i32`; `let n = String::from("a")` → `String`.
- **Mutabilidad**: asignar a una variable sin `mut` produce error semántico. Variables sin valor inicial usan el valor por
  defecto del tipo (`0`, `0.0`, `false`, `""`).
- **Tablas de tipos** de los operadores (suma, resta, multiplicación, división, módulo, relacionales, lógicos) implementadas
  según el enunciado, incluyendo la promoción `i32 → f64`, `String + String`, `i32 * String` (repetición) y comparaciones
  `i32/f64/char`. Un operador con tipos no válidos genera error semántico y el resultado es `None`.
- Otras validaciones: variable/función no declarada, número y tipo de argumentos, tipo de retorno, condiciones `bool`,
  `break`/`continue` fuera de ciclo y etiquetas inexistentes, rango de slices y índices constantes fuera de límites,
  cadena de formato de `println!` (`{}`, `{:?}`, `{{`, `}}`) con el número de argumentos correcto, y existencia de **una única `main`**.
- **Resiliencia**: los errores léxicos, sintácticos y semánticos se acumulan en una tabla y el compilador **continúa**
  para reportar varios errores en una sola corrida. Cada error incluye tipo, descripción, línea, columna y el fragmento de
  código. Salvo que el error sea crítico, el resto del programa **también se compila y se ejecuta** (sección 3.1).

### 3.1 Recuperación ante errores

El enunciado pide que los errores se reporten sin detener necesariamente el programa. Se resuelve en tres niveles,
según la fase donde ocurre el error:

| Fase | Estrategia |
|---|---|
| **Léxico** | El lexer reporta el carácter no reconocido (o el comentario sin cerrar), lo descarta y sigue; el resto de los tokens llega intacto al parser |
| **Sintáctico** | Si falta un `;`, `)`, `]` o `}` evidente, `p_error` lo detecta consultando la tabla de acciones de PLY (`parser.action[estado]`), reporta `Se esperaba ';'` en la posición justo después del último token válido e **inserta un token virtual** (el token que falló se devuelve al parser con `LexerConCola`). Así la sentencia no se pierde. En cualquier otro caso se usa modo pánico (`sentencia : error ;`): se omite la sentencia hasta el siguiente `;`. Una guarda (`_insertados`) evita ciclos |
| **Semántico** | El analizador marca cada nodo con error (`con_error`). `recuperacion.py` sanea una **copia** del AST antes de generar código (ver abajo) |

Saneamiento del AST (`compiler/recuperacion.py`):

- Una **expresión inválida** se reemplaza por un nodo `ErrorExpr`, que vale `0` al ejecutarse y se imprime como `None`
  (igual que en el ejemplo del enunciado: `let r = a + nombre; println!(r);` imprime `None`). Un `ErrorExpr` dentro de una
  expresión contamina a las que la contienen.
- Una **sentencia inválida** se omite: asignación a una variable inmutable o de tipo incorrecto, `break`/`continue` fuera de un
  ciclo, `return` inválido, `println!` con marcadores que no coinciden.
- `let x: T = <inválido>;` conserva la variable con el valor por defecto de `T`; `let x = <inválido>;` (sin tipo) se omite y sus
  usos se vuelven `None`.
- Una **condición inválida** (`if`/`while`) cuenta como falsa; un caso de `match` con patrón inválido se descarta.
- El AST original no se modifica: los reportes (AST y tabla de símbolos) se generan con el árbol sin sanear.

**Errores críticos** (el programa no se ejecuta): que no exista exactamente una función `main`, o un error sintáctico tan grave
que el parser no pueda producir ningún AST. El resultado de la API informa `ok: true` con la lista de errores cuando el
programa se ejecutó tras recuperarse, y `ok: false` cuando fue crítico.

## 4. Generación de código ARM64

### 4.1 Modelo de memoria

| Región | Uso |
|---|---|
| **Stack** | Variables locales, parámetros recibidos, arreglos, registros guardados, temporales de expresiones |
| **Heap** | Strings dinámicos (resultado de `+`, `replace`, `to_uppercase`, ...), descriptores de slices y resultados de `split`. Es un arreglo de 64 MB en `.bss` con asignador *bump* (`heap_alloc`); si se agota, el programa termina con error de memoria |
| **.data** | Literales de cadena |

Representación de valores (todos ocupan **8 bytes** en el stack para simplificar el direccionamiento):

| Tipo | Representación |
|---|---|
| `i32`, `bool`, `char` | entero en `x0` (`char` = punto de código Unicode; `bool` = 0/1) |
| `f64` | `d0` (IEEE-754 doble precisión; en el stack ocupa 8 bytes) |
| `String` | puntero a un bloque `[longitud: 8 bytes][bytes UTF-8]` (en `.data` o en el heap) |
| `[T; N]` | `N` elementos contiguos de 8 bytes en el frame de la función (matrices aplanadas) |
| `&[T]` (slice) | puntero a un descriptor de 16 bytes en el heap: `[longitud][puntero al primer elemento]` |

### 4.2 Convención de llamadas AArch64 y stack frame

- Parámetros en `x0–x7` (enteros, punteros, direcciones de arreglo) y `d0–d7` (`f64`); retorno en `x0` / `d0`.
- `x29` = frame pointer, `x30` = link register, `sp` alineado a 16 bytes.
- **Prólogo**: `stp x29, x30, [sp, #-16]!` · `mov x29, sp` · `sub sp, sp, #N` (reserva de locales).
  **Epílogo**: `mov sp, x29` · `ldp x29, x30, [sp], #16` · `ret`.
- Las variables locales viven en `[x29 - offset]`. Un arreglo se reserva como un bloque contiguo y el elemento `k` está
  en `base + 8·k`.
- Los arreglos pasados como argumento viajan por **dirección** y el receptor los **copia** a su frame (paso por valor,
  como en Rust). Un `let b = a;` también copia.
- Las expresiones dejan su resultado en `x0`/`d0`; los operandos intermedios se apilan con `str x0, [sp, #-16]!`.

### 4.3 Instrucciones generadas

Aritmética `add sub mul sdiv` (y `msub` para el módulo), `fadd fsub fmul fdiv` para `f64`, comparaciones con `cmp`/`fcmp` +
`cset`/`b.cond`, pila con `stp ldp str ldr`, control de flujo con etiquetas únicas y `b`, `b.eq/ne/lt/...`, `cbz/cbnz`.
Cada función genera su bloque con prólogo/epílogo, y el código incluye comentarios (`//`) de inicio/fin de función, manejo
de stack frame, uso de registros y puntos críticos del flujo.

### 4.4 Decisiones de generación

- **Cortocircuito** (`&&`, `||`): se evalúa el operando izquierdo y se salta al final sin evaluar el derecho si ya decide el
  resultado (obligatorio por el enunciado; probado con una función con efecto secundario en `tests/ejemplos/09`).
- **`loop`/`while`/`break`/`continue` con etiquetas**: una pila de bucles asocia cada etiqueta de fuente (`'outer`) con
  sus etiquetas de ensamblador de continuar/salir.
- **`match`**: el valor se guarda en una variable temporal y se compara con cada patrón en orden (`i32`, `char`, `bool`,
  `String` vía `str_cmp`); `_` es el comodín.
- **Arreglos multidimensionales — estrategia Row-Major**: se eligió *Row-Major* (offset = `i·C + j`, generalizado a
  N dimensiones) porque es el orden de C/C++/Rust —el lenguaje que inspira OxigenNative—, lo que hace que el recorrido
  natural `for fila { for columna }` sea secuencial en memoria, y porque permite calcular el desplazamiento acumulando
  `offset = offset·dimensión_k + índice_k` de izquierda a derecha sin conocer la primera dimensión. Los índices
  constantes se validan en compilación; los no constantes se verifican **en ejecución** (`cmp` sin signo + salto a
  `rt_indice`, lo que también atrapa índices negativos).
- **Slices**: `&a[i..j]` crea un descriptor `[longitud][dirección]` que **apunta al arreglo original** (no copia los
  elementos), con verificación de `i ≤ j ≤ longitud` en ejecución. Funcionan `len()`, indexación, `contains`, impresión,
  paso a funciones y slices de slices.
- **Impresión**: `println!` admite `{}` y `{:?}`; las rutinas imprimen directo con `write` (syscall 64). `{:?}` muestra
  `String` entre comillas dobles y `char` entre simples. Arreglos y slices siempre salen como `[a, b, c]` (anidados para
  matrices), también con `println!(arreglo)`. Los `f64` se imprimen con hasta 15 cifras significativas y sin ceros
  sobrantes, siempre con parte decimal (`3.0`, `12.5`, `0.3`), además de `NaN`, `inf` y `-inf`.
- **Errores de ejecución**: división entre cero, índice fuera de límites y falta de memoria se detectan en tiempo de
  ejecución, imprimen `Error de ejecución: ...` y terminan con código 1 (ARM64 no lanza excepción en la división por cero,
  por eso el compilador la comprueba antes de `sdiv`).
- **Rutinas de runtime** (`codegen/rutinas.py`): solo se enlazan las que el programa usa (grafo de dependencias):
  `print_int/f64/bool/char/string`, `print_arr`, `heap_alloc`, `str_concat/repeat/upper/lower/contains/replace/cmp/split`,
  `arr_contains`, `arr_quitar_vacios`, `rt_random` (syscall `getrandom`, 278) y las rutinas de error.
- **Ejecución**: `programa.s` → `aarch64-linux-gnu-as` → `aarch64-linux-gnu-ld` → `qemu-aarch64` con *timeout* de
  10 s (protege al servidor de bucles infinitos). El punto de entrada `_start` llama a `fn_main` y termina con `exit(0)`
  (syscall 93).

## 5. Desafíos enfrentados

- **PLY y el AST**: PLY solo construye el parser; el AST (clases, anotación de tipos y recorrido por *Visitor*) es propio.
- **Conflictos de gramática** en `match` (coma final opcional): se resolvieron separando el último caso y los casos con
  bloque en reglas propias; la gramática final compila sin conflictos.
- **Seguir tras un error sin inventar más errores**: omitir una sentencia con error puede generar errores en cadena (una variable
  cuya declaración se perdió). Se redujo reparando el símbolo faltante con tokens virtuales en vez de descartar la sentencia, y
  tratando los usos de una variable inválida como `None` (sin reportar errores adicionales).
- **Mensajes de error útiles**: para que falte un `;` se reporte `Se esperaba ';'` en la posición **justo después del último
  token válido**, `p_error` consulta la tabla de acciones de PLY (`parser.action[estado]`) para saber qué token se esperaba.
- **Escapes de cadena**: un `replace` encadenado falla con `"\\n"`; se procesan de izquierda a derecha con una sola expresión
  regular. Las raw strings (`r"…"`, `r#"…"#`) se reconocen *antes* que los identificadores para que la `r` no se lea como tal.
- **`split` con heap**: `heap_alloc` solo usa `x0–x5`, por lo que `str_split` mantiene su estado en registros
  *callee-saved* (`x19–x28`) y `x9/x10/x15`; está documentado en la rutina.
- **Ensamblador sin tipos**: el mismo registro puede ser entero, dirección o *double*; el generador lleva el tipo de cada
  expresión (`tipo_resultado`) para elegir `x`/`d` y la rutina de impresión correcta.

## 6. Limitaciones conocidas

- Con errores recuperables el programa se ejecuta, pero **omite** las sentencias inválidas (no intenta adivinar la intención del
  programador); un error sintáctico fuera de los casos reparables hace que se pierda esa sentencia hasta el siguiente `;`.
- No hay `struct`, `for`, `Vec` dinámico, `&mut`, referencias generales ni genéricos (fuera del alcance del enunciado).
- Un arreglo no se puede *retornar* desde una función ni usar como literal directo en un argumento (primero guárdelo en una variable).
- `match` sobre `f64` no está soportado. El heap no libera memoria (asignador *bump*).
- `split_whitespace` separa solo por espacios (no tabuladores/saltos de línea).

## 7. Pruebas

| Comando (desde `backend/`) | Qué verifica |
|---|---|
| `python3 -m tests_dev.correr_todos` | Lexer, parser, semántico, generación por tipo de construcción y pipeline completo |
| `python3 -m tests_dev.correr_ejemplos` | 41 programas de `tests/ejemplos` (ejemplos del enunciado, casos de error y de recuperación) contra su `.esperado`: errores y salida del programa |
