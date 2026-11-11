# Acuario de agentes

Demo de escritorio en Python basada en `FishAgent.java`, `HostAgent.java` y `MainFrame.java`. Veinte peces comparten un acuario 2D. Selecciona uno para relacionar lo que ves en pantalla con las reglas de `agentes.py`.

## Cómo ejecutarla

1. Descomprime el ZIP y abre una terminal en la carpeta que contiene `demo.py`.
2. Ejecuta el comando de tu sistema.

| Sistema | Comando |
| --- | --- |
| Windows | `py -3 demo.py` |
| macOS o Linux | `python3 demo.py` |

Usa Python 3.9 o posterior con Tkinter. La demo se ejecuta sin conexión y utiliza únicamente la biblioteca estándar. Si tu instalación de Linux viene sin Tkinter, en Debian o Ubuntu puedes instalarlo con `sudo apt install python3-tk`. Para comprobar que Tk puede abrir una ventana, ejecuta `python3 -m tkinter` (en Windows, `py -3 -m tkinter`).

## Primer minuto en clase

La ventana se abre en pausa con el **pez 01** seleccionado. El anillo y el rastro marcan el pez que estás siguiendo. Su color, orientación y panel de inspección muestran la **próxima acción**, calculada con la posición actual. Cada clic en **Un paso** ejecuta esa acción y actualiza el panel. **Último movimiento observado** muestra las dos posiciones del desplazamiento que acabas de ver.

El pez 01 comienza en `(588, 100)`, mide 20 unidades y recorre `250 // 20 = 12` unidades por paso. El umbral derecho empieza en 600.

| Paso | Movimiento que se acaba de ejecutar | Posición resultante | Próxima acción |
| --- | --- | --- | --- |
| 0 | Posición inicial | (588, 100) | Vigilar → |
| 1 | Avanza 12 a la derecha | (600, 100) | Vigilar → |
| 2 | Avanza otros 12 a la derecha | (612, 100) | Bajar ↓ |
| 3 | Desciende 12 | (612, 112) | Bajar ↓ |

Detente en el paso 1 y pide a los estudiantes que predigan el siguiente movimiento. El giro se activa con `x > 600`. En la igualdad, el pez aún vigila. Después de observar el giro, pulsa **Reproducir** para ver cómo los demás peces recorren el circuito.

## Las reglas del pez

El origen de coordenadas está arriba a la izquierda. `x` crece hacia la derecha e `y` hacia abajo. Las líneas verticales indican los umbrales izquierdo y derecho, y las horizontales separan las tres zonas de profundidad.

| Zona | Condición horizontal | Estado y movimiento |
| --- | --- | --- |
| Superficie · y < 130 | x ≤ umbral derecho | Vigilar → aumenta x |
| Superficie · y < 130 | x > umbral derecho | Bajar ↓ aumenta y |
| Zona media · 130 ≤ y ≤ 330 | x < umbral izquierdo | Subir ↑ disminuye y |
| Zona media · 130 ≤ y ≤ 330 | x ≥ umbral izquierdo | Bajar ↓ aumenta y |
| Fondo · y > 330 | x < umbral izquierdo | Subir ↑ disminuye y |
| Fondo · y > 330 | x ≥ umbral izquierdo | Comer ← disminuye x |

**Comer** es el nombre que da el Java al recorrido hacia la izquierda en el fondo. Todos los estados usan la misma regla de velocidad, `250 // tamaño`. Un pez de tamaño 15 avanza 16 unidades por paso y uno de tamaño 25 avanza 10.

## Qué coordina el anfitrión

En cada paso el anfitrión recorre la lista. Cada pez observa su propia posición y los umbrales compartidos, elige un estado y nada. El circuito colectivo aparece cuando muchos peces aplican esas reglas. Estas tres líneas de `Anfitrion.avanzar()` ejecutan el ciclo.

```python
for pez in self.peces:
    decision = pez.decidir(self.izquierda, self.derecha)
    pez.nadar(decision.estado)
```

El reloj programa un paso cada 100 ms en reproducción. Con **Mover umbrales** activo, al terminar cada décimo paso el anfitrión desplaza ambos umbrales 5 unidades. Mantiene 400 unidades entre ellos e invierte el sentido al alcanzar un desplazamiento de 60 unidades a cada lado de su posición inicial.

## Controles

| Control | Efecto |
| --- | --- |
| Reproducir / Pausar · tecla P | Inicia o detiene el reloj. |
| Un paso · tecla N | Ejecuta exactamente un paso y deja el acuario en pausa. |
| Clic en un pez / Siguiente | Selecciona el agente cuyo rastro y decisión quieres ver. |
| Mostrar guías | Muestra u oculta las líneas y sus coordenadas. |
| Mover umbrales | Activa el desplazamiento periódico o congela los límites donde están. |
| Reiniciar | Recupera la misma distribución inicial, selecciona el pez 01 y deja la demo en pausa. Conserva la configuración de las casillas. |

La sección **Estados del acuario** cuenta cuántos peces tienen prevista cada acción. Sus cuatro cifras suman 20 en todos los pasos.

## Del Java al Python

| Referencia Java | Equivalente en el proyecto |
| --- | --- |
| `FishAgent.definirStatus()` | `Pez.decidir()`, en `agentes.py`. Devuelve el estado y la condición que aparece en el inspector. |
| `FishAgent.nadar()` | `Pez.nadar()`, en `agentes.py`. Aplica la dirección y la velocidad. |
| `HostAgent` y sus temporizadores | `Anfitrion.avanzar()` coordina a los peces y actualiza los umbrales. La ventana lo llama mediante el reloj de Tk. |
| `MainFrame` y su referencia a `AmbientePanel` | `demo.py` construye la ventana y `escena.py` dibuja el acuario. |

### Adaptaciones para la demostración

El ejemplo Java configura 20 000 peces. La demo usa 20 para poder seguirlos individualmente. La vista 2D usa un mundo de 800 × 460 unidades con umbrales ajustados para proyectar el circuito completo. Los peces empiezan repartidos entre los cuatro movimientos y el reinicio reproduce las mismas posiciones. El desplazamiento de los umbrales es de ida y vuelta para mantenerlos visibles. El panel de dibujo referenciado por el Java se recreó con Tkinter. Cada pez es un objeto Python que el reloj actualiza de forma secuencial.
