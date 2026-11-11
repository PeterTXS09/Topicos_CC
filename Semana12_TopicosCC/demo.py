"""Punto de entrada. Ejecutar con: python demo.py"""
from collections import Counter, deque

try:
    import tkinter as tk
    from tkinter import font, ttk
except ImportError:
    raise SystemExit("Se necesita Python con Tkinter. Consulta LEEME.md para instalarlo.")

from agentes import Anfitrion, Estado, INTERVALO_MS
from escena import COLORES, Escena


PAPEL, TARJETA = "#F3F5EF", "#FCFDF9"
TINTA, GRIS, BORDE = "#193836", "#4D6862", "#D3DFD5"
VERDE = "#0B645B"


class Demo:
    def __init__(self, raiz):
        self.raiz = raiz
        raiz.title("Acuario de agentes")
        ancho = min(1140, raiz.winfo_screenwidth() - 32)
        alto = min(655, raiz.winfo_screenheight() - 72)
        raiz.geometry(f"{ancho}x{alto}")
        raiz.minsize(min(ancho, 770), min(alto, 540))
        raiz.configure(bg=PAPEL)

        disponibles = set(font.families(raiz))
        fuentes = ("Inter", "Segoe UI", "Helvetica Neue", "DejaVu Sans", "Arial")
        self.fuente = next((nombre for nombre in fuentes if nombre in disponibles), "Helvetica")
        # Algunos servidores X11 solo ofrecen fuentes de mapa de bits.
        self.simbolos = self.fuente in disponibles
        self.mono = font.nametofont("TkFixedFont").actual("family")
        self.anfitrion = Anfitrion()
        self.seleccionado = 1
        self.rastro = deque(maxlen=22)
        self.en_marcha = False
        self.temporizador = None
        self.guias = tk.BooleanVar(value=True)
        self.mover = tk.BooleanVar(value=True)

        self._estilos()
        self._interfaz()
        self.seleccionar(1)
        self.escena.bind("<Configure>", lambda evento: self.dibujar())
        raiz.bind("<KeyPress-p>", lambda evento: self.alternar())
        raiz.bind("<KeyPress-n>", lambda evento: self.un_paso())
        raiz.protocol("WM_DELETE_WINDOW", self.cerrar)

    def _estilos(self):
        estilo = ttk.Style(self.raiz)
        estilo.theme_use("clam")
        for nombre, fondo, tinta, activo in [
            ("Principal", VERDE, "#FFFFFF", "#084E47"),
            ("Control", "#E8EEE7", TINTA, "#D8E5DD"),
            ("Compacto", "#EDF2EB", VERDE, "#DCEAE1"),
        ]:
            clave = nombre + ".TButton"
            compacto = nombre == "Compacto"
            estilo.configure(clave, font=(self.fuente, -12 if compacto else -14, "bold"),
                             background=fondo, foreground=tinta, borderwidth=0, relief="flat",
                             padding=(10, 5) if compacto else (14, 9), focusthickness=1)
            estilo.map(clave, background=[("pressed", activo), ("active", activo)])
        estilo.configure("Vista.TCheckbutton", background=TARJETA, foreground=GRIS,
                         font=(self.fuente, -13), indicatorbackground="#FFFFFF",
                         indicatormargin=(0, 0, 6, 0))
        estilo.map("Vista.TCheckbutton", background=[("active", TARJETA)],
                   indicatorbackground=[("selected", "#B3E5D7")])

    def _texto(self, padre, texto, tamano, color=TINTA, negrita=False, mono=False):
        familia = self.mono if mono else self.fuente
        return tk.Label(padre, text=texto, bg=padre["bg"], fg=color, bd=0, padx=0,
                        pady=0, anchor="w", font=(familia, -tamano, "bold" if negrita else "normal"))

    def _tarjeta(self, padre):
        return tk.Frame(padre, bg=TARJETA, highlightthickness=1, highlightbackground=BORDE)

    def _interfaz(self):
        cab = tk.Frame(self.raiz, bg=PAPEL)
        cab.pack(fill="x", padx=22, pady=(17, 15))
        marca = tk.Canvas(cab, width=48, height=48, bg=PAPEL, highlightthickness=0)
        marca.pack(side="left", padx=(0, 12))
        marca.create_oval(1, 1, 47, 47, fill=VERDE, outline="")
        marca.create_polygon(9, 19, 18, 24, 9, 29, fill="#A5E6CC", outline="")
        marca.create_polygon(15, 24, 22, 16, 33, 19, 38, 24, 30, 29, 21, 30,
                             fill="#D5F4D9", outline="", smooth=True)
        marca.create_oval(29, 21, 32, 24, fill=VERDE, outline="")
        titulo = tk.Frame(cab, bg=PAPEL)
        titulo.pack(side="left")
        self._texto(titulo, "Acuario de agentes", 28, negrita=True).pack(anchor="w")
        self._texto(titulo, "Selecciona un pez para ver cómo decide su próximo movimiento.",
                    14, GRIS).pack(anchor="w", pady=(2, 0))
        self.reloj = self._texto(cab, "", 14, GRIS, mono=True)
        self.reloj.pack(side="right")
        tk.Frame(cab, bg=BORDE, width=1, height=24).pack(side="right", padx=13)
        self.modo = self._texto(cab, "", 13, VERDE, negrita=True)
        self.modo.pack(side="right")

        cuerpo = tk.Frame(self.raiz, bg=PAPEL)
        cuerpo.pack(fill="both", expand=True, padx=22, pady=(0, 18))
        cuerpo.columnconfigure(0, weight=1)
        cuerpo.rowconfigure(0, weight=1)
        izquierda = self._tarjeta(cuerpo)
        izquierda.grid(row=0, column=0, sticky="nsew")
        self.escena = Escena(izquierda, self.seleccionar, self.fuente)
        self.escena.pack(side="top", fill="both", expand=True)
        self._controles(izquierda)

        lateral = self._tarjeta(cuerpo)
        lateral.configure(width=278)
        lateral.pack_propagate(False)
        lateral.grid(row=0, column=1, padx=(14, 0), sticky="nsew")
        self._inspector(lateral)

    def _controles(self, padre):
        botones = tk.Frame(padre, bg=TARJETA)
        botones.pack(fill="x", padx=14, pady=(13, 8))
        self.play = ttk.Button(botones, text="Reproducir", width=10,
                               command=self.alternar, style="Principal.TButton")
        self.play.pack(side="left")
        self.boton_paso = ttk.Button(botones, text="Un paso", command=self.un_paso,
                                     style="Control.TButton")
        self.boton_paso.pack(side="left", padx=7)
        self.boton_reinicio = ttk.Button(botones, text="Reiniciar", command=self.reiniciar,
                                         style="Control.TButton")
        self.boton_reinicio.pack(side="left")
        opciones = tk.Frame(padre, bg=TARJETA)
        opciones.pack(fill="x", padx=14, pady=(0, 12))
        ttk.Checkbutton(opciones, text="Mostrar guías", variable=self.guias,
                        command=self.dibujar, style="Vista.TCheckbutton").pack(side="left")
        ttk.Checkbutton(opciones, text="Mover umbrales", variable=self.mover,
                        style="Vista.TCheckbutton").pack(side="left", padx=(18, 0))

    def _inspector(self, panel):
        interior = tk.Frame(panel, bg=TARJETA)
        interior.pack(fill="both", expand=True, padx=16, pady=16)
        self._texto(interior, "PEZ SELECCIONADO", 11, GRIS, True).pack(anchor="w")
        fila = tk.Frame(interior, bg=TARJETA)
        fila.pack(fill="x", pady=(3, 12))
        self.nombre = self._texto(fila, "", 26, negrita=True)
        self.nombre.pack(side="left")
        self.boton_siguiente = ttk.Button(fila, text="Siguiente", style="Compacto.TButton",
                                           command=self.siguiente_pez)
        self.boton_siguiente.pack(side="right", padx=(13, 0))

        self.decision = tk.Frame(interior, bg="#DCF4EB", padx=12, pady=10, width=244)
        self.decision.pack(fill="x")
        self.rotulo = self._texto(self.decision, "Próxima acción", 12, negrita=True)
        self.accion = self._texto(self.decision, "", 25, negrita=True)
        self.zona = self._texto(self.decision, "", 13)
        self.regla = self._texto(self.decision, "", 14, mono=True)
        for etiqueta, margen in [(self.rotulo, 0), (self.accion, 2),
                                 (self.zona, 6), (self.regla, 3)]:
            etiqueta.pack(anchor="w", pady=(margen, 0))

        self.datos = {}
        for clave in ("Posición (x, y)", "Tamaño", "Velocidad"):
            linea = tk.Frame(interior, bg=TARJETA)
            linea.pack(fill="x", pady=(12 if not self.datos else 4, 0))
            self._texto(linea, clave, 13, GRIS).pack(side="left")
            etiqueta = self._texto(linea, "", 14, mono=True)
            etiqueta.pack(side="right")
            self.datos[clave] = etiqueta

        tk.Frame(interior, height=1, bg=BORDE).pack(fill="x", pady=(14, 12))
        fila = tk.Frame(interior, bg=TARJETA)
        fila.pack(fill="x")
        self._texto(fila, "Estados del acuario", 16, negrita=True).pack(side="left")
        self._texto(fila, f"{len(self.anfitrion.peces)} peces", 12, GRIS).pack(side="right", padx=(12, 0))
        tabla = tk.Frame(interior, bg=TARJETA)
        tabla.pack(fill="x", pady=(8, 0))
        self.conteos = {}
        for indice, estado in enumerate(Estado):
            fila, columna = divmod(indice, 2)
            paleta = COLORES[estado]
            celda = tk.Frame(tabla, bg=paleta.fondo, padx=7, pady=6)
            celda.grid(row=fila, column=columna, sticky="ew",
                       padx=(0, 3) if columna == 0 else (3, 0), pady=3)
            tabla.columnconfigure(columna, weight=1, uniform="estados")
            nombre = self._nombre_estado(estado)
            self._texto(celda, nombre, 12, paleta.texto, True).pack(side="left")
            total = self._texto(celda, "", 14, paleta.texto, True, True)
            total.pack(side="right", padx=(8, 0))
            self.conteos[estado] = total

        pie = tk.Frame(interior, bg=TARJETA)
        pie.pack(side="bottom", fill="x", pady=(5, 0))
        self._texto(pie, "Último movimiento observado", 12, GRIS, True).pack(anchor="w")
        self.ultimo = self._texto(pie, "", 12)
        self.ultimo.pack(anchor="w", pady=(3, 0))

    def _nombre_estado(self, estado):
        nombre = estado.name.capitalize()
        return f"{COLORES[estado].flecha}  {nombre}" if self.simbolos else nombre

    def seleccionar(self, numero):
        self.seleccionado = numero
        self.rastro.clear()
        pez = self.anfitrion.peces[numero - 1]
        self.rastro.append((pez.x, pez.y))
        self.actualizar()

    def siguiente_pez(self):
        self.seleccionar(self.seleccionado % len(self.anfitrion.peces) + 1)

    def actualizar(self):
        anfitrion = self.anfitrion
        self.decisiones = {pez.numero: pez.decidir(anfitrion.izquierda, anfitrion.derecha)
                           for pez in anfitrion.peces}
        pez = anfitrion.peces[self.seleccionado - 1]
        proxima = self.decisiones[pez.numero]
        paleta = COLORES[proxima.estado]
        self.nombre.config(text=f"Pez {pez.numero:02}")
        self.decision.config(bg=paleta.fondo)
        for etiqueta in (self.rotulo, self.accion, self.zona, self.regla):
            etiqueta.config(bg=paleta.fondo, fg=paleta.texto)
        self.accion.config(text=self._nombre_estado(proxima.estado))
        for etiqueta, texto in ((self.zona, proxima.zona), (self.regla, proxima.condicion)):
            if not self.simbolos:
                texto = texto.replace("≤", "<=").replace("≥", ">=")
            etiqueta.config(text=texto)
        self.datos["Posición (x, y)"].config(text=f"({pez.x}, {pez.y})")
        self.datos["Tamaño"].config(text=f"{pez.tamano} u")
        self.datos["Velocidad"].config(text=f"{pez.velocidad} u/paso")
        ultimo = "Avanza un paso para verlo."
        if len(self.rastro) > 1:
            flecha = "→" if self.simbolos else "->"
            ultimo = f"{self.rastro[-2]}  {flecha}  {self.rastro[-1]}"
        self.ultimo.config(text=ultimo)
        conteo = Counter(d.estado for d in self.decisiones.values())
        for estado, etiqueta in self.conteos.items():
            etiqueta.config(text=str(conteo[estado]))
        self.modo.config(text="●  En marcha" if self.en_marcha else "●  En pausa")
        self.reloj.config(text=f"Paso {anfitrion.turno:03}")
        self.play.config(text="Pausar" if self.en_marcha else "Reproducir")
        self.dibujar()

    def dibujar(self):
        self.escena.dibujar(self.anfitrion, self.decisiones, self.seleccionado,
                            self.rastro, self.guias.get())

    def avanzar(self):
        self.anfitrion.avanzar(self.mover.get())
        pez = self.anfitrion.peces[self.seleccionado - 1]
        self.rastro.append((pez.x, pez.y))
        self.actualizar()

    def _pulso(self):
        self.temporizador = None
        self.avanzar()
        self.temporizador = self.raiz.after(INTERVALO_MS, self._pulso)

    def pausar(self):
        self.en_marcha = False
        if self.temporizador is not None:
            self.raiz.after_cancel(self.temporizador)
            self.temporizador = None

    def alternar(self):
        if self.en_marcha:
            self.pausar()
        else:
            self.en_marcha = True
            self.temporizador = self.raiz.after(INTERVALO_MS, self._pulso)
        self.actualizar()

    def un_paso(self):
        self.pausar()
        self.avanzar()

    def reiniciar(self):
        self.pausar()
        self.anfitrion = Anfitrion()
        self.seleccionar(1)

    def cerrar(self):
        self.pausar()
        self.raiz.destroy()


if __name__ == "__main__":
    try:
        ventana = tk.Tk()
    except tk.TclError as error:
        raise SystemExit(f"Abre la demo en una sesión de escritorio con Tkinter.\n{error}")
    aplicacion = Demo(ventana)
    ventana.mainloop()
