# -*- coding: utf-8 -*-
"""Figuras Chen y esquema estrella para el informe de diseño."""

import math


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

    def border(self, tx, ty, pad=3):
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
        self.under = []
        self.links = []
        self.nodes = []
        self.labels = []

    def _text(self, cx, cy, text, size=13, weight="600", fill="#14233a", italic=False):
        lines = str(text).split("\n")
        style = f"font-size:{size}px;font-weight:{weight};fill:{fill};"
        if italic:
            style += "font-style:italic;"
        if len(lines) == 1:
            return (
                f'<text x="{cx}" y="{cy}" text-anchor="middle" '
                f'dominant-baseline="middle" style="{style}">{esc(lines[0])}</text>'
            )
        lh = size + 1
        start = cy - (len(lines) - 1) * lh / 2.0
        parts = []
        for i, line in enumerate(lines):
            y = start + i * lh
            parts.append(
                f'<text x="{cx}" y="{y}" text-anchor="middle" '
                f'dominant-baseline="middle" style="{style}">{esc(line)}</text>'
            )
        return "".join(parts)

    def entity(self, cx, cy, w, h, text, weak=False):
        if weak:
            self.nodes.append(
                f'<rect x="{cx - w/2}" y="{cy - h/2}" width="{w}" height="{h}" '
                f'fill="#f3e8f7" stroke="#5b2c6f" stroke-width="1.7"/>'
            )
            inset = 4
            self.nodes.append(
                f'<rect x="{cx - w/2 + inset}" y="{cy - h/2 + inset}" '
                f'width="{w - 2*inset}" height="{h - 2*inset}" '
                f'fill="none" stroke="#5b2c6f" stroke-width="1.2"/>'
            )
        else:
            self.nodes.append(
                f'<rect x="{cx - w/2}" y="{cy - h/2}" width="{w}" height="{h}" '
                f'fill="#dae8fc" stroke="#1a4a7a" stroke-width="1.7"/>'
            )
        self.nodes.append(self._text(cx, cy, text, size=13, weight="700", fill="#10283f"))
        return Shape("rect", cx, cy, w, h)

    def rel(self, cx, cy, w, h, text, identifying=False):
        def poly(ww, hh, sw, fill):
            pts = f"{cx},{cy - hh/2} {cx + ww/2},{cy} {cx},{cy + hh/2} {cx - ww/2},{cy}"
            return (
                f'<polygon points="{pts}" fill="{fill}" stroke="#8a6d1b" stroke-width="{sw}"/>'
            )

        self.nodes.append(poly(w, h, 2.4 if identifying else 1.5, "#fff4cc"))
        if identifying:
            self.nodes.append(poly(w * 0.72, h * 0.72, 1.4, "none"))
        self.nodes.append(self._text(cx, cy, text, size=11, weight="700", fill="#3d3208"))
        return Shape("diamond", cx, cy, w, h)

    def attr(self, cx, cy, text, kind="attr"):
        size = 11
        w = max(74, int(len(text) * size * 0.58 + 20))
        h = 28
        if kind == "key":
            fill, stroke, dash, italic = "#ffe6cc", "#b36b00", "", False
        elif kind == "partial":
            fill, stroke, dash, italic = "#ffe6cc", "#b36b00", "", False
        elif kind == "derived":
            fill, stroke, dash, italic = "#ffffff", "#2e7d32", ' stroke-dasharray="5 3"', True
        elif kind == "composite":
            fill, stroke, dash, italic = "#e7f6ea", "#1b5e20", "", False
        else:
            fill, stroke, dash, italic = "#e7f5e8", "#2e7d32", "", False
        sw = 1.8 if kind == "composite" else 1.35
        self.nodes.append(
            f'<ellipse cx="{cx}" cy="{cy}" rx="{w/2}" ry="{h/2}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{dash}/>'
        )
        self.nodes.append(
            self._text(cx, cy - (1 if kind in ("key", "partial") else 0), text,
                       size=size, weight="600", fill="#1a2e22", italic=italic)
        )
        if kind in ("key", "partial"):
            half = min(w / 2 - 12, max(16, len(text) * 2.6))
            y = cy + 7
            extra = ' stroke-dasharray="2.4 2"' if kind == "partial" else ""
            self.nodes.append(
                f'<line x1="{cx - half}" y1="{y}" x2="{cx + half}" y2="{y}" '
                f'stroke="#7a4e00" stroke-width="1.1"{extra}/>'
            )
        return Shape("oval", cx, cy, w, h)

    def link_attr(self, oval, host):
        self.under.append(
            f'<line x1="{oval.cx}" y1="{oval.cy}" x2="{host.cx}" y2="{host.cy}" '
            f'stroke="#5f8f68" stroke-width="1.15"/>'
        )

    def connect(self, a, b, ca=None, cb=None, ta=False, tb=False, ca_nudge=(0, 0), cb_nudge=(0, 0)):
        x1, y1 = a.border(b.cx, b.cy)
        x2, y2 = b.border(a.cx, a.cy)
        both = ta and tb
        sw = 3.3 if both else 1.35
        self.links.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="#243040" stroke-width="{sw}" stroke-linecap="butt"/>'
        )
        if ta and not tb:
            self.links.append(self._cap(x1, y1, x2, y2))
        if tb and not ta:
            self.links.append(self._cap(x2, y2, x1, y1))
        if ca:
            self.labels.append(self._card(x1, y1, x2, y2, a.cx, a.cy, ca, ca_nudge))
        if cb:
            self.labels.append(self._card(x2, y2, x1, y1, b.cx, b.cy, cb, cb_nudge))

    def raw_line(self, x1, y1, x2, y2, sw=1.45, color="#243040"):
        self.links.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            f'stroke="{color}" stroke-width="{sw}" stroke-linecap="butt"/>'
        )

    def label(self, x, y, text, size=11, fill="#3d3208", weight="700"):
        self.labels.append(self._halo(x, y, text, size, fill, weight))

    def _cap(self, x1, y1, x2, y2, length=38):
        dx, dy = x2 - x1, y2 - y1
        dist = math.hypot(dx, dy) or 1.0
        span = min(length, dist * 0.45)
        x3, y3 = x1 + dx / dist * span, y1 + dy / dist * span
        return (
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x3:.1f}" y2="{y3:.1f}" '
            f'stroke="#243040" stroke-width="7" stroke-linecap="butt"/>'
        )

    def _card(self, bx, by, ox, oy, scx, scy, text, nudge=(0, 0)):
        dx, dy = ox - bx, oy - by
        dist = math.hypot(dx, dy) or 1.0
        ux, uy = dx / dist, dy / dist
        px, py = -uy, ux
        along = min(20, dist * 0.34)
        best = None
        for sign in (1, -1):
            x = bx + ux * along + px * 12 * sign
            y = by + uy * along + py * 12 * sign
            score = math.hypot(x - scx, y - scy)
            if best is None or score > best[0]:
                best = (score, x, y)
        return self._halo(best[1] + nudge[0], best[2] + nudge[1], text, 12, "#10283f", "700")

    def _halo(self, x, y, text, size, fill, weight):
        style = f"font-size:{size}px;font-weight:{weight};"
        return (
            f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="middle" dominant-baseline="middle" '
            f'style="{style}fill:#ffffff;stroke:#ffffff;stroke-width:4px;">{esc(text)}</text>'
            f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="middle" dominant-baseline="middle" '
            f'style="{style}fill:{fill};">{esc(text)}</text>'
        )

    def isa(self, cx, apex_y, base_y, half=36):
        pts = f"{cx},{apex_y} {cx - half},{base_y} {cx + half},{base_y}"
        self.nodes.append(
            f'<polygon points="{pts}" fill="#f8d0ce" stroke="#8a1f1a" stroke-width="1.6"/>'
        )
        self.nodes.append(self._text(cx, (apex_y + base_y) / 2 + 7, "d", size=15, weight="700", fill="#8a1f1a"))
        return (cx, apex_y), (cx - half, base_y), (cx + half, base_y)

    def render(self):
        bg = (
            f'<rect x="0" y="0" width="{self.w}" height="{self.h}" fill="#fbfcfe"/>'
        )
        body = "".join([bg] + self.under + self.links + self.nodes + self.labels)
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" '
            f'font-family="Segoe UI, Helvetica, Arial, sans-serif">{body}</svg>'
        )


