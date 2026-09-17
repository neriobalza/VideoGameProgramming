# Underpaid

Base de videojuego con Gale y Pygame: menú principal, configuración de
pantalla, selección de dos jugadores con mandos o mando y teclado, y movimiento independiente.
Usa las dependencias compartidas del repositorio y la fuente incluida en Pygame.

## Ejecutar

Desde la raíz del repositorio, con el entorno virtual activado:

```bash
python -m pip install -r requirements.txt
python 09-underpaid/main.py
```

## Pantalla

La resolución virtual permanece en **640 × 480**. Gale escala el contenido a
la resolución de ventana elegida, conservando la proporción **4:3**:

| Índice | Resolución de ventana |
|--------|-----------------------|
| 0 | 640 × 480 |
| 1 | 960 × 720 |
| 2 | 1280 × 960 |
| 3 | 1920 × 1440 |

Edita `DEFAULT_RESOLUTION_INDEX` en `settings.py` para elegir la resolución
al iniciar. Durante la ejecución, abre **Configuración**, selecciona una
resolución y pulsa **Aplicar**. Los cambios del menú duran durante esa sesión;
volver sin aplicar descarta la selección pendiente.

Para jugar en pantalla completa, cambia **Modo** a **Pantalla completa** y
pulsa **Aplicar**. Para regresar a la ventana, selecciona **Ventana** y aplica.
La pantalla completa utiliza el tamaño del escritorio y mantiene el contenido
en 4:3, con bandas negras cuando la proporción del monitor es distinta.
La resolución de ventana seleccionada se conserva para cuando vuelvas a ese modo.
Puedes iniciar en pantalla completa configurando `FULLSCREEN = True` en `settings.py`.

## Controles

- Flechas arriba/abajo o W/S: seleccionar una opción.
- Enter o Espacio: activar la opción seleccionada.
- Flechas izquierda/derecha o A/D: cambiar la resolución o el modo seleccionado.
- Ratón: seleccionar y activar opciones; pulsar la resolución recorre la lista.
- Esc: volver al menú desde configuración o desde la partida.
- Salir: cerrar el juego desde el menú principal.

## Archivos principales

- `main.py`: punto de entrada.
- `settings.py`: resolución inicial, pantalla virtual, controles y colores.
- `src/Underpaid.py`: juego, máquina de estados y cambio de ventana.
- `src/gui/Menu.py`: menú compartido por las pantallas.
- `src/states/game/MainMenuState.py`: menú principal.
- `src/states/game/SettingsState.py`: configuración de resolución.
- `src/states/game/PlayerSelectState.py`: entrada con A y elección exclusiva de lado.
- `src/states/game/PlayState.py`: movimiento independiente de los dos jugadores.
- `src/entity/Player.py`: personaje y vínculo exclusivo con su mando o teclado.
- `src/input/ControllerManager.py`: inicialización de mandos y detección de conexiones.

## Dos jugadores

Conecta dos mandos Xbox (u otros mandos reconocidos por el mapeo de SDL).
También puedes utilizar **un mando y el teclado**; cada método de entrada puede
elegir Player 1 o Player 2. Se admiten dos participantes, cada uno con una entrada diferente.
El menú principal se puede manejar con cruceta y A, o con flechas y Enter;
**Jugar** abre la selección. La pulsación que abre esa pantalla no registra
un jugador: pulsa A o Enter de nuevo para entrar en el centro.

| Acción | Mando | Teclado |
|--------|-------|---------|
| Entrar en selección / confirmar | A | Enter |
| Recorrer izquierda, centro y derecha | Joystick izquierdo | Flechas izquierda/derecha |
| Cancelar confirmación | B | Delete (también Backspace) |
| Mover el personaje en la partida | Joystick izquierdo | W/A/S/D |

1. Pulsa **A en el mando o Enter en el teclado** para aparecer en el centro.
2. Usa el joystick izquierdo o las flechas para recorrer **Player 1 ↔ centro ↔ Player 2**.
   Suelta el joystick o la tecla entre pasos. Puedes cambiar de lado mientras exploras.
3. Pulsa **A o Enter de nuevo** sobre un personaje para confirmarlo. Desde el centro
   no se confirma ningún personaje. Sólo la confirmación reserva el lado.
4. Pulsa **B o Delete** para cancelar tu confirmación, liberar el personaje y seguir
   escogiendo. Un personaje confirmado por el otro jugador no puede seleccionarse.
5. Cuando ambos jugadores confirmen personajes diferentes, se abre la pantalla
   de juego con **dos personajes animados**.

Cada personaje se mueve en todas las direcciones únicamente con el método de entrada
que confirmó ese personaje, dentro de los límites de la pantalla. En el teclado,
**W** mueve arriba, **A** a la izquierda, **S** abajo y **D** a la derecha;
las flechas se utilizan para la selección y los menús.
Hay una zona muerta para evitar movimiento por pequeñas desviaciones del joystick.
Al desconectar un mando se vuelve a selección, conservando el jugador conectado (o el teclado) y
dejando libre el lado del desconectado. Un mando reconectado debe pulsar A y elegir
el lado libre y confirmarlo con A.

Ambos jugadores utilizan `assets/graphics/player_walk.png`, con fotogramas de
32 × 64 píxeles y cuatro fotogramas por dirección. Caminan mirando en la dirección
del movimiento y permanecen quietos mirando hacia su última dirección al detenerse.
Cada jugador mantiene su propio estado de animación. `PLAYER_FRAME_INTERVAL` en
`settings.py` permite ajustar la duración de cada fotograma.

## Verificación

Las pruebas utilizan eventos de teclado y eventos SDL con mandos simulados. Desde `09-underpaid`,
con el entorno virtual activado:

```bash
python -m unittest discover -s tests -v
```
