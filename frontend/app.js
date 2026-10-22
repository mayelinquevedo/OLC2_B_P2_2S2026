/* OxigenNative - interfaz web.
   React se usa sin paso de compilacion: React, ReactDOM y htm estan en vendor/
   y las plantillas se escriben con html`...` (htm). Habla con la API (Flask):
       POST /api/compilar  { codigo }  ->  errores, simbolos, ast_svg, asm, salida, tiempo ... */

const { useState, useRef, useEffect } = React;
const html = htm.bind(React.createElement);

const CLAVE_CODIGO = "oxigen_codigo";
const CODIGO_EJEMPLO = `fn main() {
    let mut x: i32 = 10;
    let y: i32 = 20;

    if x < y {
        x = x + y;
    } else {
        x = x - y;
    }

    println!("{}", x);
}
`;

const NOMBRES_TIPO = { Lexico: "Léxico", Sintactico: "Sintáctico", Semantico: "Semántico",
                       Generacion: "Generación", Interno: "Interno" };
const nombreTipo = (t) => NOMBRES_TIPO[t] || t;

/* ---------- consola: convierte la respuesta de la API en lineas de texto ---------- */
function construirConsola(r) {
  const L = [{ t: "> Ejecutando OxigenNative...", c: "cmd" }];
  const errores = r.errores || [];
  if (r.fase === "solicitud") {
    L.push({ t: r.mensaje, c: "error" });
  } else if (!r.ok && r.fase === "analisis") {
    L.push({ t: `Se encontraron ${errores.length} error(es). Revise la pestaña Errores.`, c: "error" });
    errores.forEach((e) => {
      L.push({ t: `[Error ${nombreTipo(e.tipo)}] Línea ${e.linea}, Columna ${e.columna}`, c: "error" });
      L.push({ t: e.descripcion, c: "texto" });
      L.push({ t: "", c: "texto" });
    });
  } else if (!r.ok && r.fase === "generacion") {
    L.push({ t: "Compilación detenida: el generador aún no soporta esta construcción.", c: "error" });
    L.push({ t: r.mensaje, c: "texto" });
  } else if (!r.ok) {
    L.push({ t: `Error en la fase de ${r.fase}:`, c: "error" });
    L.push({ t: r.mensaje, c: "texto" });
  } else {
    if (errores.length > 0) {
      // recuperacion ante errores: se reportan, pero el resto del programa igual se ejecuta
      L.push({ t: `Se encontraron ${errores.length} error(es); se ejecutó el resto del programa.`, c: "error" });
      errores.forEach((e) => {
        L.push({ t: `[Error ${nombreTipo(e.tipo)}] Línea ${e.linea}, Columna ${e.columna}`, c: "error" });
        L.push({ t: e.descripcion, c: "texto" });
      });
    } else {
      L.push({ t: "Compilación exitosa.", c: "ok" });
    }
    L.push({ t: "── Programa en ejecución ──", c: "sep" });
    const salida = (r.salida || "").replace(/\n$/, "");
    if (r.salida) salida.split("\n").forEach((l) => L.push({ t: l, c: "salida" }));
    L.push({ t: "── Fin de la ejecución ──", c: "sep" });
    if (r.codigo_salida) L.push({ t: `El programa terminó con código de salida ${r.codigo_salida}.`, c: "error" });
    L.push({ t: `Tiempo de ejecución: ${r.tiempo.toFixed(4)}s`, c: "texto" });
  }
  return L;
}

/* ---------- editor con numeros de linea ---------- */
function Editor({ codigo, onCambio, errorLineas, refTA, onCursor }) {
  const refGutter = useRef(null);
  const total = codigo.split("\n").length;
  const numeros = [];
  for (let i = 1; i <= total; i++) {
    numeros.push(html`<div key=${i} className=${errorLineas.has(i) ? "num num-error" : "num"}>${i}</div>`);
  }
  // el margen de numeros se desplaza junto con el texto
  const sincronizar = (e) => { if (refGutter.current) refGutter.current.scrollTop = e.target.scrollTop; };
  const alPulsar = (e) => {
    if (e.key === "Tab") {            // Tab inserta 4 espacios en vez de cambiar de control
      e.preventDefault();
      const ta = e.target, ini = ta.selectionStart, fin = ta.selectionEnd;
      onCambio(codigo.slice(0, ini) + "    " + codigo.slice(fin));
      requestAnimationFrame(() => { ta.selectionStart = ta.selectionEnd = ini + 4; });
    }
  };
  const informarCursor = (e) => {
    const ta = e.target;
    const antes = ta.value.slice(0, ta.selectionStart).split("\n");
    onCursor({ linea: antes.length, col: antes[antes.length - 1].length + 1 });
  };
  return html`
    <div className="editor">
      <div className="gutter" ref=${refGutter}>${numeros}</div>
      <textarea ref=${refTA} value=${codigo} spellCheck=${false} wrap="off"
        placeholder="Escriba aquí su programa en OxigenNative..."
        onChange=${(e) => onCambio(e.target.value)} onScroll=${sincronizar}
        onKeyDown=${alPulsar} onKeyUp=${informarCursor} onClick=${informarCursor}></textarea>
    </div>`;
}

