# -*- coding: utf-8 -*-
"""Verificación formal del diseño: genera los fragmentos LaTeX de la sección 6.

Calcula, sobre el universo U y el conjunto F extraído del MERX:
  - el cubrimiento mínimo G (algoritmo de la conferencia 6),
  - las llaves candidatas de R(U, G),
  - la proyección de G sobre cada esquema de la descomposición y su FNBC,
  - la PPDF con el algoritmo 5.4 (Ri-operaciones),
  - la PLJ con el algoritmo 5.3 (matriz).

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
    ("Fecha", "día lectivo"),
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


def fd(lhs, rhs, origen):
    return (tuple(lhs.split()), tuple(rhs.split()), origen)


# F según el algoritmo de extracción: paso 1 entidades, 2 interrelaciones,
# 3 agregaciones y 4 reglas del negocio. Las K -> K triviales no se listan.
F = [
    # Paso 1: conjuntos de entidades
    fd("#P", "NombreP Plan", "PROGRAMA ACADÉMICO"),
    fd("#A", "NombreA", "ASIGNATURA"),
    fd("#C", "NombreC Especialidad", "COORDINADOR ACADÉMICO"),
    fd("#E", "NombreE Edad Grupo", "ESTUDIANTE"),
    fd("#J", "NombreJ", "JEFE DE DEPARTAMENTO"),
    fd("#B", "Descripcion Tipo Complejidad", "BLOQUE DE CONTENIDO"),
    fd("#S", "FInicio FFin", "SEMESTRE"),
    fd("#H", "FCreacion PTeorica PPractica PLaboratorio Cobertura Cantidad", "HORARIO"),
    fd("#Au", "Edificio Capacidad", "AULA"),
    fd("#F", "Dia HInicio HFin", "FRANJA HORARIA"),
    fd("#Sol", "Motivo FSolicitud EstadoS FResolucion", "SOLICITUD DE CAMBIO"),
    # Paso 2: interrelaciones con un extremo de cardinalidad máxima 1
    fd("#A", "#P", "CUBRIR"),
    fd("#B", "#CCrea", "CREAR"),
    fd("#B", "#A", "ABORDAR"),
    fd("#H", "#CGen", "GENERAR"),
    fd("#H", "#P", "PERTENECER"),
    fd("#H", "#S", "CORRESPONDER"),
    fd("#H", "#J", "REVISAR"),
    fd("#H", "#HAnt", "SUSTITUIR"),
    fd("#HAnt", "#H", "SUSTITUIR"),
    fd("#H #B", "#F", "OCUPAR"),
    fd("#H #B", "#Au", "UTILIZAR"),
    fd("#Sol", "#E", "SOLICITAR"),
    fd("#Sol", "#HOri", "ORIGEN"),
    fd("#Sol", "#HDes", "DESTINO"),
    fd("#Sol", "#CAt", "ATENDER"),
    fd("#Sol", "#CApo", "APOYAR"),
    # Paso 3: agregaciones
    fd("#C #P", "PGenerar PValidar", "AUTORIZACIÓN"),
    fd("#C #H", "FValidacion ObsV", "VALIDACIÓN"),
    fd("#J #H", "FRevision Decision ObsR", "REVISIÓN"),
    fd("#E #H #B Fecha", "EstadoA", "ASISTENCIA"),
    # Paso 4: reglas del negocio
    fd("Descripcion #A Tipo", "#B", "RN-03"),
    fd("FInicio", "#S", "RN-05"),
    fd("FFin", "#S", "RN-05"),
    fd("Dia HInicio", "#F", "RN-04"),
    fd("Dia HFin", "#F", "RN-04"),
    fd("#H #F", "#B", "RN-09"),
]

# Descomposición obtenida por el diseño intuitivo (sección 4.5)
RHO = [
    ("Programa", "#P NombreP Plan"),
    ("Asignatura", "#A NombreA #P"),
    ("Coordinador", "#C NombreC Especialidad"),
    ("Autorizacion", "#C #P PGenerar PValidar"),
    ("Estudiante", "#E NombreE Edad Grupo"),
    ("Matricula", "#E #P"),
    ("Jefe", "#J NombreJ"),
    ("Bloque", "#B Descripcion Tipo Complejidad #A #CCrea"),
    ("Semestre", "#S FInicio FFin"),
    ("Horario", "#H FCreacion PTeorica PPractica PLaboratorio Cobertura Cantidad #P #S #CGen"),
    ("Validacion", "#C #H FValidacion ObsV"),
    ("Revision", "#H #J FRevision Decision ObsR"),
    ("Sustitucion", "#H #HAnt"),
    ("Aula", "#Au Edificio Capacidad"),
    ("Franja", "#F Dia HInicio HFin"),
    ("Sesion", "#H #B #F #Au"),
    ("Asignacion", "#E #H"),
    ("Fecha", "Fecha"),
    ("Asistencia", "#E #H #B Fecha EstadoA"),
    ("Solicitud", "#Sol Motivo FSolicitud EstadoS FResolucion #E #HOri #HDes #CAt #CApo"),
]
RHO = [(n, a.split()) for n, a in RHO]

NOMBRE_TEX = {
    "Autorizacion": "Autorización",
    "Matricula": "Matrícula",
    "Validacion": "Validación",
    "Revision": "Revisión",
    "Sustitucion": "Sustitución",
    "Sesion": "Sesión",
    "Asignacion": "Asignación",
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


def simples(deps):
    return [(tuple(l), (a,)) for l, r, *_ in deps for a in r]


def cubrimiento_minimo(deps):
    """Devuelve (paso1, eliminados_atributos, paso2, eliminadas_df, G)."""
    paso1 = []
    for l, r in simples(deps):
        if (l, r) not in paso1:
            paso1.append((l, r))
    extranos = []
    paso2 = []
    for l, r in paso1:
        lhs = list(l)
        for a in list(l):
            if len(lhs) == 1:
                break
            resto = [b for b in lhs if b != a]
            if r[0] in clausura(resto, paso1):
                extranos.append((l, r, a))
                lhs = resto
        paso2.append((tuple(lhs), r))
    # sin duplicados conservando el orden
    vistos = []
    for d in paso2:
        if d not in vistos:
            vistos.append(d)
    paso2 = vistos
    redundantes = []
    g = list(paso2)
    for d in list(paso2):
        otras = [e for e in g if e != d]
        if d[1][0] in clausura(d[0], otras):
            redundantes.append(d)
            g = otras
    return paso1, extranos, paso2, redundantes, g


def llaves(universo, deps):
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
    for k in range(0, len(ambos) + 1):
        for extra in combinations(ambos, k):
            cand = base + list(extra)
            if any(set(e) <= set(cand) for e in encontradas):
                continue
            if clausura(cand, deps) >= set(universo):
                encontradas.append(cand)
    return solo_izq, solo_der, ambos, ninguno, encontradas


def proyeccion(ui, deps):
    """Base no trivial de pi_Ui(G): X -> (X+ ∩ Ui) - X para X minimales."""
    base = []
    for k in range(1, len(ui) + 1):
        for x in combinations(ui, k):
            cl = (clausura(x, deps) & set(ui)) - set(x)
            if not cl:
                continue
            # se omite si un subconjunto propio ya determina lo mismo
            if any(set(y) < set(x) and ((clausura(y, deps) & set(ui)) - set(y)) >= cl
                   for y, _ in base):
                continue
            if clausura(x, deps) >= set(ui):
                # superllave: solo se listan las minimales
                if any(set(y) < set(x) and clausura(y, deps) >= set(ui) for y, _ in base):
                    continue
            base.append((x, tuple(a for a in ui if a in cl)))
    return base


def llaves_de(ui, deps):
    res = []
    for k in range(1, len(ui) + 1):
        for x in combinations(ui, k):
            if any(set(y) <= set(x) for y in res):
                continue
            if clausura(x, deps) >= set(ui):
                res.append(x)
    return res


def ppdf(deps, rho):
    """Algoritmo 5.4. Devuelve por DF la traza de Z y si se preserva."""
    trazas = []
    for lhs, rhs in deps:
        z = set(lhs)
        pasos = []
        cambio = True
        pasada = 0
        while cambio:
            cambio = False
            pasada += 1
            for nombre, ui in rho:
                nuevo = z | (clausura(z & set(ui), deps) & set(ui))
                if nuevo != z:
                    pasos.append((pasada, nombre, set(nuevo - z)))
                    z = nuevo
                    cambio = True
        trazas.append((lhs, rhs, pasos, set(rhs) <= z))
    return trazas


def plj(deps, rho, universo):
    """Algoritmo 5.3. Devuelve matriz inicial, final, pasos y fila de a's."""
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


