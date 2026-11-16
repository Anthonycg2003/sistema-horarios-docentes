# -*- coding: utf-8 -*-
"""Diseño teóricamente correcto: genera los fragmentos LaTeX de la sección 4.

Parte del universo U y del conjunto F que da el diseño intuitivo del MERX y
calcula:
  - el cubrimiento minimal G,
  - la descomposición en 3FN con PPDF (algoritmo de síntesis),
  - las llaves de R(U, G),
  - la comprobación de la PLJ con el algoritmo de la matriz.

Uso:
    python verificacion.py    # escribe ../../secciones/generado/*.tex
"""

from itertools import combinations
from pathlib import Path

OUT = Path(__file__).resolve().parents[2] / "secciones" / "generado"

# Universo de atributos: (nombre, significado). El orden es el de la matriz.
UNIVERSO = [
    ("#P", "identificador del programa académico"),
    ("NombreP", "nombre del programa"),
    ("Plan", "plan de estudios del programa"),
    ("#A", "identificador de la asignatura"),
    ("NombreA", "nombre de la asignatura"),
    ("#C", "identificador del coordinador académico"),
    ("NombreC", "nombre del coordinador"),
    ("Especialidad", "especialidad del coordinador"),
    ("PGenerar", "el coordinador puede generar horarios en el programa"),
    ("PValidar", "el coordinador puede validar horarios en el programa"),
    ("#E", "identificador del estudiante"),
    ("NombreE", "nombre del estudiante"),
    ("Edad", "edad del estudiante"),
    ("Grupo", "grupo al que pertenece el estudiante"),
    ("#J", "identificador del jefe de departamento"),
    ("NombreJ", "nombre del jefe de departamento"),
    ("#B", "identificador del bloque de contenido"),
    ("Descripcion", "descripción del contenido del bloque"),
    ("Tipo", "tipo de actividad del bloque"),
    ("Complejidad", "nivel de complejidad del bloque"),
    ("#CCrea", "coordinador que creó el bloque"),
    ("#S", "identificador del semestre"),
    ("FInicio", "fecha de inicio del semestre"),
    ("FFin", "fecha de fin del semestre"),
    ("#H", "identificador del horario"),
    ("FCreacion", "fecha de creación del horario"),
    ("PTeorica", "proporción de bloques teóricos pedida"),
    ("PPractica", "proporción de bloques prácticos pedida"),
    ("PLaboratorio", "proporción de bloques de laboratorio pedida"),
    ("Cobertura", "cobertura mínima de asignaturas pedida"),
    ("Cantidad", "cantidad total de bloques pedida"),
    ("#CGen", "coordinador que generó el horario"),
    ("#HAnt", "horario al que sustituye el horario"),
    ("#CVal", "coordinador que validó el horario"),
    ("FValidacion", "fecha de la validación"),
    ("ObsV", "observaciones de la validación"),
    ("FRevision", "fecha de la revisión del jefe"),
    ("Decision", "decisión de la revisión"),
    ("ObsR", "observaciones de la revisión"),
    ("#Au", "identificador del aula"),
    ("Edificio", "edificio del aula"),
    ("Capacidad", "capacidad del aula"),
    ("#F", "identificador de la franja horaria"),
    ("Dia", "día de la semana de la franja"),
    ("HInicio", "hora de inicio de la franja"),
    ("HFin", "hora de fin de la franja"),
    ("Fecha", "día lectivo en que se imparte la sesión"),
    ("EstadoA", "presente o ausente"),
    ("#Sol", "identificador de la solicitud de cambio"),
    ("Motivo", "motivo de la solicitud"),
    ("FSolicitud", "fecha de la solicitud"),
    ("EstadoS", "estado de la solicitud"),
    ("FResolucion", "fecha de resolución de la solicitud"),
    ("#HOri", "horario de origen de la solicitud"),
    ("#HDes", "horario de destino de la solicitud"),
    ("#CAt", "coordinador que atiende la solicitud"),
    ("#CApo", "coordinador de apoyo de la solicitud"),
]
U = [a for a, _ in UNIVERSO]
ATRIBUTOS = set(U)