/* ---------- panel del codigo ARM64 ---------- */
function PanelAsm({ asm }) {
  const copiar = () => { if (navigator.clipboard) navigator.clipboard.writeText(asm); };
  const lineas = asm ? asm.replace(/\n$/, "").split("\n") : [];
  return html`
    <section className="panel" id="panel-asm">
      <header>
        <h2>Código ARM64 generado:</h2>
        ${asm ? html`<button className="mini" onClick=${copiar}>Copiar</button>` : null}
      </header>
      <div className="asm-cuerpo">
        ${asm
          ? html`<div className="asm">${lineas.map((l, i) => html`
              <div className="asm-linea" key=${i}>
                <span className="asm-num">${i + 1}</span>
                <span className=${/^\s*(#|\/\/)/.test(l) ? "asm-comentario" : ""}>${l}</span>
              </div>`)}</div>`
          : html`<p className="vacio">Aquí se mostrará el código ensamblador ARM64 generado por el compilador.</p>`}
      </div>
    </section>`;
}

/* ---------- consola de salida ---------- */
function Consola({ lineas, onLimpiar }) {
  const ref = useRef(null);
  useEffect(() => { if (ref.current) ref.current.scrollTop = ref.current.scrollHeight; }, [lineas]);
  return html`
    <section className="panel" id="panel-consola">
      <header>
        <h2>Consola de salida</h2>
        <button className="mini" onClick=${onLimpiar}>Limpiar</button>
      </header>
      <div className="consola" ref=${ref}>
        ${lineas.length === 0
          ? html`<div className="sep">Pulse «Ejecutar» (Ctrl+Enter) para compilar y correr el programa.</div>`
          : lineas.map((l, i) => html`<div key=${i} className=${l.c}>${l.t === "" ? " " : l.t}</div>`)}
      </div>
    </section>`;
}

/* ---------- reportes en pestanas ---------- */
function TablaErrores({ errores, onIr }) {
  return html`
    <table className="tabla" id="tabla-errores">
      <thead><tr><th>No</th><th>Tipo</th><th>Descripción</th><th>Línea</th><th>Columna</th><th>Fragmento</th></tr></thead>    
      <tbody>${errores.map((e, i) => html`
        <tr key=${i} className=${e.linea > 0 ? "clic" : ""} title="Ir a la línea" onClick=${() => e.linea > 0 && onIr(e.linea)}>
          <td>${i + 1}</td><td>${nombreTipo(e.tipo)}</td><td>${e.descripcion}</td><td>${e.linea}</td><td>${e.columna}</td><td><code>${e.fragmento || ""}</code></td>
        </tr>`)}</tbody>
    </table>`;
}

function TablaSimbolos({ simbolos }) {
  return html`
    <table className="tabla" id="tabla-simbolos">
      <thead><tr><th>No.</th><th>Identificador</th><th>Categoría</th><th>Tipo</th><th>Ámbito</th><th>Línea</th><th>Valor</th></tr></thead>
      <tbody>${simbolos.map((s, i) => html`
        <tr key=${i}>
          <td>${i + 1}</td><td>${s.nombre}</td><td>${s.categoria}</td><td>${s.tipo || "—"}</td>
          <td>${s.ambito}</td><td>${s.linea}</td><td>${s.valor}</td>
        </tr>`)}</tbody>
    </table>`;
}

// el SVG de Graphviz trae width/height en pt: se multiplican por el zoom
function escalarSvg(svg, z) {
  return svg.replace(/width="([\d.]+)pt"\s+height="([\d.]+)pt"/, (m, w, h) =>
    `width="${(parseFloat(w) * z).toFixed(1)}pt" height="${(parseFloat(h) * z).toFixed(1)}pt"`);
}

function VistaAST({ svg }) {
  const [zoom, setZoom] = useState(1);
  const cambiar = (d) => setZoom((z) => Math.min(3, Math.max(0.3, +(z + d).toFixed(2))));
  return html`
    <div id="vista-ast">
      <div className="herramientas">
        <button className="mini" onClick=${() => cambiar(-0.2)}>−</button>
        <span>${Math.round(zoom * 100)}%</span>
        <button className="mini" onClick=${() => cambiar(0.2)}>+</button>
        <button className="mini" onClick=${() => setZoom(1)}>100%</button>
      </div>
      <div className="ast-lienzo" dangerouslySetInnerHTML=${{ __html: escalarSvg(svg, zoom) }}></div>
    </div>`;
}