def fig_especializacion():
    c = Canvas(760, 430)
    usuario = c.entity(380, 128, 200, 48, "USUARIO")
    for cx, text, kind in (
        (70, "id", "key"),
        (175, "identificador", "key"),
        (330, "nombre", "attr"),
        (520, "credencial", "attr"),
    ):
        a = c.attr(cx, 36, text, kind)
        c.link_attr(a, usuario)
    apex, left, right = c.isa(380, 188, 252, 40)
    c.raw_line(380, 152, apex[0], apex[1], sw=3.4)
    c.label(404, 172, "t")
    c.label(470, 214, "(total, disjunta)", size=11, fill="#8a1f1a", weight="600")

    admin = c.entity(90, 328, 160, 50, "ADMINISTRADOR")
    coord = c.entity(275, 328, 175, 50, "COORDINADOR\nACADÉMICO")
    est = c.entity(475, 328, 150, 50, "ESTUDIANTE")
    jefe = c.entity(665, 328, 165, 50, "JEFE DE\nDEPARTAMENTO")
    for target, origin in (
        (admin, left),
        (coord, (380, 252)),
        (est, (380, 252)),
        (jefe, right),
    ):
        x, y = target.border(origin[0], origin[1], pad=1)
        c.raw_line(origin[0], origin[1], x, y, sw=1.45)
    esp = c.attr(250, 398, "especialidad")
    edad = c.attr(430, 398, "edad")
    grupo = c.attr(545, 398, "grupo")
    c.link_attr(esp, coord)
    c.link_attr(edad, est)
    c.link_attr(grupo, est)
    return c.render()