def fd(lhs, rhs, origen, paso):
    return (tuple(lhs.split()), tuple(rhs.split()), origen, paso)


PASOS = {
    1: "Paso 1. Conjuntos de entidades",
    2: "Paso 2. Interrelaciones uno a muchos",
    3: "Paso 3. Interrelaciones uno a uno",
    4: "Paso 4. Interrelaciones muchos a muchos",
    5: "Paso 5. Agregaciones",
    6: "Paso 6. Restricciones del sistema (sección~\\ref{sec:restricciones})",
}

# F según el diseño intuitivo, en el orden de sus pasos.
F = [
    fd("#P", "NombreP Plan", "PROGRAMA ACADÉMICO", 1),
    fd("#A", "NombreA", "ASIGNATURA", 1),
    fd("#C", "NombreC Especialidad", "COORDINADOR ACADÉMICO", 1),
    fd("#E", "NombreE Edad Grupo", "ESTUDIANTE", 1),
    fd("#J", "NombreJ", "JEFE DE DEPARTAMENTO", 1),
    fd("#B", "Descripcion Tipo Complejidad", "BLOQUE DE CONTENIDO", 1),
    fd("#S", "FInicio FFin", "SEMESTRE", 1),
    fd("#H", "FCreacion PTeorica PPractica PLaboratorio Cobertura Cantidad", "HORARIO", 1),
    fd("#Au", "Edificio Capacidad", "AULA", 1),
    fd("#F", "Dia HInicio HFin", "FRANJA HORARIA", 1),
    fd("Fecha", "Fecha", "FECHA", 1),
    fd("#Sol", "Motivo FSolicitud EstadoS FResolucion", "SOLICITUD DE CAMBIO", 1),
    fd("#B", "#CCrea", "CREAR", 2),
    fd("#B", "#A", "ABORDAR", 2),
    fd("#H", "#CGen", "GENERAR", 2),
    fd("#H", "#P", "PERTENECER", 2),
    fd("#H", "#S", "CORRESPONDER", 2),
    fd("#H", "#CVal", "VALIDAR", 2),
    fd("#H", "#J", "REVISAR", 2),
    fd("#H #B", "Fecha", "PROGRAMAR", 2),
    fd("#H #B Fecha", "#F", "OCUPAR", 2),
    fd("#H #B Fecha", "#Au", "UTILIZAR", 2),
    fd("#Sol", "#E", "SOLICITAR", 2),
    fd("#Sol", "#HOri", "ORIGEN", 2),
    fd("#Sol", "#HDes", "DESTINO", 2),
    fd("#Sol", "#CAt", "ATENDER", 2),
    fd("#Sol", "#CApo", "APOYAR", 2),
    fd("#H", "#HAnt", "SUSTITUIR", 3),
    fd("#C #P", "#C #P", "AUTORIZAR", 4),
    fd("#E #P", "#E #P", "MATRICULAR", 4),
    fd("#E #H", "#E #H", "ASIGNAR", 4),
    fd("#E #H #B Fecha", "#E #H #B Fecha", "ASISTIR", 4),
    fd("#C #P", "PGenerar PValidar", "AUTORIZACIÓN", 5),
    fd("#CVal #H", "FValidacion ObsV", "VALIDACIÓN", 5),
    fd("#J #H", "FRevision Decision ObsR", "REVISIÓN", 5),
    fd("#E #H #B Fecha", "EstadoA", "ASISTENCIA", 5),
    fd("Descripcion #A Tipo", "#B", "RN-03", 6),
    fd("Dia HInicio", "#F", "RN-04", 6),
    fd("Dia HFin", "#F", "RN-04", 6),
    fd("FInicio", "#S", "RN-05", 6),
    fd("FFin", "#S", "RN-05", 6),
    fd("#H Fecha #F", "#B", "RN-09", 6),
    fd("#HAnt", "#H", "RN-12", 6),
]

