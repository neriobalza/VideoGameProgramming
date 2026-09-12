# Breakout

Videojuego desarrollado con Python, pygame y gale. El jugador mueve una paleta
horizontal para mantener las pelotas dentro de la cancha y destruir todos los
ladrillos del nivel.

## Controles

- Flechas izquierda y derecha: mover la paleta.
- Enter: sacar la pelota y confirmar opciones de los menús.
- Espacio: lanzar las pelotas capturadas; si no hay ninguna, pausar o reanudar.
- F: disparar los cañones cuando estén disponibles.
- Escape: salir del juego.

## Power-ups

- `TwoMoreBall`: añade dos pelotas a la partida.
- `CatchBall`: permite que la paleta capture pelotas durante 5 segundos. Las
  pelotas capturadas se lanzan nuevamente con Espacio.
- `Cannons`: equipa una descarga de dos proyectiles que atraviesan y destruyen
  todos los ladrillos de su trayectoria. Se dispara con F.
- `GhostPaddle`: durante 5 segundos crea una defensa a lo ancho de la cancha,
  situada a la altura de la paleta. Toda pelota que no golpee la paleta rebota
  en esa línea, por lo que ninguna puede escapar por la parte inferior mientras
  el efecto esté activo.

Las duraciones de los efectos temporales pueden modificarse en `settings.py`.
