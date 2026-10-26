# -*- coding: utf-8 -*-
"""Figuras del MERX (notación del curso) y del esquema estrella para el informe.

Notación: rectángulo = conjunto de entidades, rombo = interrelación, recuadro
con nombre = agregación, óvalo = atributo, subrayado = llave, óvalo
discontinuo y subrayado = llave heredada por la agregación. La cardinalidad
(mín, máx) se escribe junto al conjunto de entidades al que se refiere.
"""

import math

MUCHOS = "*"


def esc(text):
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


class Shape:
    def __init__(self, kind, cx, cy, w, h):
        self.kind = kind
        self.cx = cx
        self.cy = cy
        self.w = w
        self.h = h

    def border(self, tx, ty, pad=2):
        dx = tx - self.cx
        dy = ty - self.cy
        dist = math.hypot(dx, dy) or 1.0
        hw, hh = self.w / 2.0, self.h / 2.0
        if self.kind == "diamond":
            s = 1.0 / ((abs(dx) / hw) + (abs(dy) / hh))
        elif self.kind == "oval":
            s = 1.0 / math.sqrt((dx / hw) ** 2 + (dy / hh) ** 2)
        else:
            sx = hw / abs(dx) if dx else 1e9
            sy = hh / abs(dy) if dy else 1e9
            s = min(sx, sy)
        s = max(0.0, s - pad / dist)
        return self.cx + dx * s, self.cy + dy * s