# Dependencias propias K -> K que se conservan en el cubrimiento minimal: las
# de interrelaciones sin atributos, que no tienen otra dependencia que las
# represente. Las demás se eliminan.
PROPIAS_CONSERVADAS = {"MATRICULAR", "ASIGNAR"}

# Nombre de cada esquema de la descomposición según su determinante, en el
# orden en que se presentan.
NOMBRES = {
    ("#P",): "Programa",
    ("#A",): "Asignatura",
    ("#C",): "Coordinador",
    ("#C", "#P"): "Autorización",
    ("#E",): "Estudiante",
    ("#E", "#P"): "Matrícula",
    ("#J",): "Jefe",
    ("#B",): "Bloque",
    ("#S",): "Semestre",
    ("#H",): "Horario",
    ("#Au",): "Aula",
    ("#F",): "Franja",
    ("#H", "#B"): "Sesión",
    ("#E", "#H"): "Asignación",
    ("#E", "#H", "#B"): "Asistencia",
    ("#Sol",): "Solicitud",
}

# Llaves foráneas que representan un rol: atributo -> (relación, atributo).
ROLES = {
    "#CCrea": ("Coordinador", "#C"),
    "#CGen": ("Coordinador", "#C"),
    "#CVal": ("Coordinador", "#C"),
    "#CAt": ("Coordinador", "#C"),
    "#CApo": ("Coordinador", "#C"),
    "#HAnt": ("Horario", "#H"),
    "#HOri": ("Horario", "#H"),
    "#HDes": ("Horario", "#H"),
}


# --- Teoría -----------------------------------------------------------------

def clausura(x, deps):
    z = set(x)
    cambio = True
    while cambio:
        cambio = False
        for lhs, rhs in deps:
            if set(lhs) <= z and not set(rhs) <= z:
                z |= set(rhs)
                cambio = True
    return z


def es_propia(d):
    return set(d[0]) == set(d[1])


def cubrimiento_minimal(deps):
    """Devuelve (eliminadas, conservadas, paso2, extranos, paso3, redundantes, G).

    G no incluye las propias conservadas: no intervienen en ninguna clausura.
    """
    eliminadas = [d for d in deps if es_propia(d) and d[2] not in PROPIAS_CONSERVADAS]
    conservadas = [d for d in deps if es_propia(d) and d[2] in PROPIAS_CONSERVADAS]
    paso2 = []
    for l, r, *_ in deps:
        if set(l) == set(r):
            continue
        for a in r:
            if (l, (a,)) not in paso2:
                paso2.append((l, (a,)))
    extranos = []
    paso3 = []
    for l, r in paso2:
        lhs = list(l)
        for a in list(l):
            if len(lhs) == 1:
                break
            resto = [b for b in lhs if b != a]
            if r[0] in clausura(resto, paso2):
                extranos.append((l, r, a))
                lhs = resto
        if (tuple(lhs), r) not in paso3:
            paso3.append((tuple(lhs), r))
    redundantes = []
    g = list(paso3)
    for d in list(paso3):
        otras = [e for e in g if e != d]
        if d[1][0] in clausura(d[0], otras):
            redundantes.append(d)
            g = otras
    return eliminadas, conservadas, paso2, extranos, paso3, redundantes, g


def agrupar(g):
    orden = []
    grupos = {}
    for l, r in g:
        if l not in grupos:
            grupos[l] = []
            orden.append(l)
        grupos[l] += [a for a in r if a not in grupos[l]]
    return [(l, tuple(a for a in U if a in grupos[l])) for l in orden]


def sintesis(g, conservadas):
    """Algoritmo de descomposición en 3FN con PPDF.

    Devuelve (traza, sueltos, rho). traza: (X, Ui, esquema que lo contiene o
    None). rho: lista de (nombre, llave, Ui) en el orden de NOMBRES.
    """
    grupos = agrupar(g) + [(l, ()) for l, *_ in conservadas]
    candidatos = []
    for l, r in grupos:
        ui = [a for a in U if a in set(l) | set(r)]
        candidatos.append((l, ui))
    sueltos = [a for a in U if not any(a in ui for _, ui in candidatos)]
    # el esquema de una propia conservada no se absorbe: representa por sí solo
    # la interrelación (una asignación existe aunque no haya asistencia)
    propias = {l for l, *_ in conservadas}
    traza = []
    rho = []
    for l, ui in candidatos:
        contenedor = None
        for l2, ui2 in candidatos:
            if l not in propias and l2 != l and set(ui) < set(ui2):
                contenedor = l2
                break
        traza.append((l, ui, contenedor))
        if contenedor is None:
            rho.append((NOMBRES[l], l, ui))
    orden = list(NOMBRES.values())
    rho.sort(key=lambda e: orden.index(e[0]))
    return traza, sueltos, rho


