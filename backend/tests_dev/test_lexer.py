from compiler.lexer.lexer import lexer
from compiler.errors import limpiar_errores, hay_errores, imprimir_reporte

codigo = '''
fn main() {
    let x: i32 = 10;
    let y: i32 = 20;

    if x >= y && x != 0 {
        let z = x + y * 2 - 1 / 2 % 3;
    }

    let total = @100;

    let arr = [1, 2, 3];
    let slice = &arr[1..2];

    let nombre = String::from("mayelin");

    /* comentario sin cerrar
}
'''

limpiar_errores()
lexer.input(codigo)

print("=== TOKENS ===")
for tok in lexer:
    print(tok)

print("\n=== ERRORES ===")
if hay_errores():
    imprimir_reporte()
else:
    print("Sin errores léxicos.")