def fig_oferta():
    c = Canvas(820, 300)
    programa = c.entity(230, 145, 175, 52, "PROGRAMA\nACADÉMICO")
    for cx, cy, text, kind in (
        (80, 48, "código", "key"),
        (210, 48, "nombre", "attr"),
        (380, 48, "plan de estudios", "attr"),
    ):
        a = c.attr(cx, cy, text, kind)
        c.link_attr(a, programa)
    cubre = c.rel(470, 145, 116, 76, "CUBRE")
    asignatura = c.entity(690, 145, 155, 46, "ASIGNATURA")
    c.connect(programa, cubre, ca="1", cb=None, ta=False, tb=False)
    c.connect(cubre, asignatura, ca=None, cb="N", ta=False, tb=True)
    for cx, cy, text, kind in (
        (620, 245, "id", "key"),
        (760, 245, "nombre", "attr"),
    ):
        a = c.attr(cx, cy, text, kind)
        c.link_attr(a, asignatura)
    return c.render()


def fig_personas_oferta():
    c = Canvas(820, 380)
    coord = c.entity(120, 88, 185, 52, "COORDINADOR\nACADÉMICO")
    autoriza = c.rel(340, 88, 124, 78, "AUTORIZA")
    programa = c.entity(590, 88, 175, 52, "PROGRAMA\nACADÉMICO")
    c.connect(coord, autoriza, ca="N", cb=None, ta=False, tb=False)
    c.connect(autoriza, programa, ca=None, cb="N", ta=False, tb=False)
    g = c.attr(250, 24, "puede generar")
    v = c.attr(420, 24, "puede validar")
    c.link_attr(g, autoriza)
    c.link_attr(v, autoriza)

    est = c.entity(160, 310, 155, 48, "ESTUDIANTE")
    edad = c.attr(70, 240, "edad")
    grupo = c.attr(250, 240, "grupo")
    c.link_attr(edad, est)
    c.link_attr(grupo, est)
    matricula = c.rel(420, 190, 124, 74, "MATRICULA")
    c.connect(est, matricula, ca="N", cb=None, ta=True, tb=False)
    c.connect(matricula, programa, ca=None, cb="N", ta=False, tb=False)
    return c.render()