def llaves(universo, deps, maximo=None):
    solo_izq, solo_der, ambos, ninguno = [], [], [], []
    izq = {a for l, _ in deps for a in l}
    der = {a for _, r in deps for a in r}
    for a in universo:
        if a in izq and a in der:
            ambos.append(a)
        elif a in izq:
            solo_izq.append(a)
        elif a in der:
            solo_der.append(a)
        else:
            ninguno.append(a)
    base = solo_izq + ninguno
    encontradas = []
    tope = len(ambos) if maximo is None else min(maximo, len(ambos))
    for k in range(0, tope + 1):
        for extra in combinations(ambos, k):
            cand = base + list(extra)
            if any(set(e) <= set(cand) for e in encontradas):
                continue
            if clausura(cand, deps) >= set(universo):
                encontradas.append(cand)
    return solo_izq, solo_der, ambos, ninguno, encontradas


def llaves_de(ui, deps, maximo=4):
    res = []
    for k in range(1, min(maximo, len(ui)) + 1):
        for x in combinations(ui, k):
            if any(set(y) <= set(x) for y in res):
                continue
            if clausura(x, deps) >= set(ui):
                res.append(x)
    return res


def en_3fn(ui, deps):
    """Comprueba la 3FN de Ui con las dependencias X -> A de G contenidas en Ui."""
    ks = llaves_de(ui, deps)
    primos = {a for k in ks for a in k}
    for x, (a,) in deps:
        if set(x) | {a} <= set(ui) and a not in x:
            if not clausura(x, deps) >= set(ui) and a not in primos:
                return False
    return True


def plj(deps, rho, universo):
    """Algoritmo de la matriz. Devuelve matriz inicial, final, pasos y filas de a."""
    filas = [[("a", j) if a in ui else ("b", i, j) for j, a in enumerate(universo)]
             for i, (_, ui) in enumerate(rho)]
    inicial = [list(f) for f in filas]
    col = {a: j for j, a in enumerate(universo)}
    pasos = []
    cambio = True
    pasada = 0
    while cambio:
        cambio = False
        pasada += 1
        for lhs, rhs in deps:
            grupos = {}
            for i, f in enumerate(filas):
                clave = tuple(f[col[a]] for a in lhs)
                grupos.setdefault(clave, []).append(i)
            for idx in grupos.values():
                if len(idx) < 2:
                    continue
                for a in rhs:
                    j = col[a]
                    simbolos = {filas[i][j] for i in idx}
                    if len(simbolos) == 1:
                        continue
                    meta = ("a", j) if ("a", j) in simbolos else min(simbolos)
                    for i in idx:
                        if filas[i][j] != meta:
                            if meta[0] == "a":
                                pasos.append((pasada, lhs, a, rho[i][0]))
                            filas[i][j] = meta
                    cambio = True
        if any(all(s[0] == "a" for s in f) for f in filas):
            break
    llenas = [rho[i][0] for i, f in enumerate(filas) if all(s[0] == "a" for s in f)]
    return inicial, filas, pasos, llenas


def llaves_foraneas(nombre_r, ui, rho):
    """Llaves foráneas de Ui: llaves primarias de otros esquemas y roles."""
    refs = []
    for n2, k2, _ in rho:
        if n2 != nombre_r and set(k2) <= set(ui):
            refs.append((k2, n2, None))
    # se omite la referencia a K si otra referencia la contiene (#H en (#H, #B))
    refs = [r for r in refs
            if not any(set(r[0]) < set(o[0]) for o in refs)]
    for a in ui:
        if a in ROLES:
            refs.append(((a,), ROLES[a][0], ROLES[a][1]))
    return refs


