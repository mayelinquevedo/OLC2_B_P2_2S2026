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
