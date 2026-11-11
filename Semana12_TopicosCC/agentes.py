"""Las decisiones de los peces y el reloj del acuario. Este módulo es Python puro."""
from dataclasses import dataclass
from enum import Enum
from random import Random


# Coordenadas del mundo. La profundidad y aumenta hacia abajo.
ANCHO, ALTO = 800, 460
SUPERFICIE, FONDO = 130, 330
IZQUIERDA, DERECHA = 200, 600
INTERVALO_MS = 100


class Estado(Enum):
    # Cada valor es el vector (dx, dy) de un solo movimiento.
    VIGILAR = (1, 0)
    COMER = (-1, 0)
    SUBIR = (0, -1)
    BAJAR = (0, 1)


@dataclass(frozen=True)
class Decision:
    estado: Estado
    zona: str
    condicion: str


@dataclass
class Pez:
    numero: int
    x: int
    y: int
    tamano: int

    @property
    def velocidad(self):
        """Distancia por paso. Conserva la división entera del Java."""
        return 250 // self.tamano

    def decidir(self, izquierda, derecha):
        """Observa su posición. Cada retorno explica exactamente la regla elegida."""
        if self.y < SUPERFICIE:
            zona = f"Superficie  ·  y < {SUPERFICIE}"
            if self.x > derecha:
                return Decision(Estado.BAJAR, zona, f"x = {self.x} > {derecha}")
            return Decision(Estado.VIGILAR, zona, f"x = {self.x} ≤ {derecha}")

        if self.y > FONDO:
            zona = f"Fondo  ·  y > {FONDO}"
            if self.x < izquierda:
                return Decision(Estado.SUBIR, zona, f"x = {self.x} < {izquierda}")
            return Decision(Estado.COMER, zona, f"x = {self.x} ≥ {izquierda}")

        zona = f"Zona media  ·  {SUPERFICIE} ≤ y ≤ {FONDO}"
        if self.x < izquierda:
            return Decision(Estado.SUBIR, zona, f"x = {self.x} < {izquierda}")
        return Decision(Estado.BAJAR, zona, f"x = {self.x} ≥ {izquierda}")

    def nadar(self, estado):
        """Una decisión cambia una sola coordenada."""
        dx, dy = estado.value
        self.x += dx * self.velocidad
        self.y += dy * self.velocidad


def crear_peces():
    """Veinte peces en las cuatro zonas de movimiento, listos para observar."""
    azar = Random(7)
    peces = []
    for i in range(20):
        grupo, lado = divmod(i, 4)
        if lado == 0:  # Superficie
            x, y = 585 - 85 * grupo, azar.randint(72, 117)
        elif lado == 1:  # Columna de descenso
            x, y = azar.randint(616, 673), 143 + 40 * grupo
        elif lado == 2:  # Fondo
            x, y = 561 - 83 * grupo, azar.randint(346, 390)
        else:  # Columna de ascenso
            x, y = azar.randint(142, 191), 308 - 39 * grupo
        peces.append(Pez(i + 1, x, y, azar.randint(15, 26)))

    # Este pez permite reproducir a mano los primeros tres pasos.
    peces[0] = Pez(numero=1, x=588, y=100, tamano=20)
    return peces


class Anfitrion:
    """Equivale a HostAgent. Comparte los umbrales y marca los pasos."""
    def __init__(self):
        self.peces = crear_peces()
        self.turno = 0
        self.izquierda = IZQUIERDA
        self.derecha = DERECHA
        self.desplazamiento = 5

    def avanzar(self, mover_umbrales=True):
        # Todos observan los mismos umbrales durante este paso.
        for pez in self.peces:
            decision = pez.decidir(self.izquierda, self.derecha)
            pez.nadar(decision.estado)

        self.turno += 1
        if mover_umbrales and self.turno % 10 == 0:
            self.izquierda += self.desplazamiento
            self.derecha += self.desplazamiento
            # La ida y la vuelta mantienen el circuito dentro de la ventana.
            if abs(self.izquierda - IZQUIERDA) >= 60:
                self.desplazamiento *= -1