class Canvas:
    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.boxes = []
        self.under = []
        self.links = []
        self.nodes = []
        self.labels = []

    def _text(self, cx, cy, text, size=13, weight="600", fill="#14233a"):
        lines = str(text).split("\n")
        style = f"font-size:{size}px;font-weight:{weight};fill:{fill};"
        lh = size + 1
        start = cy - (len(lines) - 1) * lh / 2.0
        return "".join(
            f'<text x="{cx}" y="{start + i * lh}" text-anchor="middle" '
            f'dominant-baseline="middle" style="{style}">{esc(line)}</text>'
            for i, line in enumerate(lines)
        )

    def entity(self, cx, cy, w, h, text):
        self.nodes.append(
            f'<rect x="{cx - w/2}" y="{cy - h/2}" width="{w}" height="{h}" '
            f'fill="#dae8fc" stroke="#1a4a7a" stroke-width="1.7"/>'
        )
        self.nodes.append(self._text(cx, cy, text, size=13, weight="700", fill="#10283f"))
        return Shape("rect", cx, cy, w, h)

    def rel(self, cx, cy, w, h, text):
        pts = f"{cx},{cy - h/2} {cx + w/2},{cy} {cx},{cy + h/2} {cx - w/2},{cy}"
        self.nodes.append(
            f'<polygon points="{pts}" fill="#fff4cc" stroke="#8a6d1b" stroke-width="1.5"/>'
        )
        self.nodes.append(self._text(cx, cy, text, size=11, weight="700", fill="#3d3208"))
        return Shape("diamond", cx, cy, w, h)

    def agg(self, x1, y1, x2, y2, text):
        """Agregación: recuadro con su nombre abajo a la derecha."""
        self.boxes.append(
            f'<rect x="{x1}" y="{y1}" width="{x2 - x1}" height="{y2 - y1}" '
            f'fill="#f3f7fb" stroke="#4a5d70" stroke-width="1.5"/>'
        )
        self.boxes.append(
            f'<text x="{x2 - 10}" y="{y2 - 11}" text-anchor="end" '
            f'style="font-size:12px;font-weight:700;fill:#2b3b4c;">{esc(text)}</text>'
        )
        return Shape("rect", (x1 + x2) / 2, (y1 + y2) / 2, x2 - x1, y2 - y1)

    def attr(self, cx, cy, text, kind="attr"):
        size = 11
        w = max(70, int(len(text) * size * 0.6 + 22))
        h = 28
        dash = ' stroke-dasharray="5 3"' if kind == "inherited" else ""
        fill = "#ffffff" if kind == "inherited" else "#e7f5e8"
        self.nodes.append(
            f'<ellipse cx="{cx}" cy="{cy}" rx="{w/2}" ry="{h/2}" '
            f'fill="{fill}" stroke="#2e7d32" stroke-width="1.3"{dash}/>'
        )
        dy = -1 if kind in ("key", "inherited") else 0
        self.nodes.append(self._text(cx, cy + dy, text, size=size, weight="600", fill="#1a2e22"))
        if kind in ("key", "inherited"):
            half = min(w / 2 - 10, len(text) * 3.3 + 2)
            self.nodes.append(
                f'<line x1="{cx - half}" y1="{cy + 7}" x2="{cx + half}" y2="{cy + 7}" '
                f'stroke="#1a2e22" stroke-width="1"/>'
            )
        return Shape("oval", cx, cy, w, h)

    def link_attr(self, oval, host, to_border=False):
        if to_border:
            # atributo de una agregación: cae vertical sobre el borde del recuadro
            x = min(max(oval.cx, host.cx - host.w / 2 + 8), host.cx + host.w / 2 - 8)
            y = host.cy - host.h / 2 if oval.cy < host.cy else host.cy + host.h / 2
        else:
            x, y = host.cx, host.cy
        self.under.append(
            f'<line x1="{oval.cx}" y1="{oval.cy}" x2="{x:.1f}" y2="{y:.1f}" '
            f'stroke="#5f8f68" stroke-width="1.1"/>'
        )

    def attrs(self, host, items, to_border=False):
        for cx, cy, text, kind in items:
            self.link_attr(self.attr(cx, cy, text, kind), host, to_border)

    def connect(self, a, b, ca=None, cb=None, nudge_a=(0, 0), nudge_b=(0, 0)):
        """Une a con b. ca y cb son la cardinalidad junto a a y junto a b."""
        x1, y1 = a.border(b.cx, b.cy)
        x2, y2 = b.border(a.cx, a.cy)
        self.links.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="#243040" stroke-width="1.35"/>'
        )
        if ca:
            self.labels.append(self._card(x1, y1, x2, y2, ca, nudge_a))
        if cb:
            self.labels.append(self._card(x2, y2, x1, y1, cb, nudge_b))

    def line(self, pts, color="#243040"):
        d = " ".join(f"{x},{y}" for x, y in pts)
        self.links.append(
            f'<polyline points="{d}" fill="none" stroke="{color}" stroke-width="1.35"/>'
        )

    def label(self, x, y, text, size=12, fill="#10283f", weight="700", italic=False):
        self.labels.append(self._halo(x, y, text, size, fill, weight, italic))

    def _card(self, bx, by, ox, oy, text, nudge=(0, 0)):
        dx, dy = ox - bx, oy - by
        dist = math.hypot(dx, dy) or 1.0
        ux, uy = dx / dist, dy / dist
        px, py = -uy, ux
        if py > 0 or (py == 0 and px < 0):
            px, py = -px, -py
        along = min(22, dist * 0.35)
        x = bx + ux * along + px * 11 + nudge[0]
        y = by + uy * along + py * 11 + nudge[1]
        return self._halo(x, y, text, 12, "#10283f", "700")

    def _halo(self, x, y, text, size, fill, weight, italic=False):
        style = f"font-size:{size}px;font-weight:{weight};"
        if italic:
            style += "font-style:italic;"
        return (
            f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="middle" dominant-baseline="middle" '
            f'style="{style}fill:#ffffff;stroke:#ffffff;stroke-width:4px;">{esc(text)}</text>'
            f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="middle" dominant-baseline="middle" '
            f'style="{style}fill:{fill};">{esc(text)}</text>'
        )

    def render(self):
        bg = f'<rect x="0" y="0" width="{self.w}" height="{self.h}" fill="#fbfcfe"/>'
        body = "".join([bg] + self.boxes + self.under + self.links + self.nodes + self.labels)
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" '
            f'font-family="Segoe UI, Helvetica, Arial, sans-serif">{body}</svg>'
        )


def card(minimo, maximo):
    return f"{minimo},{MUCHOS if maximo == '*' else maximo}"