# --- LaTeX ------------------------------------------------------------------

def t(a):
    return a.replace("#", r"\#")


def conj(attrs):
    return ", ".join(t(a) for a in attrs)


def llave(attrs):
    return "\\{" + conj(attrs) + "\\}"


def dep(lhs, rhs):
    return f"{conj(lhs)} \\ensuremath{{\\to}} {conj(rhs)}"


def nombre(n):
    return NOMBRE_TEX.get(n, n)


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


def tex_dependencias():
    pasos = [
        ("Paso 1. Conjuntos de entidades", 0, 11),
        ("Paso 2. Interrelaciones con un extremo de cardinalidad máxima 1", 11, 27),
        ("Paso 3. Agregaciones", 27, 31),
        ("Paso 4. Reglas del negocio (sección~\\ref{sec:restricciones})", 31, len(F)),
    ]
    out = []
    n = 1
    for titulo, a, b in pasos:
        out.append(f"\\textbf{{{titulo}}}\n\\begin{{enumerate}}[label=f\\arabic*,start={n},leftmargin=3em]")
        for lhs, rhs, origen in F[a:b]:
            out.append(f"  \\item {dep(lhs, rhs)} \\hfill {{\\small\\color{{gris}}{origen}}}")
            n += 1
        out.append("\\end{enumerate}")
    return "\n".join(out) + "\n"