# --- LaTeX ------------------------------------------------------------------

def t(a):
    return a.replace("#", r"\#")


def conj(attrs):
    return ", ".join(t(a) for a in attrs)


def llave(attrs):
    return "\\{" + conj(attrs) + "\\}"


def dep(lhs, rhs):
    return f"{conj(lhs)} \\ensuremath{{\\to}} {conj(rhs)}"


def escribir(nombre_archivo, texto):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / nombre_archivo).write_text(
        "% Generado por assets/source/verificacion.py. No editar a mano.\n" + texto,
        encoding="utf-8",
    )


def tex_universo():
    filas = []
    mitad = (len(UNIVERSO) + 1) // 2
    izq, der = UNIVERSO[:mitad], UNIVERSO[mitad:]
    for k in range(mitad):
        a, s = izq[k]
        celdas = [t(a), s]
        if k < len(der):
            b, s2 = der[k]
            celdas += [t(b), s2]
        else:
            celdas += ["", ""]
        filas.append(" & ".join(celdas) + r" \\")
    return (
        "{\\footnotesize\\filas\n"
        "\\begin{xltabular}{\\linewidth}{>{\\bfseries}l L{1}>{\\bfseries}l L{1}}\n"
        "\\rowcolor{azul}\\cab{Atributo} & \\cab{Significado} & \\cab{Atributo} & \\cab{Significado} \\\\\n"
        "\\endhead\n" + "\n".join(filas) + "\n\\end{xltabular}}\n"
    )


def etiqueta(origen, k):
    return f"df:{origen}-{k}"


def tex_dependencias():
    out = []
    n = 1
    contador = {}
    for paso, titulo in PASOS.items():
        deps = [d for d in F if d[3] == paso]
        out.append(f"\\textbf{{{titulo}}}\n\\begin{{enumerate}}[label=f\\arabic*,start={n},leftmargin=3em]")
        for lhs, rhs, origen, _ in deps:
            et = ""
            if paso == 6:
                contador[origen] = contador.get(origen, 0) + 1
                et = f"\\label{{{etiqueta(origen, contador[origen])}}}"
            out.append(f"  \\item{et} {dep(lhs, rhs)} \\hfill {{\\small\\color{{gris}}{origen}}}")
            n += 1
        out.append("\\end{enumerate}")
    return "\n".join(out) + "\n"


def numero(d):
    return f"f{F.index(d) + 1}"