def fig_bloque():
    c = Canvas(860, 400)
    coord = c.entity(95, 58, 170, 50, "COORDINADOR\nACADÉMICO")
    crea = c.rel(265, 58, 108, 68, "CREA")
    bloque = c.entity(455, 58, 175, 52, "BLOQUE DE\nCONTENIDO")
    aborda = c.rel(655, 58, 112, 70, "ABORDA")
    asig = c.entity(800, 168, 145, 46, "ASIGNATURA")
    c.connect(coord, crea, ca="1", cb=None, ta=False, tb=False)
    c.connect(crea, bloque, ca=None, cb="N", ta=False, tb=True)
    c.connect(bloque, aborda, ca="N", cb=None, ta=True, tb=False)
    c.connect(aborda, asig, ca=None, cb="1", ta=False, tb=False)
    attrs = [
        (70, 175, "id", "key"),
        (175, 175, "título", "attr"),
        (300, 175, "descripción", "attr"),
        (455, 175, "tipo de actividad", "attr"),
        (140, 245, "complejidad", "attr"),
        (300, 245, "duración", "attr"),
        (470, 245, "hash de duplicado", "derived"),
    ]
    for cx, cy, text, kind in attrs:
        a = c.attr(cx, cy, text, kind)
        c.link_attr(a, bloque)
    return c.render()


def fig_horario():
    c = Canvas(880, 560)
    programa = c.entity(470, 42, 175, 50, "PROGRAMA\nACADÉMICO")
    de = c.rel(470, 128, 100, 64, "DE")
    horario = c.entity(470, 250, 145, 48, "HORARIO")
    coord = c.entity(95, 250, 165, 52, "COORDINADOR\nACADÉMICO")
    genera = c.rel(275, 250, 112, 70, "GENERA")
    c.connect(programa, de, ca="1", cb=None, ta=False, tb=False)
    c.connect(de, horario, ca=None, cb="N", ta=False, tb=True)
    c.connect(coord, genera, ca="1", cb=None, ta=False, tb=False)
    c.connect(genera, horario, ca=None, cb="N", ta=False, tb=True)

    attrs = [
        (800, 36, "id", "key"),
        (760, 108, "fecha de creación", "attr"),
        (800, 168, "estado", "attr"),
        (800, 228, "semestre", "attr"),
        (720, 292, "generado auto.", "attr"),
        (700, 360, "equilibrio cumplido", "derived"),
    ]
    for cx, cy, text, kind in attrs:
        a = c.attr(cx, cy, text, kind)
        c.link_attr(a, horario)

    comp = c.attr(300, 390, "parámetros", "composite")
    c.link_attr(comp, horario)
    parts = [
        (70, 470, "prop. teórica"),
        (210, 470, "prop. práctica"),
        (370, 470, "prop. laboratorio"),
        (90, 520, "cobertura mínima"),
        (260, 520, "cant. de bloques"),
        (430, 520, "estrategia"),
    ]
    for cx, cy, text in parts:
        a = c.attr(cx, cy, text, "attr")
        c.link_attr(a, comp)
    return c.render()