def tex_cubrimiento(paso1, extranos, paso2, redundantes, g):
    out = []
    out.append(
        f"\\textbf{{Paso 1.}} Al descomponer las partes derechas, las {len(F)} dependencias de $F$ "
        f"se convierten en {len(paso1)} dependencias de la forma $X \\to A$ ($F'$).\n"
    )
    compuestas = [(l, r) for l, r in paso1 if len(l) > 1]
    filas = []
    for l, r in compuestas:
        detalle = []
        for a in l:
            resto = [b for b in l if b != a]
            cl = clausura(resto, paso1)
            veredicto = "sí" if r[0] in cl else "no"
            detalle.append(f"{llave(resto)}$^+ \\ni$ {t(r[0])}: {veredicto}")
        filas.append(f"{dep(l, r)} & " + "; ".join(detalle) + r" \\")
    out.append(
        "\\textbf{Paso 2.} Solo las dependencias con determinante compuesto pueden tener atributos "
        "extraños. Para cada atributo $B$ de $X$ se comprueba si $A \\in (X - B)^+_{F'}$:\n\n"
        "{\\footnotesize\\filas\n\\begin{xltabular}{\\linewidth}{L{0.7}L{1.3}}\n"
        "\\rowcolor{azul}\\cab{Dependencia} & \\cab{Comprobación} \\\\\n\\endhead\n"
        + "\n".join(filas) + "\n\\end{xltabular}}\n"
    )
    if extranos:
        items = "; ".join(
            f"en {dep(l, r)} sobra {t(a)}" for l, r, a in extranos
        )
        out.append(f"Resultan extraños: {items}. Se obtiene $F''$.\n")
    else:
        out.append("No hay atributos extraños: $F'' = F'$.\n")
    fuentes = {}
    for l, r in paso2:
        fuentes.setdefault(r[0], []).append((l, r))
    unicas = sum(1 for v in fuentes.values() if len(v) == 1)
    filas3 = []
    for a in U:
        for l, r in fuentes.get(a, []):
            if len(fuentes[a]) < 2:
                continue
            otras = [e for e in paso2 if e != (l, r)]
            cl = clausura(l, otras)
            filas3.append(
                f"{dep(l, r)} & {conj([b for b in U if b in cl])} & "
                f"{'sí' if a in cl else 'no'} \\\\"
            )
    out.append(
        "\n\\textbf{Paso 3.} Si $A$ solo aparece a la derecha de $X \\to A$, al quitar esa "
        f"dependencia $A$ deja de ser alcanzable desde $X$, así que no es redundante. Ocurre con "
        f"{unicas} de los {len(fuentes)} atributos que aparecen a la derecha. Para los demás se "
        "calcula $X^+$ con $F'' - \\{X \\to A\\}$:\n\n"
        "{\\footnotesize\\filas\n\\begin{xltabular}{\\linewidth}{L{0.55}L{1.3}>{\\centering\\arraybackslash}p{16mm}}\n"
        "\\rowcolor{azul}\\cab{$X \\to A$} & \\cab{$X^+$ sin $X \\to A$} & \\cab{¿$A \\in X^+$?} \\\\\n\\endhead\n"
        + "\n".join(filas3) + "\n\\end{xltabular}}\n"
    )
    if redundantes:
        items = "; ".join(dep(l, r) for l, r in redundantes)
        out.append(f"Son redundantes: {items}.\n")
    else:
        out.append("Ninguna es redundante: $G = F''$.\n")
    agrupadas = agrupar(g)
    out.append(
        f"\nEl cubrimiento mínimo $G$ tiene {len(g)} dependencias. Agrupadas por determinante:\n"
        "\\begin{enumerate}[label=g\\arabic*,leftmargin=3em]\n"
        + "\n".join(f"  \\item {dep(l, r)}" for l, r in agrupadas)
        + "\n\\end{enumerate}\n"
    )
    return "\n".join(out)