def tex_cubrimiento(eliminadas, conservadas, paso2, extranos, paso3, redundantes, g):
    out = []
    out.append(
        "\\textbf{Paso 1. Dependencias propias.} Se eliminan "
        + "; ".join(f"{dep(d[0], d[1])} ({numero(d)}, {d[2]})" for d in eliminadas)
        + ". Se conservan "
        + " y ".join(f"{dep(d[0], d[1])} ({numero(d)}, {d[2]})" for d in conservadas)
        + ".\n"
    )
    simples = sum(1 for d in F if not es_propia(d))
    out.append(
        f"\\textbf{{Paso 2. Partes derechas simples.}} Las {simples} dependencias restantes "
        f"se descomponen en {len(paso2)} dependencias de la forma $X \\to A$ ($F'$).\n"
    )
    compuestas = [(l, r) for l, r in paso2 if len(l) > 1]
    filas = []
    for l, r in compuestas:
        detalle = []
        for a in l:
            resto = [b for b in l if b != a]
            cl = clausura(resto, paso2)
            veredicto = "sí" if r[0] in cl else "no"
            detalle.append(f"{llave(resto)}$^+ \\ni$ {t(r[0])}: {veredicto}")
        filas.append(f"{dep(l, r)} & " + "; ".join(detalle) + r" \\")
    out.append(
        "\\textbf{Paso 3. Atributos redundantes.} Para cada $B \\in X$ se comprueba si "
        "$A \\in (X - B)^+_{F'}$:\n\n"
        "{\\footnotesize\\filas\n\\begin{xltabular}{\\linewidth}{L{0.7}L{1.3}}\n"
        "\\rowcolor{azul}\\cab{Dependencia} & \\cab{Comprobación} \\\\\n\\endhead\n"
        + "\n".join(filas) + "\n\\end{xltabular}}\n"
    )
    if extranos:
        por_atributo = {}
        for l, r, a in extranos:
            por_atributo.setdefault((l, a), []).append(r[0])
        items = "; ".join(
            f"{t(a)} en {dep(l, rs)}" for (l, a), rs in por_atributo.items()
        )
        out.append(f"Son redundantes: {items}. Se obtiene $F''$, con {len(paso3)} dependencias.\n")
    else:
        out.append("No hay atributos redundantes: $F'' = F'$.\n")
    fuentes = {}
    for l, r in paso3:
        fuentes.setdefault(r[0], []).append((l, r))
    unicas = sum(1 for v in fuentes.values() if len(v) == 1)
    filas3 = []
    for a in U:
        for l, r in fuentes.get(a, []):
            if len(fuentes[a]) < 2:
                continue
            otras = [e for e in paso3 if e != (l, r)]
            cl = clausura(l, otras)
            filas3.append(
                f"{dep(l, r)} & {conj([b for b in U if b in cl])} & "
                f"{'sí' if a in cl else 'no'} \\\\"
            )
    out.append(
        f"\n\\textbf{{Paso 4. Dependencias redundantes.}} {unicas} de los {len(fuentes)} atributos "
        "de la derecha tienen una sola dependencia, que no puede ser redundante. Para el resto "
        "se calcula $X^+$ con $F'' - \\{X \\to A\\}$:\n\n"
        "{\\footnotesize\\filas\n\\begin{xltabular}{\\linewidth}{L{0.55}L{1.3}>{\\centering\\arraybackslash}p{16mm}}\n"
        "\\rowcolor{azul}\\cab{$X \\to A$} & \\cab{$X^+$ sin $X \\to A$} & \\cab{¿$A \\in X^+$?} \\\\\n\\endhead\n"
        + "\n".join(filas3) + "\n\\end{xltabular}}\n"
    )
    if redundantes:
        items = "; ".join(dep(l, r) for l, r in redundantes)
        out.append(f"Son redundantes: {items}.\n")
    else:
        out.append("Ninguna es redundante.\n")
    agrupadas = agrupar(g) + [(l, r) for l, r, *_ in conservadas]
    out.append(
        f"\nEl cubrimiento minimal $G$ tiene {len(g)} dependencias de la forma $X \\to A$ y las "
        f"{len(conservadas)} propias conservadas. Agrupadas por determinante:\n"
        "\\begin{enumerate}[label=g\\arabic*,leftmargin=3em]\n"
        + "\n".join(f"  \\item {dep(l, r)}" for l, r in agrupadas)
        + "\n\\end{enumerate}\n"
    )
    return "\n".join(out)


def tex_sintesis(traza, rho):
    filas = []
    for l, ui, contenedor in traza:
        destino = f"contenido en {NOMBRES[contenedor]}" if contenedor else NOMBRES[l]
        orden = list(l) + [a for a in ui if a not in l]
        filas.append(f"{conj(l)} & {conj(orden)} & {destino} \\\\")
    return (
        "{\\footnotesize\\filas\n"
        "\\begin{xltabular}{\\linewidth}{L{0.5}L{1.75}L{0.75}}\n"
        "\\rowcolor{azul}\\cab{Determinante $X$} & \\cab{Esquema $X \\cup Y$} & \\cab{Resultado} \\\\\n"
        "\\endhead\n" + "\n".join(filas) + "\n\\end{xltabular}}\n"
    )


