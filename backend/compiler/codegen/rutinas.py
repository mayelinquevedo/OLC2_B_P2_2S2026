"""Rutinas de apoyo en ensamblador ARM64 que el generador agrega al programa
solo cuando se usan. Todas escriben con la syscall write (64) en stdout."""

RUTINA_PRINT_INT = """print_int:
    # imprime x0 como entero con signo, sin salto de linea
    stp x29, x30, [sp, #-16]!
    mov x29, sp
    sub sp, sp, #32
    mov x1, sp
    add x1, x1, #32
    mov x2, #0
    mov x3, #0
    cmp x0, #0
    b.ge 1f
    mov x3, #1
    neg x0, x0
1:
    mov x4, #10
2:
    udiv x5, x0, x4
    msub x6, x5, x4, x0
    add x6, x6, #48
    sub x1, x1, #1
    strb w6, [x1]
    add x2, x2, #1
    mov x0, x5
    cbnz x0, 2b
    cbz x3, 3f
    sub x1, x1, #1
    mov w6, #45
    strb w6, [x1]
    add x2, x2, #1
3:
    mov x0, #1
    mov x8, #64
    svc #0
    mov sp, x29
    ldp x29, x30, [sp], #16
    ret
"""

RUTINA_PRINT_BOOL = """print_bool:
    # imprime x0 como true o false, sin salto de linea
    cbz x0, 1f
    adrp x1, txt_true
    add x1, x1, :lo12:txt_true
    mov x2, #4
    b 2f
1:
    adrp x1, txt_false
    add x1, x1, :lo12:txt_false
    mov x2, #5
2:
    mov x0, #1
    mov x8, #64
    svc #0
    ret
"""

RUTINA_PRINT_CHAR = """print_char:
    # imprime x0 (punto de codigo Unicode) codificado en UTF-8
    stp x29, x30, [sp, #-16]!
    mov x29, sp
    sub sp, sp, #16
    mov x1, sp
    cmp x0, #0x80
    b.hs 1f
    strb w0, [x1]
    mov x2, #1
    b 5f
1:
    cmp x0, #0x800
    b.hs 2f
    lsr x3, x0, #6
    orr x3, x3, #0xC0
    strb w3, [x1]
    and x3, x0, #0x3F
    orr x3, x3, #0x80
    strb w3, [x1, #1]
    mov x2, #2
    b 5f
2:
    mov x4, #0x10000
    cmp x0, x4
    b.hs 3f
    lsr x3, x0, #12
    orr x3, x3, #0xE0
    strb w3, [x1]
    lsr x3, x0, #6
    and x3, x3, #0x3F
    orr x3, x3, #0x80
    strb w3, [x1, #1]
    and x3, x0, #0x3F
    orr x3, x3, #0x80
    strb w3, [x1, #2]
    mov x2, #3
    b 5f
3:
    lsr x3, x0, #18
    orr x3, x3, #0xF0
    strb w3, [x1]
    lsr x3, x0, #12
    and x3, x3, #0x3F
    orr x3, x3, #0x80
    strb w3, [x1, #1]
    lsr x3, x0, #6
    and x3, x3, #0x3F
    orr x3, x3, #0x80
    strb w3, [x1, #2]
    and x3, x0, #0x3F
    orr x3, x3, #0x80
    strb w3, [x1, #3]
    mov x2, #4
5:
    mov x0, #1
    mov x8, #64
    svc #0
    mov sp, x29
    ldp x29, x30, [sp], #16
    ret
"""