def agrupar(g):
    orden = []
    grupos = {}
    for l, r in g:
        if l not in grupos:
            grupos[l] = []
            orden.append(l)
        grupos[l].append(r[0])
    return [(l, tuple(a for a in U if a in grupos[l])) for l in orden]


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


def tex_esquemas(g, rho):
    filas = []
    for n, ui in rho:
        base = proyeccion(ui, g)
        ks = llaves_de(ui, g)
        if base:
            deps_txt = "; ".join(dep(l, r) for l, r in base)
        else:
            deps_txt = "solo triviales"
        ks_txt = "; ".join("(" + conj(k) + ")" for k in ks)
        ok = all(any(set(k) <= set(l) for k in ks) for l, _ in base)
        filas.append(
            f"{nombre(n)} & {deps_txt} & {ks_txt} & {'sí' if ok else 'no'} \\\\"
        )
    return (
        "{\\footnotesize\\filas\n"
        "\\begin{xltabular}{\\linewidth}{L{0.55}L{1.75}L{0.6}>{\\centering\\arraybackslash}p{9mm}}\n"
        "\\rowcolor{azul}\\cab{Esquema} & \\cab{Base de $\\pi_{U_i}(G)$} & \\cab{Llaves} & \\cab{FNBC} \\\\\n"
        "\\endhead\n" + "\n".join(filas) + "\n\\end{xltabular}}\n"
    )


def tex_ppdf(g, rho):
    trazas = ppdf(agrupar(g), rho)
    filas = []
    for lhs, rhs, pasos, ok in trazas:
        aportan = []
        for pasada, n, nuevos in pasos:
            if set(rhs) & nuevos and nombre(n) not in aportan:
                aportan.append(nombre(n))
        # pasada en que Z ya contiene a Y
        z = set(lhs)
        en = 0
        for pasada, n, nuevos in pasos:
            z |= nuevos
            if set(rhs) <= z:
                en = pasada
                break
        filas.append(
            f"{dep(lhs, rhs)} & {', '.join(aportan)} & {en} & {'sí' if ok else 'no'} \\\\"
        )
    return (
        "{\\footnotesize\\filas\n"
        "\\begin{xltabular}{\\linewidth}{L{1.45}L{0.55}>{\\centering\\arraybackslash}p{12mm}>{\\centering\\arraybackslash}p{12mm}}\n"
        "\\rowcolor{azul}\\cab{Dependencia de $G$} & \\cab{$R_i$ que aportan $Y$} & \\cab{Pasada} & \\cab{$Y \\subseteq Z$} \\\\\n"
        "\\endhead\n" + "\n".join(filas) + "\n\\end{xltabular}}\n"
    ), all(ok for *_, ok in trazas)