def tex_esquemas(rho, g):
    filas = []
    for n, k, ui in rho:
        resto = [a for a in ui if a not in k]
        esquema = "(\\underline{" + conj(k) + "}" + (", " + conj(resto) if resto else "") + ")"
        otras = [x for x in llaves_de(ui, g) if set(x) != set(k)]
        otras_txt = "; ".join("(" + conj(x) + ")" if len(x) > 1 else conj(x) for x in otras) or "---"
        fks = []
        for ref, destino, col in llaves_foraneas(n, ui, rho):
            izq = conj(ref) if len(ref) == 1 else "(" + conj(ref) + ")"
            der = f"{destino}({t(col)})" if col else destino
            fks.append(f"{izq} \\ensuremath{{\\to}} {der}")
        filas.append(f"{n} & {esquema} & {otras_txt} & {'; '.join(fks) or '---'} \\\\")
    return (
        "{\\footnotesize\\filas\n"
        "\\begin{xltabular}{\\linewidth}{L{0.45}L{1.45}L{0.5}L{1.1}}\n"
        "\\rowcolor{azul}\\cab{Relación} & \\cab{Esquema} & \\cab{Otras llaves} & \\cab{Llaves foráneas} \\\\\n"
        "\\endhead\n" + "\n".join(filas) + "\n\\end{xltabular}}\n"
    )


def traza_clausura(x, deps):
    z = set(x)
    pasos = []
    while True:
        nuevo = set(z)
        for l, r in deps:
            if set(l) <= z:
                nuevo |= set(r)
        if nuevo == z:
            return pasos
        pasos.append(nuevo - z)
        z = nuevo


def tex_llaves(g):
    si, sd, am, ni, ks = llaves(U, g)
    base = si + ni
    cl = clausura(base, g)
    clasif = (
        "\\begin{itemize}\n"
        f"  \\item solo a la izquierda ($L$): {conj(si)};\n"
        f"  \\item a ambos lados ($M$): {conj(am)};\n"
        f"  \\item solo a la derecha ($D$): los {len(sd)} restantes;\n"
        f"  \\item en ninguna dependencia: {conj(ni) if ni else 'ninguno'}.\n"
        "\\end{itemize}\n"
    )
    faltan = [a for a in U if a not in cl]
    base_txt = (
        f"$L^+ =$ {llave(base)}$^+$ contiene {len(cl)} de los {len(U)} atributos. "
        f"Faltan: {conj(faltan)}.\n"
    )
    lista = (
        "\\begin{enumerate}[label=K\\arabic*,leftmargin=3em,itemsep=0pt]\n"
        + "\n".join(f"  \\item \\{{{conj(k)}\\}}" for k in ks)
        + "\n\\end{enumerate}\n"
    )
    k1 = ks[0]
    pasos = traza_clausura(k1, g)
    filas = []
    for i, nuevos in enumerate(pasos, 1):
        filas.append(f"$X_{{{i}}}$ & {conj([a for a in U if a in nuevos])} \\\\")
    traza = (
        "{\\footnotesize\\filas\n\\begin{xltabular}{\\linewidth}{l L{1}}\n"
        "\\rowcolor{azul}\\cab{Iteración} & \\cab{Atributos que se añaden} \\\\\n\\endhead\n"
        f"$X_0$ & {conj(k1)} \\\\\n" + "\n".join(filas) + "\n\\end{xltabular}}\n"
    )
    minimal = []
    for a in k1:
        resto = [b for b in k1 if b != a]
        falta = [b for b in U if b not in clausura(resto, g)]
        minimal.append(f"sin {t(a)} falta {conj(falta[:3])}{'…' if len(falta) > 3 else ''}")
    minimal_txt = "; ".join(minimal) + ".\n"
    escribir("llaves-clasificacion.tex", clasif)
    escribir("llaves-base.tex", base_txt)
    escribir("llaves-lista.tex", lista)
    escribir("llaves-traza.tex", traza)
    escribir("llaves-minimal.tex", minimal_txt)
    return ks