function PanelReportes({ resultado, vigente, pestana, onPestana, onIr }) {
  const errores = resultado ? resultado.errores : [];
  const vacio = (texto) => html`<p className="vacio">${texto}</p>`;
  let cuerpo;
  if (pestana === "errores") {
    cuerpo = !resultado ? vacio("Aquí se mostrarán los errores del programa.")
      : errores.length === 0 ? html`<p className="vacio bien">Sin errores.</p>`
      : html`<${TablaErrores} errores=${errores} onIr=${onIr} />`;
  } else if (pestana === "simbolos") {
    cuerpo = !resultado ? vacio("Aquí se mostrará la información de las variables y funciones.")
      : resultado.simbolos.length === 0 ? vacio("No se registraron símbolos.")
      : html`<${TablaSimbolos} simbolos=${resultado.simbolos} />`;
  } else {
    cuerpo = !resultado ? vacio("Aquí se mostrará el árbol de sintaxis abstracta del programa.")
      : !resultado.ast_svg ? vacio("No hay AST: el programa tiene errores que impidieron construirlo.")
      : html`<${VistaAST} svg=${resultado.ast_svg} />`;
  }
  const pestanas = [["errores", "Errores"], ["simbolos", "Tabla de símbolos"], ["ast", "AST"]];
  return html`
    <section className="panel" id="panel-reportes">
      <div className="pestanas">
        ${pestanas.map(([id, texto]) => html`
          <button key=${id} id=${"pestana-" + id} className=${pestana === id ? "pestana activa" : "pestana"} onClick=${() => onPestana(id)}>
            ${texto}${id === "errores" && errores.length > 0 ? html`<span className="insignia">${errores.length}</span>` : null}
          </button>`)}
      </div>
      <div className="cuerpo-pestana">${cuerpo}</div>
    </section>`;
}

/* ---------- aplicacion ---------- */
function leerCodigoGuardado() {
  try { const g = localStorage.getItem(CLAVE_CODIGO); if (g !== null) return g; } catch (e) { /* sin almacenamiento */ }
  return CODIGO_EJEMPLO;
}