def fig_oferta():
    c = Canvas(1120, 640)
    autorizacion = c.agg(30, 220, 710, 330, "AUTORIZACIÓN")
    coord = c.entity(130, 275, 170, 52, "COORDINADOR\nACADÉMICO")
    autorizar = c.rel(350, 275, 124, 70, "AUTORIZAR")
    programa = c.entity(560, 275, 170, 52, "PROGRAMA\nACADÉMICO")
    c.connect(coord, autorizar, ca=card(0, "*"))
    c.connect(autorizar, programa, cb=card(0, "*"))
    c.attrs(autorizacion, [
        (100, 165, "#COORDINADOR", "inherited"),
        (240, 165, "#PROGRAMA", "inherited"),
        (380, 165, "PUEDE GENERAR", "attr"),
        (520, 125, "PUEDE VALIDAR", "attr"),
    ], to_border=True)
    c.attrs(coord, [
        (80, 400, "#COORDINADOR", "key"),
        (170, 450, "NOMBRE", "attr"),
        (300, 410, "ESPECIALIDAD", "attr"),
    ])
    c.attrs(programa, [
        (660, 60, "#PROGRAMA", "key"),
        (790, 95, "NOMBRE", "attr"),
        (830, 165, "PLAN DE ESTUDIOS", "attr"),
    ])

    cubrir = c.rel(860, 275, 110, 66, "CUBRIR")
    asignatura = c.entity(1030, 275, 150, 48, "ASIGNATURA")
    c.connect(programa, cubrir, ca=card(1, 1))
    c.connect(cubrir, asignatura, cb=card(1, "*"))
    c.attrs(asignatura, [
        (980, 370, "#ASIGNATURA", "key"),
        (1070, 420, "NOMBRE", "attr"),
    ])

    matricular = c.rel(560, 430, 130, 70, "MATRICULAR")
    estudiante = c.entity(560, 560, 150, 48, "ESTUDIANTE")
    c.connect(programa, matricular, ca=card(1, "*"))
    c.connect(matricular, estudiante, cb=card(0, "*"))
    c.attrs(estudiante, [
        (380, 530, "#ESTUDIANTE", "key"),
        (390, 600, "NOMBRE", "attr"),
        (740, 530, "EDAD", "attr"),
        (730, 600, "GRUPO", "attr"),
    ])
    return c.render()


def fig_bloque():
    c = Canvas(1000, 330)
    coord = c.entity(100, 90, 170, 52, "COORDINADOR\nACADÉMICO")
    crear = c.rel(300, 90, 104, 64, "CREAR")
    bloque = c.entity(500, 90, 170, 52, "BLOQUE DE\nCONTENIDO")
    abordar = c.rel(700, 90, 116, 66, "ABORDAR")
    asignatura = c.entity(895, 90, 150, 48, "ASIGNATURA")
    c.connect(coord, crear, ca=card(1, 1))
    c.connect(crear, bloque, cb=card(0, "*"))
    c.connect(bloque, abordar, ca=card(0, "*"))
    c.connect(abordar, asignatura, cb=card(1, 1))
    c.attrs(bloque, [
        (290, 230, "#BLOQUE", "key"),
        (430, 270, "DESCRIPCIÓN", "attr"),
        (590, 270, "TIPO DE ACTIVIDAD", "attr"),
        (720, 220, "COMPLEJIDAD", "attr"),
    ])
    return c.render()