# Imprime d0 con hasta 15 cifras significativas y sin ceros finales
# (siempre deja al menos un decimal: 10.0, 2.5, 0.0).
#   n = parte entera, len = sus digitos, k = 15 - len (o 15 si n == 0)
#   frac = round((|x| - n) * 10^k), se imprime con k digitos y se recortan ceros
RUTINA_PRINT_F64 = """print_f64:
    stp x29, x30, [sp, #-16]!
    mov x29, sp
    sub sp, sp, #96
    fmov x0, d0
    lsr x1, x0, #52
    and x1, x1, #0x7FF
    cmp x1, #0x7FF
    b.eq 30f
    lsr x3, x0, #63
    fabs d0, d0
    fcvtzs x4, d0
    scvtf d1, x4
    fsub d2, d0, d1
    mov x5, #1
    mov x6, x4
    mov x7, #10
40:
    cmp x6, #10
    b.lo 41f
    udiv x6, x6, x7
    add x5, x5, #1
    b 40b
41:
    mov x8, #15
    cbz x4, 42f
    cmp x5, #15
    b.ge 43f
    sub x8, x8, x5
    b 42f
43:
    mov x8, #0
42:
    mov x9, #1
    mov x10, x8
    cbz x10, 45f
44:
    mul x9, x9, x7
    subs x10, x10, #1
    b.ne 44b
45:
    scvtf d3, x9
    fmul d2, d2, d3
    fcvtns x12, d2
    cmp x12, x9
    b.ne 46f
    add x4, x4, #1
    mov x12, #0
46:
    mov x14, sp
    cbz x3, 47f
    mov w15, #45
    strb w15, [x14], #1
47:
    add x15, sp, #96
    mov x6, x4
50:
    udiv x10, x6, x7
    msub x11, x10, x7, x6
    add x11, x11, #48
    sub x15, x15, #1
    strb w11, [x15]
    mov x6, x10
    cbnz x6, 50b
    add x6, sp, #96
51:
    cmp x15, x6
    b.hs 52f
    ldrb w11, [x15], #1
    strb w11, [x14], #1
    b 51b
52:
    mov w11, #46
    strb w11, [x14], #1
    cbnz x8, 53f
    mov w11, #48
    strb w11, [x14], #1
    b 59f
53:
    add x15, sp, #96
    mov x6, x12
    mov x13, x8
54:
    udiv x10, x6, x7
    msub x11, x10, x7, x6
    add x11, x11, #48
    sub x15, x15, #1
    strb w11, [x15]
    mov x6, x10
    subs x13, x13, #1
    b.ne 54b
    add x6, sp, #96
55:
    sub x10, x6, x15
    cmp x10, #1
    b.ls 56f
    ldrb w11, [x6, #-1]
    cmp w11, #48
    b.ne 56f
    sub x6, x6, #1
    b 55b
56:
    cmp x15, x6
    b.hs 59f
    ldrb w11, [x15], #1
    strb w11, [x14], #1
    b 56b
59:
    mov x1, sp
    sub x2, x14, x1
    b 34f
30:
    and x2, x0, #0xFFFFFFFFFFFFF
    cbnz x2, 31f
    tbnz x0, #63, 32f
    adrp x1, txt_inf
    add x1, x1, :lo12:txt_inf
    mov x2, #3
    b 34f
31:
    adrp x1, txt_nan
    add x1, x1, :lo12:txt_nan
    mov x2, #3
    b 34f
32:
    adrp x1, txt_ninf
    add x1, x1, :lo12:txt_ninf
    mov x2, #4
34:
    mov x0, #1
    mov x8, #64
    svc #0
    mov sp, x29
    ldp x29, x30, [sp], #16
    ret
"""


#  Cadenas (String). Una cadena es un puntero a un bloque:
#      [ longitud en bytes: 8 bytes ][ bytes del texto ... ]
#  Las cadenas nuevas se reservan en el heap (arreglo en .bss) con un
#  asignador secuencial: heap_ptr avanza y nunca se libera.
HEAP_BYTES = 64 * 1024 * 1024

RUTINA_HEAP_ALLOC = """heap_alloc:
    # x0 = bytes necesarios -> x0 = direccion de un bloque nuevo (alineado a 16)
    add x0, x0, #15
    and x0, x0, #-16
    adrp x1, heap_ptr
    add x1, x1, :lo12:heap_ptr
    ldr x2, [x1]
    cbnz x2, 1f
    adrp x2, heap_base
    add x2, x2, :lo12:heap_base
1:
    add x3, x2, x0
    adrp x4, heap_base
    add x4, x4, :lo12:heap_base
    movz x5, #0x400, lsl #16
    add x4, x4, x5
    cmp x3, x4
    b.hi rt_memoria
    str x3, [x1]
    mov x0, x2
    ret
"""

RUTINA_PRINT_STRING = """print_string:
    # x0 = cadena. Escribe sus bytes, sin salto de linea
    ldr x2, [x0]
    add x1, x0, #8
    mov x0, #1
    mov x8, #64
    svc #0
    ret
"""

RUTINA_STR_CONCAT = """str_concat:
    # x0 = a, x1 = b -> x0 = nueva cadena a + b
    stp x29, x30, [sp, #-48]!
    mov x29, sp
    stp x0, x1, [sp, #16]
    ldr x2, [x0]
    ldr x3, [x1]
    add x4, x2, x3
    str x4, [sp, #32]
    add x0, x4, #8
    bl heap_alloc
    ldp x5, x6, [sp, #16]
    ldr x4, [sp, #32]
    str x4, [x0]
    add x7, x0, #8
    ldr x2, [x5]
    add x5, x5, #8
1:
    cbz x2, 2f
    ldrb w9, [x5], #1
    strb w9, [x7], #1
    sub x2, x2, #1
    b 1b
2:
    ldr x2, [x6]
    add x6, x6, #8
3:
    cbz x2, 4f
    ldrb w9, [x6], #1
    strb w9, [x7], #1
    sub x2, x2, #1
    b 3b
4:
    ldp x29, x30, [sp], #48
    ret
"""

