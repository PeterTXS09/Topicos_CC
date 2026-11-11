"""Vista 2D. Recibe las decisiones ya calculadas y las dibuja en un Canvas."""
import math
import tkinter as tk
from typing import NamedTuple

from agentes import ALTO, ANCHO, FONDO, SUPERFICIE, Estado


class Paleta(NamedTuple):
    flecha: str
    cuerpo: str
    aleta: str
    texto: str
    fondo: str


COLORES = {
    Estado.VIGILAR: Paleta("→", "#86ECD6", "#409F92", "#116453", "#DCF4EB"),
    Estado.COMER:   Paleta("←", "#FFD580", "#CD9650", "#785310", "#FFF0D0"),
    Estado.SUBIR:   Paleta("↑", "#B8BCFF", "#7D84C0", "#514B91", "#EDEBFD"),
    Estado.BAJAR:   Paleta("↓", "#FFA38E", "#C56F68", "#934739", "#FFE8DF"),
}


class Escena(tk.Canvas):
    def __init__(self, padre, seleccionar, fuente):
        super().__init__(padre, bg="#123947", width=1, height=1,
                         highlightthickness=0, cursor="crosshair")
        self.seleccionar = seleccionar
        self.fuente = fuente
        self.medidas = None
        self.guias_anteriores = None
        self.blancos = []
        self.bind("<Button-1>", self._elegir_pez)

    def _punto(self, x, y):
        return x * self.sx, y * self.sy

    def _puntos(self, puntos):
        return [v for punto in puntos for v in self._punto(*punto)]

    def _elegir_pez(self, evento):
        # Tolerancia generosa para poder seleccionar también los peces pequeños.
        candidatos = []
        for numero, x, y, radio in self.blancos:
            distancia = math.hypot(evento.x - x, evento.y - y)
            if distancia <= radio:
                candidatos.append((distancia, numero))
        if candidatos:
            self.seleccionar(min(candidatos)[1])

    def _fondo(self):
        """El paisaje es estático. Se reconstruye al redimensionar la ventana."""
        self.delete("all")
        claro, oscuro = (37, 110, 118), (9, 42, 56)
        for fila in range(60):
            t = fila / 59
            rgb = tuple(round(a + (b - a) * t) for a, b in zip(claro, oscuro))
            color = "#%02x%02x%02x" % rgb
            self.create_rectangle(*self._punto(0, fila * ALTO / 60),
                                  *self._punto(ANCHO, (fila + 1) * ALTO / 60 + 1),
                                  fill=color, outline="")
        # Ondas superficiales y pequeñas burbujas sirven de referencias de profundidad.
        for nivel in (8, 16, 25):
            onda = [(x, nivel + 3 * math.sin(x / 42 + nivel / 6))
                    for x in range(-20, ANCHO + 21, 12)]
            self.create_line(self._puntos(onda), fill="#388089", smooth=True)
        for x, y, r in [(48, 94, 3), (53, 77, 1.6), (91, 246, 2), (80, 263, 4),
                        (700, 210, 3), (707, 192, 1.8), (746, 303, 4), (738, 320, 2),
                        (317, 272, 2), (320, 262, 1), (426, 80, 2), (462, 299, 1.5)]:
            self.create_oval(*self._punto(x-r, y-r), *self._punto(x+r, y+r),
                             outline="#46868B")
        # Dos perfiles de fondo y algas que quedan fuera de la pista de los peces.
        for nivel, amplitud, fase, color in [(415, 11, 0, "#19515A"),
                                             (438, 8, 2, "#103B46")]:
            cresta = [(x, nivel + amplitud * math.sin(x / 97 + fase)
                       + 4 * math.cos(x / 41)) for x in range(-20, ANCHO + 21, 12)]
            suelo = cresta + [(ANCHO + 20, ALTO), (-20, ALTO)]
            self.create_polygon(self._puntos(suelo), fill=color, outline="")
        for x, altura, giro in [(38, 65, 1), (60, 43, -1), (84, 31, 1),
                                 (719, 44, 1), (749, 68, -1), (774, 48, 1)]:
            for i in (-1, 0, 1):
                punta = x + 14 * i * giro
                h = altura * (1 - abs(i) * .23)
                hoja = [(x, 442), (x + 8 * giro + 5 * i, 442 - h * .42),
                        (punta, 442 - h), (punta + 4, 442 - h * .54), (x + 3, 442)]
                self.create_polygon(self._puntos(hoja), fill="#27626A", smooth=True)

    def _guias(self, visible, izquierda, derecha):
        self.delete("guia")
        if not visible:
            return
        letra = (self.fuente, -11, "bold")
        for x in (izquierda, derecha):
            self.create_line(*self._punto(x, 36), *self._punto(x, 411),
                             fill="#699C9F", dash=(3, 6), tags="guia")
            self.create_text(*self._punto(x, 24), text=f"x = {x}", font=letra,
                             fill="#E2F3E9", tags="guia")
        for y in (SUPERFICIE, FONDO):
            self.create_line(*self._punto(15, y), *self._punto(ANCHO - 15, y),
                             fill="#79A5A7", dash=(5, 5), tags="guia")
            self.create_text(*self._punto(ANCHO - 16, y - 5), text=f"y = {y}",
                             font=letra, fill="#DBEEEB", anchor="se", tags="guia")
        for y, texto in [(46, "SUPERFICIE"), (216, "ZONA MEDIA"), (358, "FONDO")]:
            self.create_text(*self._punto(17, y), text=texto, anchor="w",
                             font=(self.fuente, -10, "bold"), fill="#ABD4D0", tags="guia")

    def _pez(self, pez, estado, turno, elegido):
        x, y = self._punto(pez.x, pez.y)
        escala = pez.tamano * min(self.sx, self.sy)
        dx, dy = estado.value
        paleta = COLORES[estado]

        def punto(u, v):
            # u apunta hacia la cabeza. v es perpendicular al movimiento.
            return x + escala * (dx*u - dy*v), y + escala * (dy*u + dx*v)

        def forma(puntos, color, suave=True):
            coords = [v for par in puntos for v in punto(*par)]
            self.create_polygon(coords, fill=color, outline="", smooth=suave, tags="movil")

        radio = 1.45 * escala + 3
        self.blancos.append((pez.numero, x, y, radio))
        if elegido:
            self.create_oval(x-radio, y-radio, x+radio, y+radio, outline="#F0FAE8",
                             width=2, dash=(5, 4), tags="movil")
        aleteo = .08 * math.sin(turno * .8 + pez.numero)
        forma([(-.52, 0), (-1.13, -.41 + aleteo), (-1.07, .43 + aleteo)],
              paleta.aleta, False)
        forma([(-.41, -.18), (-.21, -.60), (.17, -.29)], paleta.aleta, False)
        forma([(-.71, 0), (-.5, -.27), (-.07, -.38), (.44, -.34), (.84, -.13),
               (.92, 0), (.72, .18), (.27, .34), (-.25, .31), (-.55, .14)], paleta.cuerpo)
        forma([(-.08, .02), (.16, .10), (-.20, .28)], paleta.aleta, False)
        ex, ey = punto(.55, -.10)
        er = max(1.6, escala * .115)
        self.create_oval(ex-er, ey-er, ex+er, ey+er, fill="#F2F8E8", outline="", tags="movil")
        self.create_oval(ex-er*.55, ey-er*.55, ex+er*.55, ey+er*.55,
                         fill="#153944", outline="", tags="movil")
        if elegido:
            self.create_text(x+radio, y-radio, text=f"{pez.numero:02}", anchor="sw",
                             font=(self.fuente, -11, "bold"), fill="#F1FAEB", tags="movil")

    def dibujar(self, anfitrion, decisiones, seleccionado, rastro, guias):
        medidas = self.winfo_width(), self.winfo_height()
        if min(medidas) < 10:
            return
        if medidas != self.medidas:
            self.medidas = medidas
            self.sx, self.sy = medidas[0] / ANCHO, medidas[1] / ALTO
            self._fondo()
            self.guias_anteriores = None

        limites = (guias, anfitrion.izquierda, anfitrion.derecha)
        if limites != self.guias_anteriores:
            self._guias(*limites)
            self.guias_anteriores = limites

        self.delete("movil")
        self.blancos.clear()
        if len(rastro) > 1:
            self.create_line(self._puntos(rastro), fill="#C5E4D5",
                             width=2, dash=(2, 4), tags="movil")
        # El seleccionado se dibuja al final para que su anillo siga visible.
        ordenados = sorted(anfitrion.peces, key=lambda pez: pez.numero == seleccionado)
        for pez in ordenados:
            self._pez(pez, decisiones[pez.numero].estado, anfitrion.turno,
                      pez.numero == seleccionado)