def fig_horario():
    c = Canvas(1040, 620)
    horario = c.entity(520, 290, 150, 50, "HORARIO")
    programa = c.entity(520, 50, 170, 52, "PROGRAMA\nACADÉMICO")
    pertenecer = c.rel(520, 165, 140, 66, "PERTENECER")
    c.connect(programa, pertenecer, ca=card(1, 1))
    c.connect(pertenecer, horario, cb=card(0, "*"))

    coord = c.entity(100, 290, 170, 52, "COORDINADOR\nACADÉMICO")
    generar = c.rel(300, 290, 116, 66, "GENERAR")
    c.connect(coord, generar, ca=card(1, 1))
    c.connect(generar, horario, cb=card(0, "*"))

    semestre = c.entity(930, 290, 150, 50, "SEMESTRE")
    corresponder = c.rel(740, 290, 156, 66, "CORRESPONDER")
    c.connect(semestre, corresponder, ca=card(1, 1))
    c.connect(corresponder, horario, cb=card(0, "*"))
    c.attrs(semestre, [
        (930, 175, "#SEMESTRE", "key"),
        (900, 410, "FECHA DE INICIO", "attr"),
        (980, 460, "FECHA DE FIN", "attr"),
    ])

    c.rel(520, 520, 140, 66, "SUSTITUIR")
    # interrelación unaria: dos líneas del horario a los lados del rombo
    c.line([(490, 315), (490, 501)])
    c.line([(550, 315), (550, 501)])
    c.label(470, 340, card(0, 1))
    c.label(572, 340, card(0, 1))
    c.label(452, 470, "anterior", size=11, fill="#5c6b7a", weight="600", italic=True)
    c.label(590, 470, "sucesor", size=11, fill="#5c6b7a", weight="600", italic=True)

    c.attrs(horario, [
        (380, 205, "#HORARIO", "key"),
        (670, 205, "FECHA DE CREACIÓN", "attr"),
        (270, 390, "PROPORCIÓN TEÓRICA", "attr"),
        (250, 445, "PROPORCIÓN PRÁCTICA", "attr"),
        (250, 500, "PROPORCIÓN DE LABORATORIO", "attr"),
        (740, 400, "COBERTURA MÍNIMA", "attr"),
        (740, 460, "CANTIDAD DE BLOQUES", "attr"),
    ])
    return c.render()


def fig_validacion():
    c = Canvas(1000, 300)
    validacion = c.agg(30, 120, 800, 230, "VALIDACIÓN")
    coord = c.entity(140, 175, 170, 52, "COORDINADOR\nACADÉMICO")
    validar = c.rel(400, 175, 114, 66, "VALIDAR")
    horario = c.entity(640, 175, 150, 50, "HORARIO")
    c.connect(coord, validar, ca=card(0, "*"))
    c.connect(validar, horario, cb=card(0, "*"))
    c.attrs(validacion, [
        (150, 60, "#COORDINADOR", "inherited"),
        (310, 60, "#HORARIO", "inherited"),
        (480, 60, "FECHA DE VALIDACIÓN", "attr"),
        (660, 60, "OBSERVACIONES", "attr"),
    ], to_border=True)
    return c.render()


def fig_revision():
    c = Canvas(1000, 380)
    revision = c.agg(30, 120, 800, 230, "REVISIÓN")
    jefe = c.entity(140, 175, 170, 52, "JEFE DE\nDEPARTAMENTO")
    revisar = c.rel(400, 175, 114, 66, "REVISAR")
    horario = c.entity(640, 175, 150, 50, "HORARIO")
    c.connect(jefe, revisar, ca=card(0, 1))
    c.connect(revisar, horario, cb=card(0, "*"))
    c.attrs(revision, [
        (110, 60, "#JEFE", "inherited"),
        (240, 60, "#HORARIO", "inherited"),
        (400, 60, "FECHA DE REVISIÓN", "attr"),
        (560, 60, "DECISIÓN", "attr"),
        (700, 60, "OBSERVACIONES", "attr"),
    ], to_border=True)
    c.attrs(jefe, [
        (90, 320, "#JEFE", "key"),
        (220, 320, "NOMBRE", "attr"),
    ])
    return c.render()