RUTINA_STR_REPEAT = """str_repeat:
    # x0 = cadena, x1 = veces -> x0 = nueva cadena repetida (veces <= 0 da "")
    stp x29, x30, [sp, #-48]!
    mov x29, sp
    cmp x1, #0
    csel x1, x1, xzr, gt
    stp x0, x1, [sp, #16]
    ldr x2, [x0]
    mul x4, x2, x1
    str x4, [sp, #32]
    add x0, x4, #8
    bl heap_alloc
    ldp x5, x6, [sp, #16]
    ldr x4, [sp, #32]
    str x4, [x0]
    add x7, x0, #8
    ldr x2, [x5]
    add x5, x5, #8
1:
    cbz x6, 4f
    mov x9, x5
    mov x10, x2
2:
    cbz x10, 3f
    ldrb w11, [x9], #1
    strb w11, [x7], #1
    sub x10, x10, #1
    b 2b
3:
    sub x6, x6, #1
    b 1b
4:
    ldp x29, x30, [sp], #48
    ret
"""

RUTINA_STR_CMP = """str_cmp:
    # x0 = a, x1 = b -> x0 = -1, 0 o 1 (orden lexicografico por bytes)
    ldr x2, [x0]
    ldr x3, [x1]
    add x4, x0, #8
    add x5, x1, #8
    cmp x2, x3
    csel x6, x2, x3, lo
1:
    cbz x6, 3f
    ldrb w7, [x4], #1
    ldrb w9, [x5], #1
    cmp w7, w9
    b.ne 2f
    sub x6, x6, #1
    b 1b
2:
    mov x0, #1
    mov x10, #-1
    csel x0, x0, x10, hi
    ret
3:
    cmp x2, x3
    mov x0, #1
    mov x10, #-1
    csel x0, x0, x10, hi
    csel x0, x0, xzr, ne
    ret
"""

RUTINA_STR_UPPER = """str_upper:
    # x0 = cadena -> x0 = nueva cadena con a-z convertidas a A-Z (solo ASCII)
    stp x29, x30, [sp, #-32]!
    mov x29, sp
    str x0, [sp, #16]
    ldr x1, [x0]
    add x0, x1, #8
    bl heap_alloc
    ldr x5, [sp, #16]
    ldr x2, [x5]
    str x2, [x0]
    add x6, x5, #8
    add x7, x0, #8
1:
    cbz x2, 3f
    ldrb w9, [x6], #1
    sub w10, w9, #97
    cmp w10, #25
    b.hi 2f
    sub w9, w9, #32
2:
    strb w9, [x7], #1
    sub x2, x2, #1
    b 1b
3:
    ldp x29, x30, [sp], #32
    ret
"""

RUTINA_STR_LOWER = """str_lower:
    # x0 = cadena -> x0 = nueva cadena con A-Z convertidas a a-z (solo ASCII)
    stp x29, x30, [sp, #-32]!
    mov x29, sp
    str x0, [sp, #16]
    ldr x1, [x0]
    add x0, x1, #8
    bl heap_alloc
    ldr x5, [sp, #16]
    ldr x2, [x5]
    str x2, [x0]
    add x6, x5, #8
    add x7, x0, #8
1:
    cbz x2, 3f
    ldrb w9, [x6], #1
    sub w10, w9, #65
    cmp w10, #25
    b.hi 2f
    add w9, w9, #32
2:
    strb w9, [x7], #1
    sub x2, x2, #1
    b 1b
3:
    ldp x29, x30, [sp], #32
    ret
"""

RUTINA_STR_CONTAINS = """str_contains:
    # x0 = cadena, x1 = subcadena -> x0 = 1 si la contiene, 0 si no
    ldr x2, [x0]
    ldr x3, [x1]
    add x4, x0, #8
    add x5, x1, #8
    cmp x3, x2
    b.hi 6f
    cbz x3, 5f
    sub x6, x2, x3
    mov x7, #0
1:
    mov x8, #0
2:
    cmp x8, x3
    b.hs 5f
    add x9, x7, x8
    ldrb w10, [x4, x9]
    ldrb w11, [x5, x8]
    cmp w10, w11
    b.ne 3f
    add x8, x8, #1
    b 2b
3:
    add x7, x7, #1
    cmp x7, x6
    b.ls 1b
6:
    mov x0, #0
    ret
5:
    mov x0, #1
    ret
"""

