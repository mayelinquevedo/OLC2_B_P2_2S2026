# OxigenNative

Ingeniería en Ciencias y Sistemas
Universidad de SAN CARLOS DE GUATEMALA
CURSO: Organizacion de lenguajes y compiladores 2
seccion: B

Nombre: Mayelin Lucía Quevedo Camey
carnet: 202307771

Compilador de un lenguaje académico de sintaxis inspirada en **Rust** que genera **ensamblador ARM64 (AArch64)**





Si el código tiene errores léxicos, sintácticos o semánticos, el compilador **los reporta y sigue**
ejecutando el resto del programa (una expresión inválida vale `None`); solo se detiene en errores críticos
(por ejemplo, no hay `main`).

## Requisitos (Linux / WSL Ubuntu)

```bash
sudo apt update
sudo apt install -y python3 python3-venv graphviz qemu-user binutils-aarch64-linux-gnu
```

## Instalación y ejecución

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m api.app            # servidor en http://127.0.0.1:5000
```

Abra **http://127.0.0.1:5000** en el navegador (el servidor también sirve el frontend).

## Estructura

```
backend/
  api/app.py                  API REST (Flask): /api/compilar, /api/reportes/<nombre>
  compiler/
    lexer/lexer.py            análisis léxico (PLY lex)
    parser/parser.py          gramática y construcción del AST (PLY yacc)
    ast/nodos.py              nodos del AST (clases propias)
    semantic/                 analizador semántico y tabla de símbolos
    codegen/generador.py      Visitor que traduce el AST directo a ARM64
    codegen/rutinas.py        rutinas de runtime en ensamblador (print, strings, heap, ...)
    formato.py                interpretación de la cadena de formato de println!
    recuperacion.py           saneamiento del AST: seguir ejecutando tras errores
    reportes.py               reportes HTML y AST en Graphviz
    pipeline.py               orquesta todas las fases
  runtime/ejecutor.py         as → ld → qemu-aarch64
  tests_dev/                  pruebas automáticas
frontend/                     interfaz web (HTML/CSS/JS + React sin compilación)
tests/                        programas .ox de ejemplo y casos por fase
docs/                         documentación técnica, manual de usuario y diagramas
```

## Pruebas

```bash
cd backend
python3 -m tests_dev.correr_todos      # pruebas unitarias por fase
python3 -m tests_dev.correr_ejemplos   # 41 programas de tests/ejemplos (errores y salida) contra su .esperado
```

## Documentación

- [Manual Técnico](docs/Manual_Tecnico.md): gramática, generación de código, decisiones de diseño.
- [Manual de usuario](docs/manual_usuario.md): instalación, uso del editor, lectura de reportes.