def fig_valida_asigna():
    c = Canvas(1040, 720)
    horario = c.entity(910, 300, 150, 50, "HORARIO")

    coord = c.entity(110, 78, 175, 50, "COORDINADOR\nACADÉMICO")
    emite = c.rel(300, 78, 100, 62, "EMITE")
    validacion = c.entity(490, 78, 155, 46, "VALIDACIÓN")
    recae = c.rel(700, 78, 108, 62, "RECAE")
    c.connect(coord, emite)
    c.connect(emite, validacion, tb=True)
    c.connect(validacion, recae, ta=True)
    c.connect(recae, horario)
    c.label(205, 118, "1")
    c.label(395, 118, "N")
    c.label(595, 118, "N")
    c.label(800, 145, "1")
    for cx, cy, text, kind in (
        (250, 22, "id", "key"),
        (370, 22, "fecha", "attr"),
        (500, 22, "decisión", "attr"),
        (650, 22, "observaciones", "attr"),
    ):
        a = c.attr(cx, cy, text, kind)
        c.link_attr(a, validacion)

    jefe = c.entity(110, 250, 165, 50, "JEFE DE\nDEPARTAMENTO")
    dicta = c.rel(300, 250, 100, 62, "DICTA")
    aprobacion = c.entity(500, 250, 160, 46, "APROBACIÓN")
    resuelve = c.rel(710, 250, 120, 62, "RESUELVE")
    c.connect(jefe, dicta)
    c.connect(dicta, aprobacion, tb=True)
    c.connect(aprobacion, resuelve, ta=True)
    c.connect(resuelve, horario)
    c.label(205, 292, "1")
    c.label(400, 292, "N")
    c.label(610, 292, "N")
    c.label(830, 230, "1")

    sustituye = c.rel(710, 470, 130, 62, "SUSTITUYE")
    c.connect(aprobacion, sustituye)
    c.connect(sustituye, horario)
    c.label(600, 370, "N")
    c.label(830, 400, "1")
    for cx, cy, text, kind in (
        (150, 360, "id", "key"),
        (280, 360, "fecha", "attr"),
        (160, 420, "decisión", "attr"),
        (330, 420, "observaciones", "attr"),
    ):
        a = c.attr(cx, cy, text, kind)
        c.link_attr(a, aprobacion)

    est = c.entity(110, 630, 155, 48, "ESTUDIANTE")
    asignado = c.rel(360, 630, 128, 68, "ASIGNADO")
    c.connect(est, asignado)
    c.connect(asignado, horario)
    c.label(230, 590, "N")
    c.label(760, 560, "N")
    return c.render()


def fig_sesion():
    c = Canvas(1120, 530)
    horario = c.entity(390, 36, 145, 46, "HORARIO")
    incluye = c.rel(390, 118, 118, 68, "INCLUYE")
    sesion = c.entity(390, 230, 140, 48, "SESIÓN")
    c.connect(horario, incluye, ca="1", cb=None, ta=False, tb=False)
    c.connect(incluye, sesion, ca=None, cb="N", ta=False, tb=True)

    bloque = c.entity(70, 230, 150, 50, "BLOQUE DE\nCONTENIDO")
    imparte = c.rel(230, 230, 108, 66, "IMPARTE")
    c.connect(bloque, imparte, ca="1", cb=None, ta=False, tb=False)
    c.connect(imparte, sesion, ca=None, cb="N", ta=False, tb=True)

    ocupa = c.rel(640, 118, 112, 66, "OCUPA")
    franja = c.entity(880, 118, 170, 50, "FRANJA\nHORARIA")
    c.connect(sesion, ocupa, ca="N", cb=None, ta=True, tb=False)
    c.connect(ocupa, franja, ca=None, cb="1", ta=False, tb=False)

    usa = c.rel(640, 360, 100, 64, "USA")
    aula = c.entity(880, 360, 120, 46, "AULA")
    c.connect(sesion, usa, ca="N", cb=None, ta=True, tb=False)
    c.connect(usa, aula, ca=None, cb="1", ta=False, tb=False)

    sid = c.attr(390, 310, "id", "key")
    c.link_attr(sid, sesion)
    for cx, cy, text, kind in (
        (760, 36, "id", "key"),
        (960, 36, "día", "attr"),
        (700, 210, "hora de inicio", "attr"),
        (1040, 210, "hora de fin", "attr"),
    ):
        a = c.attr(cx, cy, text, kind)
        c.link_attr(a, franja)
    for cx, cy, text, kind in (
        (760, 450, "id", "key"),
        (900, 450, "nombre", "attr"),
        (760, 500, "edificio", "attr"),
        (940, 500, "capacidad", "attr"),
    ):
        a = c.attr(cx, cy, text, kind)
        c.link_attr(a, aula)
    return c.render()


def fig_asistencia():
    c = Canvas(960, 280)
    est = c.entity(90, 150, 155, 48, "ESTUDIANTE")
    registra = c.rel(270, 150, 120, 66, "REGISTRA")
    asist = c.entity(470, 150, 160, 48, "ASISTENCIA")
    ocurre = c.rel(680, 150, 110, 66, "OCURRE")
    sesion = c.entity(860, 150, 140, 48, "SESIÓN")
    c.connect(est, registra, ca="1", cb=None, ta=False, tb=False)
    c.connect(registra, asist, ca=None, cb="N", ta=False, tb=True)
    c.connect(asist, ocurre, ca="N", cb=None, ta=True, tb=False)
    c.connect(ocurre, sesion, ca=None, cb="1", ta=False, tb=False)
    for cx, cy, text, kind in (
        (360, 48, "id", "key"),
        (490, 48, "estado", "attr"),
        (620, 48, "fecha", "attr"),
    ):
        a = c.attr(cx, cy, text, kind)
        c.link_attr(a, asist)
    return c.render()