RUTINA_STR_REPLACE = """str_replace:
    # x0 = cadena, x1 = buscada, x2 = reemplazo -> x0 = nueva cadena
    # reemplaza todas las ocurrencias (de izquierda a derecha, sin solaparse);
    # si la buscada esta vacia devuelve una copia
    stp x29, x30, [sp, #-64]!
    mov x29, sp
    stp x0, x1, [sp, #16]
    str x2, [sp, #32]
    ldr x3, [x0]
    ldr x4, [x1]
    mov x9, #0
    cbz x4, 20f
    add x5, x0, #8
    add x6, x1, #8
    mov x7, #0
11:
    add x8, x7, x4
    cmp x8, x3
    b.hi 20f
    mov x10, #0
12:
    cmp x10, x4
    b.hs 13f
    add x11, x7, x10
    ldrb w12, [x5, x11]
    ldrb w13, [x6, x10]
    cmp w12, w13
    b.ne 14f
    add x10, x10, #1
    b 12b
13:
    add x9, x9, #1
    add x7, x7, x4
    b 11b
14:
    add x7, x7, #1
    b 11b
20:
    ldr x2, [sp, #32]
    ldr x10, [x2]
    sub x10, x10, x4
    mul x10, x9, x10
    add x10, x3, x10
    str x10, [sp, #40]
    add x0, x10, #8
    bl heap_alloc
    ldp x5, x6, [sp, #16]
    ldr x2, [sp, #32]
    ldr x10, [sp, #40]
    str x10, [x0]
    add x7, x0, #8
    ldr x3, [x5]
    ldr x4, [x6]
    ldr x15, [x2]
    add x5, x5, #8
    add x6, x6, #8
    add x2, x2, #8
    mov x8, #0
21:
    cmp x8, x3
    b.hs 30f
    cbz x4, 25f
    add x9, x8, x4
    cmp x9, x3
    b.hi 25f
    mov x10, #0
22:
    cmp x10, x4
    b.hs 23f
    add x11, x8, x10
    ldrb w12, [x5, x11]
    ldrb w13, [x6, x10]
    cmp w12, w13
    b.ne 25f
    add x10, x10, #1
    b 22b
23:
    mov x10, #0
24:
    cmp x10, x15
    b.hs 26f
    ldrb w12, [x2, x10]
    strb w12, [x7], #1
    add x10, x10, #1
    b 24b
26:
    add x8, x8, x4
    b 21b
25:
    ldrb w12, [x5, x8]
    strb w12, [x7], #1
    add x8, x8, #1
    b 21b
30:
    ldp x29, x30, [sp], #64
    ret
"""

RUTINA_RANDOM = """rt_random:
    # x0 = minimo, x1 = maximo -> x0 = entero aleatorio en [minimo, maximo]
    stp x29, x30, [sp, #-48]!
    mov x29, sp
    stp x0, x1, [sp, #16]
    add x0, sp, #32
    mov x1, #8
    mov x2, #0
    mov x8, #278
    svc #0
    ldr x3, [sp, #32]
    ldp x0, x1, [sp, #16]
    cmp x1, x0
    b.ge 1f
    mov x2, x0
    mov x0, x1
    mov x1, x2
1:
    sub x2, x1, x0
    add x2, x2, #1
    udiv x4, x3, x2
    msub x4, x4, x2, x3
    add x0, x0, x4
    sxtw x0, w0
    ldp x29, x30, [sp], #48
    ret
"""

# ---- tabla de rutinas: nombre -> texto, y sus dependencias ----
RUTINAS = {
    "print_int": RUTINA_PRINT_INT, "print_bool": RUTINA_PRINT_BOOL,
    "print_char": RUTINA_PRINT_CHAR, "print_f64": RUTINA_PRINT_F64,
    "print_string": RUTINA_PRINT_STRING, "heap_alloc": RUTINA_HEAP_ALLOC,
    "str_concat": RUTINA_STR_CONCAT, "str_repeat": RUTINA_STR_REPEAT,
    "str_cmp": RUTINA_STR_CMP, "str_upper": RUTINA_STR_UPPER,
    "str_lower": RUTINA_STR_LOWER, "str_contains": RUTINA_STR_CONTAINS,
    "str_replace": RUTINA_STR_REPLACE, "rt_random": RUTINA_RANDOM,
}
DEPENDENCIAS = {
    "heap_alloc": ["rt_memoria"],
    "str_concat": ["heap_alloc"], "str_repeat": ["heap_alloc"],
    "str_upper": ["heap_alloc"], "str_lower": ["heap_alloc"],
    "str_replace": ["heap_alloc"],
}
# rutinas que imprimen un mensaje y terminan con codigo 1
MENSAJES_ERROR = {
    "rt_div_cero": "Error de ejecución: división entre cero\n",
    "rt_indice": "Error de ejecución: índice fuera de los límites del arreglo\n",
    "rt_memoria": "Error de ejecución: memoria insuficiente\n",
}
ORDEN_RUTINAS = ["print_int", "print_bool", "print_char", "print_f64", "print_string",
                 "heap_alloc", "str_concat", "str_repeat", "str_cmp", "str_upper",
                 "str_lower", "str_contains", "str_replace", "rt_random",
                 "rt_div_cero", "rt_indice", "rt_memoria"]