function App() {
  const [codigo, setCodigo] = useState(leerCodigoGuardado);
  const [nombre, setNombre] = useState("programa.ox");
  const [resultado, setResultado] = useState(null);
  const [codigoEjecutado, setCodigoEjecutado] = useState(null);
  const [consola, setConsola] = useState([]);
  const [ejecutando, setEjecutando] = useState(false);
  const [pestana, setPestana] = useState("errores");
  const [cursor, setCursor] = useState({ linea: 1, col: 1 });
  const [menu, setMenu] = useState(false);
  const refTA = useRef(null);
  const refArchivo = useRef(null);
  const refEjecutar = useRef(null);

  // el codigo se guarda en el navegador para no perderlo al recargar
  useEffect(() => { try { localStorage.setItem(CLAVE_CODIGO, codigo); } catch (e) { /* ignorar */ } }, [codigo]);

  // el menu de reportes se cierra al hacer clic fuera
  useEffect(() => {
    const cerrar = (e) => { if (!e.target.closest || !e.target.closest(".menu-contenedor")) setMenu(false); };
    document.addEventListener("click", cerrar);
    return () => document.removeEventListener("click", cerrar);
  }, []);

  // atajo: Ctrl+Enter ejecuta
  useEffect(() => {
    const atajo = (e) => { if ((e.ctrlKey || e.metaKey) && e.key === "Enter") { e.preventDefault(); refEjecutar.current(); } };
    window.addEventListener("keydown", atajo);
    return () => window.removeEventListener("keydown", atajo);
  }, []);

  async function ejecutar() {
    if (ejecutando) return;
    setEjecutando(true);
    setConsola([{ t: "> Ejecutando OxigenNative...", c: "cmd" }]);
    try {
      const resp = await fetch("/api/compilar", {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ codigo }),
      });
      const datos = await resp.json();
      setResultado(datos);
      setCodigoEjecutado(codigo);
      setConsola(construirConsola(datos));
      if (datos.errores && datos.errores.length > 0) setPestana("errores");
    } catch (e) {
      setConsola([{ t: "> Ejecutando OxigenNative...", c: "cmd" },
                  { t: "No se pudo comunicar con el servidor.", c: "error" },
                  { t: "¿Está corriendo?  cd backend && python -m api.app", c: "texto" }]);
    } finally {
      setEjecutando(false);
    }
  }
  refEjecutar.current = ejecutar;

  function nuevo() {
    if (codigo.trim() !== "" && !window.confirm("¿Descartar el código actual y crear un archivo nuevo?")) return;
    setCodigo(""); setNombre("sin_titulo.ox"); setResultado(null); setCodigoEjecutado(null); setConsola([]);
  }
  function abrir() { refArchivo.current.click(); }
  async function alAbrir(e) {
    const archivo = e.target.files[0];
    if (!archivo) return;
    setCodigo(await archivo.text()); setNombre(archivo.name);
    setResultado(null); setCodigoEjecutado(null); setConsola([]);
    e.target.value = "";
  }
  function guardar() {
    const blob = new Blob([codigo], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = /\.(ox|rs|txt)$/.test(nombre) ? nombre : nombre + ".ox";
    document.body.appendChild(a); a.click(); a.remove();
    URL.revokeObjectURL(url);
  }
  function irALinea(n) {
    const ta = refTA.current;
    if (!ta || !n) return;
    const lineas = codigo.split("\n");
    let pos = 0;
    for (let i = 0; i < n - 1 && i < lineas.length; i++) pos += lineas[i].length + 1;
    ta.focus();
    ta.setSelectionRange(pos, pos + (lineas[n - 1] ? lineas[n - 1].length : 0));
    ta.scrollTop = Math.max(0, (n - 4) * 20);
  }

  // las lineas con error solo se marcan mientras el codigo no cambie
  const vigente = resultado && codigoEjecutado === codigo;
  const errorLineas = new Set(vigente ? (resultado.errores || []).filter((e) => e.linea > 0).map((e) => e.linea) : []);

  const paso = ejecutando ? 2 : !resultado ? 1 : (resultado.errores && resultado.errores.length > 0) ? 4 : 3;
  const pasos = ["", "", "", ""];

  const enlace = (archivo, texto, activo, descargar) => activo
    ? html`<a href=${"/api/reportes/" + archivo + (descargar ? "?descargar=1" : "")} target=${descargar ? "_self" : "_blank"} rel="noopener">${texto}</a>`
    : html`<span>${texto}</span>`;

  return html`
    <div className="app">
      <header className="barra">
        <div className="marca">
          <div className="logo">Ox</div>
          <div><div className="titulo">OxigenNative</div><div className="subtitulo">Compilador inspirado en Rust · genera ARM64</div></div>
        </div>
        <div className="acciones">
          <button id="btn-nuevo" onClick=${nuevo}>Nuevo</button>
          <button id="btn-abrir" onClick=${abrir}>Abrir</button>
          <button id="btn-guardar" onClick=${guardar}>Guardar</button>
          <button id="btn-ejecutar" className="primario" disabled=${ejecutando} onClick=${ejecutar}>${ejecutando ? "Ejecutando..." : "Ejecutar"}</button>
          <div className="menu-contenedor">
            <button id="btn-reportes" onClick=${() => setMenu(!menu)}>Reportes ▾</button>
            ${menu ? html`
              <div className="menu" id="menu-reportes">
                ${enlace("errores.html", "Reporte de errores (HTML)", !!resultado)}
                ${enlace("simbolos.html", "Tabla de símbolos (HTML)", !!resultado)}
                ${enlace("ast.svg", "Árbol de sintaxis (SVG)", !!(resultado && resultado.ast_svg))}
                ${enlace("ast.dot", "Árbol de sintaxis (DOT)", !!(resultado && resultado.ast_svg), true)}
              </div>` : null}
          </div>
          <input type="file" accept=".ox,.rs,.txt" ref=${refArchivo} style=${{ display: "none" }} onChange=${alAbrir} />
        </div>
      </header>

      <main className="rejilla">
        <section className="panel" id="panel-editor">
          <header><h2>${nombre}</h2><span className="estado">Línea ${cursor.linea}, Columna ${cursor.col}</span></header>
          <${Editor} codigo=${codigo} onCambio=${setCodigo} errorLineas=${errorLineas} refTA=${refTA} onCursor=${setCursor} />
        </section>
        <${PanelAsm} asm=${resultado ? resultado.asm : null} />
        <${Consola} lineas=${consola} onLimpiar=${() => setConsola([])} />
        <${PanelReportes} resultado=${resultado} vigente=${vigente} pestana=${pestana} onPestana=${setPestana} onIr=${irALinea} />
      </main>

      <footer className="pasos">
        ${pasos.map((texto, i) => html`
          <span key=${i} style=${{ display: "contents" }}>
            <span className=${paso === i + 1 ? "paso activo" : "paso"}><span className="n">${i + 1}</span>${texto}</span>
            ${i < pasos.length - 1 ? html`<span className="flecha">→</span>` : null}
          </span>`)}
      </footer>
    </div>`;
}

ReactDOM.createRoot(document.getElementById("raiz")).render(html`<${App} />`);