def fig_solicitud():
    c = Canvas(1000, 600)
    est = c.entity(80, 52, 150, 46, "ESTUDIANTE")
    solicita = c.rel(250, 52, 112, 64, "SOLICITA")
    solicitud = c.entity(530, 250, 190, 56, "SOLICITUD\nDE CAMBIO")
    c.connect(est, solicita)
    c.connect(solicita, solicitud, tb=True)
    c.label(165, 22, "1")
    c.label(370, 130, "N")

    coord = c.entity(80, 250, 150, 50, "COORDINADOR\nACADÉMICO")
    atiende = c.rel(250, 165, 112, 62, "ATIENDE")
    apoya = c.rel(250, 365, 112, 62, "APOYA")
    c.connect(coord, atiende)
    c.connect(atiende, solicitud, tb=True)
    c.connect(coord, apoya)
    c.connect(apoya, solicitud)
    c.label(160, 195, "1")
    c.label(400, 190, "N")
    c.label(160, 340, "1")
    c.label(400, 330, "N")

    origen = c.rel(780, 125, 112, 62, "ORIGEN")
    destino = c.rel(780, 385, 112, 62, "DESTINO")
    horario = c.entity(910, 255, 140, 46, "HORARIO")
    c.connect(solicitud, origen, ta=True)
    c.connect(origen, horario)
    c.connect(solicitud, destino)
    c.connect(destino, horario)
    c.label(670, 155, "N")
    c.label(870, 155, "1")
    c.label(670, 355, "N")
    c.label(870, 365, "1")

    for cx, cy, text, kind in (
        (400, 490, "id", "key"),
        (510, 490, "motivo", "attr"),
        (620, 490, "estado", "attr"),
        (390, 550, "fecha solicitud", "attr"),
        (540, 550, "fecha resolución", "attr"),
        (690, 550, "resultado", "attr"),
    ):
        a = c.attr(cx, cy, text, kind)
        c.link_attr(a, solicitud)
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
    bloque = dim(900, 330, 230, 64, "dim_bloque", "título, asignatura\ncomplejidad, creador")
    c.connect(tiempo, asist)
    c.connect(grupo, asist)
    c.connect(bloque, asist)

    cambio = fact(
        520, 530, 420, 88, "fact_solicitud_cambio",
        "medida: solicitudes\ndegeneradas: estudiante · programa · resultado",
    )
    c.connect(tiempo, cambio)
    c.connect(grupo, cambio)
    return c.render()


FIGURES = [
    ("fig-isa", "Figura 1. Especialización total y disjunta de usuario.", fig_especializacion),
    ("fig-oferta", "Figura 2. Programa académico y asignaturas que cubre (1:N).", fig_oferta),
    ("fig-personas", "Figura 3. Autorización del coordinador y matrícula. El grupo es atributo del estudiante.", fig_personas_oferta),
    ("fig-bloque", "Figura 4. Banco de bloques de contenido.", fig_bloque),
    ("fig-horario", "Figura 5. Horario, generación y parámetros.", fig_horario),
    ("fig-valida", "Figura 6. Validación y aprobación como entidades, asignación N:N y horario sucesor.", fig_valida_asigna),
    ("fig-sesion", "Figura 7. Sesión: franja de catálogo y aula, las dos obligatorias.", fig_sesion),
    ("fig-asiste", "Figura 8. Asistencia como entidad: una fila por estudiante, sesión y fecha.", fig_asistencia),
    ("fig-solicitud", "Figura 9. Solicitud de cambio de horario.", fig_solicitud),
    ("fig-estrella", "Figura 10. Almacén analítico en esquema estrella, independiente del modelo operacional.", fig_estrella),
]