def fig_sesion():
    c = Canvas(1000, 560)
    sesion = c.agg(30, 110, 760, 230, "SESIÓN")
    horario = c.entity(140, 170, 150, 50, "HORARIO")
    programar = c.rel(380, 170, 140, 66, "PROGRAMAR")
    bloque = c.entity(620, 170, 170, 52, "BLOQUE DE\nCONTENIDO")
    c.connect(horario, programar, ca=card(0, "*"))
    c.connect(programar, bloque, cb=card(1, "*"))
    c.attrs(sesion, [
        (300, 50, "#HORARIO", "inherited"),
        (460, 50, "#BLOQUE", "inherited"),
    ], to_border=True)

    ocupar = c.rel(250, 320, 110, 64, "OCUPAR")
    franja = c.entity(250, 440, 160, 52, "FRANJA\nHORARIA")
    c.connect(sesion, ocupar, ca=card(0, "*"), nudge_a=(-40, 0))
    c.connect(ocupar, franja, cb=card(1, 1))
    c.attrs(franja, [
        (90, 390, "#FRANJA", "key"),
        (90, 470, "DÍA", "attr"),
        (180, 525, "HORA DE INICIO", "attr"),
        (340, 525, "HORA DE FIN", "attr"),
    ])

    utilizar = c.rel(620, 320, 120, 64, "UTILIZAR")
    aula = c.entity(620, 440, 130, 48, "AULA")
    c.connect(sesion, utilizar, ca=card(0, "*"), nudge_a=(40, 0))
    c.connect(utilizar, aula, cb=card(1, 1))
    c.attrs(aula, [
        (480, 470, "#AULA", "key"),
        (620, 525, "EDIFICIO", "attr"),
        (780, 470, "CAPACIDAD", "attr"),
    ])
    return c.render()


def fig_asistencia():
    c = Canvas(1040, 470)
    asistencia = c.agg(20, 110, 1020, 440, "ASISTENCIA")
    sesion = c.agg(45, 140, 600, 250, "SESIÓN")
    horario = c.entity(140, 195, 140, 48, "HORARIO")
    programar = c.rel(320, 195, 136, 62, "PROGRAMAR")
    bloque = c.entity(500, 195, 150, 50, "BLOQUE DE\nCONTENIDO")
    c.connect(horario, programar)
    c.connect(programar, bloque)

    asistir = c.rel(760, 195, 120, 64, "ASISTIR")
    fecha = c.entity(930, 195, 120, 46, "FECHA")
    estudiante = c.entity(760, 345, 150, 48, "ESTUDIANTE")
    c.connect(sesion, asistir, ca=card(0, "*"))
    c.connect(asistir, fecha, cb=card(0, "*"))
    c.connect(asistir, estudiante, cb=card(0, "*"))
    c.attrs(fecha, [(930, 330, "FECHA", "key")])
    c.attrs(asistencia, [
        (130, 50, "#ESTUDIANTE", "inherited"),
        (290, 50, "#HORARIO", "inherited"),
        (440, 50, "#BLOQUE", "inherited"),
        (580, 50, "FECHA", "inherited"),
        (720, 50, "ESTADO", "attr"),
    ], to_border=True)
    return c.render()


def fig_solicitud():
    c = Canvas(1040, 640)
    solicitud = c.entity(520, 330, 190, 56, "SOLICITUD\nDE CAMBIO")
    estudiante = c.entity(150, 80, 150, 48, "ESTUDIANTE")
    horario = c.entity(900, 80, 150, 50, "HORARIO")

    asignar = c.rel(520, 80, 124, 64, "ASIGNAR")
    c.connect(estudiante, asignar, ca=card(0, "*"))
    c.connect(asignar, horario, cb=card(0, "*"))

    solicitar = c.rel(300, 210, 124, 64, "SOLICITAR")
    c.connect(estudiante, solicitar, ca=card(1, 1))
    c.connect(solicitar, solicitud, cb=card(0, "*"))

    origen = c.rel(740, 210, 112, 62, "ORIGEN")
    c.connect(horario, origen, ca=card(1, 1))
    c.connect(origen, solicitud, cb=card(0, "*"))
    destino = c.rel(900, 330, 112, 62, "DESTINO")
    c.connect(horario, destino, ca=card(0, 1))
    c.connect(destino, solicitud, cb=card(0, "*"))

    coord = c.entity(130, 460, 170, 52, "COORDINADOR\nACADÉMICO")
    atender = c.rel(320, 390, 116, 62, "ATENDER")
    apoyar = c.rel(320, 530, 112, 62, "APOYAR")
    c.connect(coord, atender, ca=card(1, 1))
    c.connect(atender, solicitud, cb=card(0, "*"))
    c.connect(coord, apoyar, ca=card(0, 1))
    c.connect(apoyar, solicitud, cb=card(0, "*"))

    c.attrs(solicitud, [
        (520, 470, "#SOLICITUD", "key"),
        (660, 445, "MOTIVO", "attr"),
        (560, 545, "FECHA DE SOLICITUD", "attr"),
        (800, 500, "ESTADO", "attr"),
        (760, 600, "FECHA DE RESOLUCIÓN", "attr"),
    ])
    return c.render()