def tex_plj(g, rho2):
    _, final, pasos, llenas = plj(agrupar(g), rho2, U)
    grupos = []
    for pasada, lhs, a, fila in pasos:
        if fila != "Llave":
            continue
        if grupos and grupos[-1][0] == pasada and grupos[-1][1] == lhs:
            grupos[-1][2].append(a)
        else:
            grupos.append((pasada, lhs, [a]))
    filas = [
        f"{p} & {conj(lhs)} \\ensuremath{{\\to}} & {conj(attrs)} \\\\"
        for p, lhs, attrs in grupos
    ]
    return (
        "{\\footnotesize\\filas\n\\begin{xltabular}{\\linewidth}{c L{0.7}L{1.3}}\n"
        "\\rowcolor{azul}\\cab{Pasada} & \\cab{Dependencia aplicada} & "
        "\\cab{Columnas en que la fila Llave pasa de $b$ a $a$} \\\\\n\\endhead\n"
        + "\n".join(filas) + "\n\\end{xltabular}}\n"
    ), llenas


def tex_matriz(inicial, final, rho2):
    nombres = [n for n, _ in rho2]
    cols = "l" + "c" * len(rho2)
    cab = " & ".join(
        f"\\rotatebox{{90}}{{\\cab{{{n}}}}}" for n in nombres
    )
    filas = []
    for j, a in enumerate(U):
        celdas = []
        for i in range(len(rho2)):
            ini, fin = inicial[i][j], final[i][j]
            if ini[0] == "a":
                celdas.append("a")
            elif fin[0] == "a":
                celdas.append("\\textbf{\\color{azuldos}a}")
            else:
                celdas.append("\\color{grisclaro}b")
        filas.append(f"{t(a)} & " + " & ".join(celdas) + r" \\")
    return (
        "{\\scriptsize\\setlength{\\tabcolsep}{2.2pt}\\renewcommand{\\arraystretch}{1.0}\\filas\n"
        f"\\begin{{longtable}}{{{cols}}}\n"
        f"\\rowcolor{{azul}}\\cab{{Atributo}} & {cab} \\\\\n\\endhead\n"
        + "\n".join(filas) + "\n\\end{longtable}}\n"
    )


def main():
    for lhs, rhs, *_ in F:
        for a in lhs + rhs:
            assert a in ATRIBUTOS, a

    eliminadas, conservadas, paso2, extranos, paso3, redundantes, g = cubrimiento_minimal(F)
    traza, sueltos, rho = sintesis(g, conservadas)
    assert not sueltos, sueltos
    assert {a for *_, ui in rho for a in ui} == ATRIBUTOS
    for n, _, ui in rho:
        assert en_3fn(ui, g), n

    escribir("universo.tex", tex_universo())
    escribir("dependencias.tex", tex_dependencias())
    escribir("cubrimiento.tex", tex_cubrimiento(
        eliminadas, conservadas, paso2, extranos, paso3, redundantes, g))
    escribir("sintesis.tex", tex_sintesis(traza, rho))
    escribir("esquemas.tex", tex_esquemas(rho, g))

    rho_plj = [(n, ui) for n, _, ui in rho]
    sin_llave = plj(agrupar(g), rho_plj, U)[3]
    ks = tex_llaves(g)
    contenidas = [k for k in ks if any(set(k) <= set(ui) for _, ui in rho_plj)]
    rho2 = rho_plj + [("Llave", list(ks[0]))]
    traza_plj, llenas = tex_plj(g, rho2)
    inicial, final, pasos, _ = plj(agrupar(g), rho2, U)
    escribir("plj-traza.tex", traza_plj)
    escribir("matriz.tex", tex_matriz(inicial, final, rho2))

    print(f"|U| = {len(U)}  |F| = {len(F)}  |F'| = {len(paso2)}  |G| = {len(g)}")
    print("propias eliminadas:", [d[2] for d in eliminadas])
    print("atributos redundantes:", [(l, r, a) for l, r, a in extranos])
    print("dependencias redundantes:", redundantes)
    print("esquemas:", [(n, ui) for n, _, ui in rho])
    print("llaves:", ks)
    print("llave contenida en algún esquema de rho:", contenidas)
    print("PLJ sin la llave, filas de a:", sin_llave)
    print("PLJ con la llave, filas de a:", llenas, "pasadas:", max(p[0] for p in pasos))


if __name__ == "__main__":
    main()