def tex_ppdf_ejemplo(g, rho):
    lhs, rhs = ("#H", "#F"), ("#B",)
    z = set(lhs)
    lineas = [f"$Z =$ {llave(lhs)}"]
    for n, ui in rho:
        inter = [a for a in U if a in z and a in ui]
        nuevo = z | (clausura(inter, g) & set(ui))
        if inter:
            ganados = [a for a in U if a in nuevo - z]
            lineas.append(
                f"{nombre(n)}: $Z \\cap U_i =$ {llave(inter)}; "
                + (f"$(Z \\cap U_i)^+ \\cap U_i$ añade {llave(ganados)}"
                   if ganados else "no añade nada")
            )
        z = nuevo
    return (
        "\\begin{itemize}\n"
        + "\n".join(f"  \\item {l}" for l in lineas)
        + "\n\\end{itemize}\n"
        f"Al terminar la pasada, $Z =$ {llave([a for a in U if a in z])}, que contiene a \\#B. "
        "Una segunda pasada no cambia $Z$.\n"
    )


def tex_plj(g, rho, llave):
    rho2 = rho + [("Llave", list(llave))]
    inicial, final, pasos, llenas = plj(agrupar(g), rho2, U)
    sin_llave = plj(agrupar(g), rho, U)[3]
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
    traza = (
        "{\\footnotesize\\filas\n\\begin{xltabular}{\\linewidth}{c L{0.7}L{1.3}}\n"
        "\\rowcolor{azul}\\cab{Pasada} & \\cab{Dependencia aplicada} & "
        "\\cab{Columnas en que la fila Llave pasa de $b$ a $a$} \\\\\n\\endhead\n"
        + "\n".join(filas) + "\n\\end{xltabular}}\n"
    )
    pasadas = max(p[0] for p in pasos) if pasos else 0
    return traza, sin_llave, llenas, pasadas, inicial, final, rho2


def tex_matriz(inicial, final, rho2):
    nombres = [nombre(n) for n, _ in rho2]
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
        "{\\scriptsize\\setlength{\\tabcolsep}{2.2pt}\\renewcommand{\\arraystretch}{1.05}\\filas\n"
        f"\\begin{{longtable}}{{{cols}}}\n"
        f"\\rowcolor{{azul}}\\cab{{Atributo}} & {cab} \\\\\n\\endhead\n"
        + "\n".join(filas) + "\n\\end{longtable}}\n"
    )


def main():
    for lhs, rhs, _ in F:
        for a in lhs + rhs:
            assert a in ATRIBUTOS, a
    for n, ui in RHO:
        for a in ui:
            assert a in ATRIBUTOS, (n, a)
    cubiertos = {a for _, ui in RHO for a in ui}
    assert cubiertos == ATRIBUTOS, ATRIBUTOS - cubiertos

    paso1, extranos, paso2, redundantes, g = cubrimiento_minimo(F)
    escribir("universo.tex", tex_universo())
    escribir("dependencias.tex", tex_dependencias())
    escribir("cubrimiento.tex", tex_cubrimiento(paso1, extranos, paso2, redundantes, g))
    ks = tex_llaves(g)
    escribir("esquemas.tex", tex_esquemas(g, RHO))
    tabla, preserva = tex_ppdf(g, RHO)
    escribir("ppdf.tex", tabla)
    escribir("ppdf-ejemplo.tex", tex_ppdf_ejemplo(g, RHO))
    traza, sin_llave, llenas, pasadas, inicial, final, rho2 = tex_plj(g, RHO, ks[0])
    escribir("plj-traza.tex", traza)
    escribir("matriz.tex", tex_matriz(inicial, final, rho2))

    contenidas = [k for k in ks if any(set(k) <= set(ui) for _, ui in RHO)]
    print(f"|U| = {len(U)}  |F| = {len(F)}  |F'| = {len(paso1)}  |G| = {len(g)}")
    print("atributos extraños:", [(l, r, a) for l, r, a in extranos])
    print("dependencias redundantes:", redundantes)
    print("llaves:", ks)
    print("llave contenida en algún esquema de rho:", contenidas)
    print("PPDF:", preserva)
    print("PLJ sin la llave, filas de a:", sin_llave)
    print("PLJ con la llave, filas de a:", llenas, "pasadas:", pasadas)
    for n, ui in RHO:
        print(f"  {n}: llaves {llaves_de(ui, g)}  base {proyeccion(ui, g)}")


if __name__ == "__main__":
    main()