def fig_estrella():
    c = Canvas(1040, 680)

    def dim(cx, cy, w, h, title, lines):
        c.nodes.append(
            f'<rect x="{cx - w/2}" y="{cy - h/2}" width="{w}" height="{h}" rx="2" '
            f'fill="#dae8fc" stroke="#1a4a7a" stroke-width="1.6"/>'
        )
        c.nodes.append(c._text(cx, cy - (8 if lines else 0), title, size=12, weight="700", fill="#10283f"))
        if lines:
            c.nodes.append(c._text(cx, cy + 12, lines, size=10, weight="500", fill="#243848"))
        return Shape("rect", cx, cy, w, h)

    def fact(cx, cy, w, h, title, lines):
        c.nodes.append(
            f'<rect x="{cx - w/2}" y="{cy - h/2}" width="{w}" height="{h}" rx="2" '
            f'fill="#153a5b" stroke="#0d2744" stroke-width="1.6"/>'
        )
        c.nodes.append(c._text(cx, cy - 18, title, size=12, weight="700", fill="#ffffff"))
        c.nodes.append(c._text(cx, cy + 8, lines, size=10, weight="500", fill="#e7eef6"))
        return Shape("rect", cx, cy, w, h)

    tiempo = dim(520, 40, 250, 56, "dim_tiempo", "periodo, año, semestre")
    c.label(520, 82, "la misma dimensión para los tres hechos", size=11, fill="#1a4a7a", weight="600")

    ocup = fact(210, 175, 280, 72, "fact_ocupacion_aula", "medidas: minutos ocupados · sesiones")
    aula = dim(90, 310, 160, 52, "dim_aula", "nombre, edificio")
    franja = dim(310, 310, 230, 52, "dim_franja", "día, etiqueta, inicio, fin")
    c.connect(tiempo, ocup)
    c.connect(aula, ocup)
    c.connect(franja, ocup)

    asist = fact(
        800, 185, 360, 92, "fact_asistencia_bloque",
        "medidas: presentes · ausentes · tasa\ndegeneradas: estudiante · programa",
    )
    grupo = dim(640, 330, 160, 52, "dim_grupo", "grupo")
    bloque = dim(900, 330, 230, 64, "dim_bloque", "descripción, asignatura\ncomplejidad, creador")
    c.connect(tiempo, asist)
    c.connect(grupo, asist)
    c.connect(bloque, asist)

    cambio = fact(
        520, 530, 420, 88, "fact_solicitud_cambio",
        "medida: solicitudes\ndegeneradas: estudiante · programa · estado",
    )
    c.connect(tiempo, cambio)
    c.connect(grupo, cambio)
    return c.render()


FIGURES = [
    ("fig-oferta", "Programa, asignaturas, autorización y matrícula.", fig_oferta),
    ("fig-bloque", "Banco de bloques de contenido.", fig_bloque),
    ("fig-horario", "Horario, generación, semestre y sustitución.", fig_horario),
    ("fig-validacion", "Validación del coordinador.", fig_validacion),
    ("fig-revision", "Revisión del jefe de departamento.", fig_revision),
    ("fig-sesion", "Sesión: bloque programado en un horario, franja y aula.", fig_sesion),
    ("fig-asistencia", "Asistencia a una sesión en un día lectivo.", fig_asistencia),
    ("fig-solicitud", "Asignación y solicitud de cambio de horario.", fig_solicitud),
    ("fig-estrella", "Almacén analítico en esquema estrella.", fig_estrella),
]
