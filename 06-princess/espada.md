# Capítulo 8

# Espadas en Movimiento y una Mazmorra Viva: *Princess*

> “A lo largo de la serie Zelda siempre he intentado que los jugadores sientan que están dentro de una especie de jardín en miniatura. Mi reto era cómo hacer que la gente se sintiera cómoda y, al mismo tiempo, muy asustada.”
>
> —Shigeru Miyamoto, *CNN Interactive*, 1998

Cada juego anterior de este libro ha vivido dentro de los límites de una sola pantalla estática (Pong, Breakout, Match3) o, cuando mucho, de un nivel lineal que se recorre de izquierda a derecha (Super Martian). The Legend of the Princess (06-princess en el repositorio) es el primero en romper ambos límites a la vez, y lo hace cambiando dos cosas simultáneamente. La primera es de género: deja de ser un juego de pantalla fija o de nivel lineal para convertirse en un ARPG[^1] de vista cenital al estilo The Legend of Zelda. El jugador combate con espada, recoge corazones, empuja y lanza macetas, y se desplaza entre habitaciones de una mazmorra generada de forma procedural, cada una con su propio surtido de enemigos, obstáculos y puertas. La segunda es de infraestructura: es la primera vez en el libro que aparece la necesidad de tener más de una “pantalla” activa al mismo tiempo. El caso canónico es un menú de pausa dibujado sobre un juego que sigue siendo visible mientras está congelado. Esa necesidad no la resuelve la máquina de estados de reemplazo total del Capítulo 4, sino una pieza de infraestructura nueva: una pila de estados.

Este capítulo sigue, por eso, dos frentes independientes. El primero, en la Sección 8.2, es puramente de biblioteca: qué problema exacto resuelve una pila de estados que una máquina de reemplazo no resuelve, y cómo la implementa gale comparándola, código en mano, con la StateMachine ya conocida. Se advierte desde ya un matiz importante que se aclarará en su momento: este juego en particular no necesita apilar pantallas (no tiene menú de pausa). Por eso la pila de estados se presenta aquí como la pieza de infraestructura que la mecánica exige en general, y que el Capítulo 9 sí terminará usando en código real, para superponer un cuadro de diálogo sobre un mundo que debe quedar congelado pero visible.

El segundo frente, en la Sección 8.3 en adelante bajo “Integrando todo”, es de integración pura: cómo Princess reutiliza la máquina de estados simple (Capítulo 4) para su propio flujo de pantallas y para la inteligencia artificial de sus enemigos, cómo estructura sus entidades y objetos como datos, y cómo reutiliza los temporizadores y tweens de gale.timer.Timer (Capítulo 6, Sección 6.3) para la transición entre habitaciones.

## 8.1. Contexto histórico: el mundo que se podía guardar

The Legend of the Princess usa nombres y personajes propios. Pero la mecánica que reconstruye –combate en tiempo real, exploración no lineal y mazmorras con acertijos, todo en vista cenital– tiene un antecedente concreto, The Legend of Zelda, desarrollado por Nintendo bajo la dirección de Shigeru Miyamoto y Takashi Tezuka.

El juego se concibió en 1984 como título de lanzamiento para el Family Computer Disk System, el periférico de disquetes de la Famicom, y se publicó en Japón en febrero de 1986. Miyamoto declaró en entrevistas posteriores que la idea nació de sus propias exploraciones infantiles por el campo y las colinas cercanas a su pueblo natal. Tezuka, por su parte, aportó buena parte de la estructura narrativa (Sheff, 1993). La elección del disco, y no del cartucho habitual, no fue anecdótica: permitió, por primera vez en una consola Nintendo, guardar la partida, una innovación técnica indispensable para un diseño que rompía con el formato de niveles lineales dominante hasta entonces.

Zelda propuso en su lugar un mundo abierto explorable desde el primer instante, sin un orden obligatorio de progresión, combinado con mazmorras laberínticas, resolución de acertijos y combate en tiempo real: exactamente los cuatro elementos que este capítulo reconstruye en Princess. Esta combinación es la que la historiografía del videojuego señala como acta fundacional del género action-adventure, y por extensión del ARPG de vista cenital (Sheff, 1993). El impacto de ese diseño de mundo abierto sigue siendo objeto de estudio disciplinar. Un análisis reciente en la revista diid. Disegno Industriale Industrial Design compara las estrategias espaciales de una entrega posterior de la saga con principios de diseño paisajístico, evidenciando que la genealogía de diseño abierta en 1986 continúa activa cuarenta años después (Uguzzoni, 2025).

La posibilidad de guardar la partida que introdujo el Family Computer Disk System no vuelve a aparecer en este libro sino hasta Ultimate Fantasy (Capítulo 9), el primer juego lo suficientemente largo como para necesitarla de verdad.

**Figura 8.1:** Shigeru Miyamoto en 2015, codirector de The Legend of Zelda junto con Takashi Tezuka.

*Fotografía del Ministerio de Educación, Cultura, Deportes, Ciencia y Tecnología de Japón, licencia CC BY 4.0, vía Wikimedia Commons.*

## 8.2. Arquitectura de pantallas: la pila de estados

### 8.2.1. El límite de una máquina de estados de reemplazo total

Recuérdese el contrato de gale.state.StateMachine del Capítulo 4, es decir, un diccionario de estados con nombre, un estado current, y un método change que hace exactamente esto:

```python
def change(
    self, state_name: str, *args: Tuple[Any], **kwargs: Dict[str, Any]
) -> None:
    self.current.exit()
    self.current = self.states[state_name](self)
    self.current.enter(*args, **kwargs)
```

La palabra clave es reemplazo. change llama exit() sobre el estado saliente, lo descarta por completo (la referencia self.current se sobrescribe) y construye uno nuevo desde cero. En todos los juegos vistos hasta ahora esto es exactamente lo deseado: no tiene sentido que la pantalla de game over y la de juego en curso existan simultáneamente.

Pero el supuesto se rompe en cuanto aparece una pantalla que debe superponerse a otra sin destruirla: un menú de pausa dibujado sobre el juego (que debe seguir viéndose, congelado, detrás del menú), un cuadro de diálogo sobre un mundo explorable, o un cuadro de confirmación sobre un menú de pausa. Con StateMachine eso es imposible por construcción: en el instante en que se llama change(’pause’), el estado de juego ya fue destruido. No hay manera de volver a él con su información intacta salvo reconstruirlo de nuevo, perdiendo exactamente el punto del ejercicio (que el juego quede tal cual estaba, no que se reinicie).

### 8.2.2. Cómo lo implementa gale: gale.state.StateStack

La solución de gale vive en el mismo módulo que StateMachine, gale.state, y comparte con ella la misma base –todo estado, apilado o no, sigue siendo una BaseState con los métodos enter, exit, on_input, update y render–, lo cual es precisamente lo que permite comparar ambas clases método a método.

Antes de leer el código, conviene ver la idea en un dibujo. La Figura 8.2 muestra la pila en el instante exacto de una pausa: dos estados coexisten, uno encima del otro, pero solo uno de ellos, la cima, sigue “vivo” en el sentido de recibir entrada y lógica; el de abajo quedó congelado y solo se sigue dibujando.

```text
          PauseState (activo)
                                     render():
                                     TODOS,                          update()/on_input():
                                     de abajo                        SOLO el de la cima
                                     hacia arriba
         PlayState (congelado)
```

**Figura 8.2:** Estado de la pila durante una pausa: render() recorre toda la lista de abajo hacia arriba, así que PlayState sigue dibujándose tal cual quedó; update() y on_input(), en cambio, solo llegan al estado en la cima, PauseState –el juego de abajo no avanza ni un cuadro mientras el menú está encima–.

La Tabla 8.1 resume, operación por operación, lo que el dibujo anterior muestra para el caso de la pausa: en qué se parecen y en qué difieren StateMachine y StateStack antes de entrar en el código real de esta última.

| Operación | StateMachine | StateStack |
|---|---|---|
| Cambiar de estado | `change`: saca el estado anterior con `exit()` y lo sustituye por uno nuevo. | `push` agrega un estado encima sin tocar los demás; `pop` saca solo el de la cima con `exit()`. |
| Quién recibe `update`/`on_input` | Siempre uno solo: `self.current`. | Siempre uno solo: `self.states[-1]` (la cima). |
| Quién se dibuja | Solo el estado actual, `self.current`. | Todos los apilados, de abajo hacia arriba (`for state in self.states`). |

**Cuadro 8.1:** Comparación método a método entre `StateMachine` y `StateStack`: la fila decisiva es la última, dibujar solo el actual contra dibujar toda la pila, porque de ahí sale, sin ningún código adicional, la posibilidad de un menú superpuesto.

```python
class StateStack:
    def __init__(self) -> None:
        self.states = []

    def on_input(self, input_id: str, input_data: InputData) -> None:
        if len(self.states) == 0:
            raise RuntimeError("State stacks is empty")
        self.states[-1].on_input(input_id, input_data)

    def update(self, dt: float) -> None:
        if len(self.states) == 0:
            raise RuntimeError("State stacks is empty")
        self.states[-1].update(dt)

    def render(self, surface: pygame.Surface) -> None:
        for state in self.states:
            state.render(surface)

    def push(
        self, state: BaseState, *args: Tuple[Any], **kwargs: Dict[str, Any]
    ) -> None:
        self.states.append(state)
        state.enter(*args, **kwargs)

    def pop(self) -> None:
        if len(self.states) == 0:
            raise RuntimeError("State stacks is empty")
        self.states[-1].exit()
        self.states.pop()
```

La comparación, método por método, deja ver que el contrato de entrada y salida de un estado, enter/exit, es idéntico al de StateMachine; lo que cambia es cuándo se invoca y qué se hace con los estados que no están activos:

- **Cambiar de estado:** en `StateMachine` es `change`: saca el estado anterior (`exit`) y lo sustituye. En `StateStack` hay dos operaciones separadas, `push` (agrega un estado encima de los que ya había, sin tocarlos, y ejecuta `enter`) y `pop` (saca solamente el de la cima con `exit` y lo elimina de la lista), dejando expuesto de nuevo el estado que estaba justo debajo, intacto.
- **Quién recibe entrada y actualización:** en ambas clases, solo un estado la recibe: `self.current` en una, `self.states[-1]` (la cima) en la otra. Nunca hay dos estados compitiendo por el mismo evento de teclado ni actualizándose dos veces en el mismo cuadro.
- **Quién se dibuja:** aquí está la diferencia real. `StateMachine.render` dibuja únicamente `self.current`. `StateStack.render` recorre toda la lista, de abajo hacia arriba (`for state in self.states`), de modo que un estado que dejó de recibir `update` por no estar en la cima sigue dibujándose cuadro a cuadro, exactamente como quedó congelado la última vez que se actualizó.

Esa última fila de la comparación es, en una sola línea de código (for state in self.states en render contra self.current.render en StateMachine), todo el mecanismo detrás de un menú de pausa. Si un estado de juego se apila y luego se empuja un PauseState encima, el estado de juego nunca recibe exit() (sigue en la lista) ni vuelve a recibir update() (ya no es la cima). Pero render() lo sigue dibujando en cada cuadro. El jugador ve el mundo tal cual estaba en el instante de la pausa –nada se mueve, ninguna animación avanza– con el menú dibujado por encima.

Al hacer pop() sobre el PauseState, este desaparece de la pila con su exit(). El estado de juego, que nunca dejó de estar ahí, vuelve a ser la cima, así que retoma update exactamente en el punto en que lo había dejado, porque nunca fue destruido ni reconstruido.

> **“Congelado” significa que deja de recibir update, no que todo se detiene**
>
> Apilar un PauseState detiene la lógica que vive dentro de update: física, animaciones, temporizadores propios del estado de juego. No detiene nada que ya haya sido disparado por fuera de ese ciclo. Por ejemplo, la música de fondo que PlayState.enter arranca con pygame.mixer.music.play() (src/states/game/PlayState.py) sigue sonando durante la pausa, porque pygame.mixer.music es un reproductor global e independiente del update del estado que lo inició. Si un menú de pausa debe silenciar la música, hace falta pausarla explícitamente (pygame.mixer.music.pause()/unpause()) al entrar y salir del propio PauseState: “congelado” es una propiedad de la pila de estados, no del sistema de audio.

### 8.2.3. Un caso real: superponer sin congelar la ejecución completa

Vale una aclaración honesta antes de continuar: The Legend of the Princess, el juego de este capítulo, no tiene menú de pausa, así que no hay, dentro de su propio código, un PauseState que mostrar. La pila de estados se introduce aquí, y no en el capítulo donde efectivamente se usa por primera vez, por dos razones. La primera es que la necesidad conceptual de superponer pantallas nace exactamente del tipo de juego que comienza en este capítulo (uno con más de una posible “vista” sobre el mismo mundo). La segunda es que los dos capítulos siguientes construyen directamente sobre esta sección: el Capítulo 9 reemplaza por completo su StateMachine de nivel superior por una StateStack, y el Capítulo 10 hace lo mismo. Adelantar el ejemplo real de UltimateFantasy deja ver el mecanismo funcionando con datos reales en lugar de quedarse solo en la teoría:

```python
class UltimateFantasy(Game):
    def init(self) -> None:
        self.state_stack = StateStack()
        self.state_stack.push(StartState(self.state_stack))

    def update(self, dt: float) -> None:
        self.state_stack.update(dt)

    def render(self, surface: pygame.Surface) -> None:
        self.state_stack.render(surface)
```

y, dentro del estado de mundo explorable, la apertura de un cuadro de diálogo al interactuar con un personaje no jugador:

```python
def _try_interact(self) -> None:
    from src.states.game.DialogueState import DialogueState

    player = self.party.first_alive()
    ...
    for npc in self.current_region().npcs:
        ...
        if dx <= 1 and dy <= 1:
            text = npc.on_interact()
            self.stack.push(DialogueState(self.stack), text=text)
            return
```

DialogueState se apila directamente sobre el estado de juego que contiene el mundo. A partir de ese push, state_stack.update solo llama al diálogo: el mundo deja de moverse y los personajes dejan de caminar. Pero state_stack.render sigue dibujando el mundo en cada cuadro, con el cuadro de texto encima. Es el mismo mecanismo del menú de pausa, aplicado a un problema distinto: el de congelar el juego visible sin ocultarlo mientras el jugador lee un texto.

La Figura 8.3 retoma este mismo ejemplo, pero extendido en el tiempo, para mostrar el ciclo completo de una superposición: el push que abre el diálogo y, cuadros después, el pop que lo cierra. Nótese que EstadoDeMundo solo recibe una llamada al principio, la que dispara el push. En la segunda mitad del diagrama no vuelve a aparecer ninguna flecha dirigida a él, y esa ausencia es, visualmente, la prueba de que quedó congelado sin que nadie, ni enter, ni exit, ni update, volviera a tocarlo mientras estuvo debajo de DialogueState.

## 8.3. Integrando todo: Princess

Con la pila de estados ya entendida como pieza de infraestructura de gale, el resto del capítulo es, en cambio, un ejercicio de integración con lo que ya se tenía: Princess resuelve su propio flujo de pantallas con la StateMachine simple, no con la pila (no la necesita), y reutiliza, para la inteligencia artificial de sus enemigos, para representar entidades y objetos, y para las transiciones entre habitaciones, ideas de los capítulos anteriores.

```text
     :Jugador             :EstadoDeMundo                  :StateStack                 :DialogueState
                         on_input(interactuar)
                                      on_input(interactuar)
                               push(DialogueState(self.stack), text)
                                                                        enter(text)
                         on_input(confirmar)
                                                                  on_input(confirmar)
                                                                          pop()
                                                                          exit()
```

**Figura 8.3:** Ciclo completo de push/pop sobre StateStack para el cuadro de diálogo de UltimateFantasy: arriba, el push que apila DialogueState y ejecuta su enter(); abajo, cuadros después, el pop que ejecuta su exit() y lo retira de la pila. EstadoDeMundo recibe la llamada inicial que dispara el push pero ninguna otra después, ni exit() ni update(), así que su ausencia de la mitad inferior del diagrama es, precisamente, la evidencia de que quedó congelado, tal cual estaba, sin haber sido tocado.

### 8.3.1. El flujo de pantallas de Princess: de vuelta a StateMachine

El juego completo, a nivel de gale.game.Game, es tan simple como el de Flappy Bird: tres pantallas que se reemplazan entre sí, nunca se superponen, así que StateMachine basta:

```python
class TheLegendOfThePrincess(Game):
    def init(self) -> None:
        self.state_machine = StateMachine(
            {
                "start": game_states.StartState,
                "play": game_states.PlayState,
                "game-over": game_states.GameOverState,
            }
        )
        self.state_machine.change("start")
```

Las tres transiciones entre estas pantallas son igual de directas. De start a play ocurre al presionar enter en StartState.on_input. De play a game-over ocurre cuando Dungeon invoca el callback on_game_over al llegar la vida del jugador a cero. Y de game-over de vuelta a start ocurre, otra vez, al presionar enter, esta vez en GameOverState.on_input. La Figura 8.4 dibuja esta máquina de tres estados con sus transiciones reales, en el mismo estilo que la Figura 4.5 del Capítulo 4.

```text
                                                             vida = 0
                         enter                                                game-over
      start                                 play
                                           enter
```

**Figura 8.4:** Máquina de estados finitos del flujo general de The Legend of the Princess: start → play ocurre al presionar enter sobre la pantalla de título, play → game-over ocurre cuando la vida del jugador llega a cero (el callback _on_game_over de PlayState), y game-over → start ocurre, otra vez, al presionar enter sobre la pantalla de game over.

PlayState entra directamente a construir al jugador y una Dungeon (la mazmorra), y expone un callback _on_game_over que la mazmorra invoca cuando la vida del jugador llega a cero:

```python
def _on_game_over(self) -> None:
    self.state_machine.change("game-over", player=self.player)
```

Nótese el patrón: es la misma idea de pasar datos al entrar a un estado que ya se practicó en el Capítulo 4 (change reenvía *args/**kwargs a enter), usada aquí para que la pantalla de game over pueda, por ejemplo, mostrar estadísticas del jugador que acaba de morir.

### 8.3.2. Qué sobrevive entre habitaciones: el jugador como estado persistente

Princess no tiene “niveles” discretos con pantalla de transición entre uno y otro; tiene una mazmorra de habitaciones encadenadas, y el jugador se desplaza de una a otra cruzando una puerta. Lo interesante, en términos de arquitectura, es qué sobrevive a ese cruce y qué se descarta. La clase Dungeon mantiene una única instancia de Player durante toda la partida y la pasa a cada Room que construye:

```python
class Dungeon:
    def __init__(
        self,
        player: TypeVar("Player"),
        on_game_over: Callable[[], None],
    ) -> None:
        self.player = player
        self.on_game_over = on_game_over
        self.current_room = Room(self.player, self.on_game_over)
        self.next_room = None
        ...
```

Cuando el jugador cruza una puerta, begin_shifting construye una Room nueva, con su propio surtido aleatorio de enemigos y objetos, pero reutiliza el mismo objeto Player, con su vida, su dirección y (si llevaba una maceta en brazos) su carga consigo. Lo que se descarta al cambiar de habitación es exactamente lo que debe descartarse: enemigos, macetas, interruptores de esa habitación en particular. Lo que sobrevive, en cambio, es exactamente lo que define el progreso del jugador: sus corazones de vida (self.player.health, seis unidades iniciales, dos por corazón dibujado en pantalla) y su posición relativa a la puerta por la que entró.

No hay, en este juego, puntaje ni inventario de ítems recolectables más allá de los corazones mismos. Pero la estructura es la misma que usaría cualquier extensión con esas mecánicas: el dato que debe persistir entre pantallas vive en el objeto Player, que nunca se destruye, y no en la Room, que sí.

### 8.3.3. Entidades y objetos como datos

Tanto los enemigos como los objetos del escenario (macetas, interruptores, corazones) se definen como diccionarios de datos en src/definitions/, no como una clase por cada tipo de enemigo. Un enemigo, por ejemplo, es solamente su animación:

```python
"skeleton": {
    "texture": "entities",
    "animations": {
        "walk-left": {"frames": [22, 23, 24, 23], "interval": 0.2},
        "walk-right": {"frames": [34, 35, 36, 35], "interval": 0.2},
        ...
        "idle-left": {"frames": [23]},
        ...
    },
},
```

y un objeto de escenario incluye además su comportamiento al ser tocado, como el corazón:

```python
def _pickup_heart(player, obj) -> None:
    player.heal(2)
    settings.SOUNDS["heart-taken"].play()

GAME_OBJECT_DEFS = {
    ...
    "heart": {
        "type": "heart",
        "texture": "hearts",
        "frame": 5,
        "solid": False,
        "consumable": True,
        "default_state": "default",
        "states": {"default": {"frame": 5}},
        "on_consume": _pickup_heart,
    },
}
```

GameObject.on_consume guarda esa función y Room.update la invoca cuando el jugador colisiona con un objeto consumible. Es el mismo patrón de clausura como callback guardado en un diccionario que el Capítulo 6 (Sección 6.2) usó para las reacciones al completar una fila de Match3, aplicado ahora a “qué le pasa al jugador cuando toca este objeto” en lugar de “qué le pasa al tablero cuando se completa esta fila”.

Conviene ser preciso, sin embargo, en un punto donde es fácil asumir demasiado por analogía con el Capítulo 7 (Sección 7.2): Super Martian carga su nivel desde un archivo JSON exportado por Tiled, dibujado a mano una sola vez. Princess no hace eso: cada Room se genera de forma procedural en tiempo de ejecución. _generate_walls_and_floors elige aleatoriamente entre variantes de piso y pared para cada celda, y _generate_entities/_generate_objects escogen al azar cuántos y cuáles enemigos y obstáculos poblarán la habitación.

Lo que Princess sí retoma de Super Martian es la maquinaria de bajo nivel para trabajar con hojas de sprites recortadas en tiles (settings.frame, TILE_SIZE, frames.generate_frames), no su cargador de niveles como archivo de datos. Las plantillas de ENTITY_DEFS y GAME_OBJECT_DEFS sí son “datos” en el sentido de separar la descripción de un tipo de objeto de su lógica de juego. Pero la disposición de una habitación concreta, dónde queda cada enemigo, cada maceta, es aleatoria, no autoral.

### 8.3.4. IA de los enemigos: una máquina de estados de dos nodos

Cada enemigo es una Entity con su propia StateMachine, la misma clase del Capítulo 4, aplicada ahora no al flujo de pantallas sino a la toma de decisiones de un personaje no jugador. Room._generate_entities le da a cada enemigo solamente dos estados posibles, idle y walk:

```python
entity.state_machine.states = {
    "walk": lambda sm, e=entity: EntityWalkState(e, sm),
    "idle": lambda sm, e=entity: EntityIdleState(e, sm),
}
entity.change_state("walk")
```

La decisión de cuándo pasar de uno a otro no ocurre en update, que solo aplica movimiento y colisión, sino en un método adicional, process_ai, que Room.update invoca una vez por cuadro para cada entidad viva y que cada estado sobrescribe con su propia regla:

```python
class EntityIdleState(BaseEntityState):
    def enter(self) -> None:
        self.entity.change_animation(f"idle-{self.entity.direction}")
        self.wait_duration = 0
        self.wait_timer = 0

    def process_ai(self, room, dt: float) -> None:
        if self.wait_duration == 0:
            self.wait_duration = random.randint(1, 5)
        else:
            self.wait_timer += dt
            if self.wait_timer > self.wait_duration:
                self.entity.change_state("walk")

class EntityWalkState(BaseEntityState):
    def update(self, dt: float) -> None:
        entity = self.entity
        held = entity.held

        if held["move_left"]:
            entity.direction = "left"
        elif held["move_right"]:
            entity.direction = "right"
        elif held["move_up"]:
            entity.direction = "up"
        elif held["move_down"]:
            entity.direction = "down"

        self.bumped = move_and_bump(entity, dt)

    def _pick_direction(self) -> None:
        for stop in _STOP_COMMANDS:
            stop.execute(self.entity)

        direction = random.choice(_DIRECTIONS)
        _MOVE_COMMANDS[direction].execute(self.entity)
        self.entity.change_animation(f"walk-{direction}")

    def process_ai(self, room, dt: float) -> None:
        if self.move_duration == 0 or self.bumped:
            self.move_duration = random.randint(1, 5)
            self._pick_direction()
        elif self.movement_timer > self.move_duration:
            self.movement_timer = 0
            if random.randint(1, 3) == 1:
                self.entity.change_state("idle")
                return
            self.move_duration = random.randint(1, 5)
            self._pick_direction()
        self.movement_timer += dt
```

held no es un invento propio de EntityWalkState: es un diccionario de intención (move_left/move_right/move_up/move_down) que Entity expone para cualquier entidad, jugador incluido, y que _MOVE_COMMANDS/ _STOP_COMMANDS llenan mediante gale.command (Capítulo 7, Sección 7.4.3), el mismo módulo que introdujo Super Martian. Player liga esos mismos comandos –MOVE_LEFT, MOVE_RIGHT y análogos– a InputHandler mediante CommandBindings, exactamente como lo hacía Super Martian con move_direction; _pick_direction ejecuta esos mismos objetos, pero por decisión de process_ai en lugar de por una tecla presionada. Es el mismo patrón de reutilización ya visto con la babosa de Super Martian –un Command compartido, disparado unas veces desde InputHandler y otras desde la lógica autónoma de un enemigo– aplicado aquí a cuatro direcciones en vez de dos.

Es, literalmente, una máquina de estados de dos nodos con transiciones gobernadas por temporizadores aleatorios: un enemigo inactivo espera entre uno y cinco segundos y luego camina; uno que camina lo hace en una dirección aleatoria durante un intervalo también aleatorio, y al vencerse tiene una probabilidad de un tercio de volver a quedar inactivo. Es deliberadamente simple, ya que no persigue al jugador ni reacciona a su cercanía. Pero es exactamente la misma idea de la máquina de estados de reemplazo total del Capítulo 4 (un estado activo a la vez, con change_state para transicionar), aplicada por primera vez a un personaje no jugador en lugar de al flujo de pantallas del juego.

La Figura 8.5 dibuja esta máquina de dos estados con sus dos transiciones reales, ambas gobernadas por temporizadores con duraciones aleatorias en segundos y no por ninguna medición de distancia al jugador.

La separación entre update (mecánica: mover y detectar colisión con el borde de la habitación, en move_and_bump) y process_ai (decisión: hacia dónde y por cuánto tiempo) es la que permite que los estados del jugador, que comparten la misma jerarquía de clase, BaseEntityState, reutilicen la mitad de movimiento sin heredar ninguna lógica de inteligencia artificial que no les corresponde.

```text
                               wait_timer > wait_duration
                              (wait_duration aleatorio, 1–5 s)
                      idle                                       walk
                             movement_timer > move_duration
                               y random.randint(1,3) == 1
                                    (probabilidad 1/3)
```

**Figura 8.5:** Máquina de estados de la IA de un enemigo en Princess: idle → walk ocurre al vencerse un temporizador de espera con duración aleatoria entre uno y cinco segundos (EntityIdleState.process_ai); walk → idle ocurre al vencerse el temporizador de movimiento (también entre uno y cinco segundos) y con una probabilidad adicional de un tercio (EntityWalkState.process_ai); si esa probabilidad no se cumple, el enemigo elige una nueva dirección aleatoria y una nueva duración, pero permanece en walk. Ninguna de las dos transiciones depende de la posición del jugador: es una caminata errante gobernada por relojes, no una persecución por proximidad.

### 8.3.5. Reutilizando los temporizadores de Match3: la transición entre habitaciones

El desplazamiento de cámara al cruzar una puerta, la mazmorra “resbala” de una habitación a la siguiente en un segundo, con el jugador atravesando visualmente el hueco de la puerta, no está escrito a mano cuadro a cuadro, sino que reutiliza Timer.tween, la misma utilidad de interpolación con funciones anónimas del Capítulo 6 (Sección 6.3):

```python
to_tween = [
    (self, {"camera_x": shift_x, "camera_y": shift_y}),
    (self.player, {"x": player_x, "y": player_y}),
]

pot = getattr(self.player.state_machine.current, "pot", None)
if pot is not None:
    to_tween.append(
        (pot, {"x": player_x, "y": player_y - pot.height / 2})
    )

Timer.tween(
    1,
    to_tween,
    on_finish=self._finish_shifting_and_place_player,
)
```

En una sola llamada a Timer.tween se interpola, durante un segundo, la posición de la cámara (camera_x/camera_y de la propia Dungeon), la del jugador, y, condicionalmente, si el jugador está cargando una maceta al momento de cruzar, la de la maceta, para que las tres cosas se muevan de forma sincronizada. El callback on_finish es, otra vez, el patrón de clausura usado como reacción a que termine un temporizador: al vencerse el segundo, _finish_shifting_and_place_player intercambia current_room por next_room y reubica al jugador junto a la puerta opuesta de la nueva habitación.

Nótese que esto no usa la pila de estados de la Sección 8.2, pues es una animación dentro de la misma pantalla de juego, no una pantalla nueva superpuesta. Pero sí es el mismo mecanismo de temporizadores que le da a esa sección su motivación original: un giro de cámara que no debe verse como un salto instantáneo.

### 8.3.6. Recortando al jugador contra el hueco de la puerta: gale.stencil

El segundo tramo de una transición de habitación, antes de que empiece a deslizarse la cámara, es el instante en que el jugador todavía está de pie sobre el umbral, así que parte de su sprite cae sobre el hueco abierto de la puerta, y otra parte todavía se solapa con la pared sólida que la rodea. Dibujar al jugador completo ahí encima haría que se viera “montado” sobre la pared. La primera versión de este capítulo resolvía esto ocultando al jugador por completo mientras durara el solape: un atajo honesto pero visible, ya que el jugador desaparecía y volvía a aparecer de golpe, en vez de cruzar el umbral.

gale.stencil.Stencil resuelve el problema de verdad, pues recorta, sobre el canal alfa de una superficie, únicamente la forma que se le indique, dejando transparente todo lo que quede fuera. Aplicado al sprite del jugador, la forma a conservar es, exactamente, el rectángulo de la abertura real de la puerta (Doorway.get_collision_rect()), no el rectángulo, más amplio, que solo se usa para detectar que el jugador está cerca de una puerta:

```python
sprite_rect = pygame.Rect(sprite_x, sprite_y, frame.width, frame.height)
visible = self.visibility_clip_rect.clip(sprite_rect)
visible.move_ip(-sprite_x, -sprite_y)

stencil = Stencil((frame.width, frame.height))
stencil.draw(lambda mask: mask.fill((255, 255, 255, 255), visible))
stencil.apply(image)
```

visibility_clip_rect, None para cualquier entidad que nunca cruza una puerta, y por lo tanto cero costo para enemigos y NPCs, se fija cada cuadro en Room.render únicamente si el jugador está cerca de alguna de las cuatro puertas, calculado intersectando su rectángulo de colisión contra la abertura real de la puerta correspondiente. El resultado visual es exactamente el pedido: la parte del jugador que cae dentro del hueco de la puerta se sigue viendo con normalidad, y solo la parte que se solaparía con la pared se recorta. Es decir, el jugador se ve pasar a través del umbral, cada vez más o menos visible según cuánto de su sprite ya cruzó, en vez de desaparecer y reaparecer de golpe.

**Figura 8.6:** Una partida en curso de The Legend of the Princess.

### 8.3.7. Construcción de The Legend of the Princess

Atando lo anterior, la construcción completa del juego combina varias piezas. Está una StateMachine de tres pantallas (inicio, juego, game over) para el flujo general, y una mazmorra de habitaciones generadas proceduralmente, conectadas por puertas que se abren al activar un interruptor (GameObject con estados unpressed/pressed y un callback on_collide). Está también un jugador con su propia StateMachine de siete estados –idle, walk, swing-sword, y sus tres variantes al cargar una maceta–, donde el ataque de espada crea un pygame.Rect de golpe posicionado según la dirección del jugador y comparado por colisión contra cada enemigo vivo de la habitación. A esto se suman enemigos con la máquina de estados de dos nodos ya descrita y una probabilidad de soltar un corazón al morir, transiciones entre habitaciones interpoladas con Timer.tween, y un recorte por gale.stencil del jugador contra el hueco de cada puerta, para que cruzarlas se vea como pasar a través del umbral y no como desaparecer y reaparecer. Es, en conjunto, la primera vez en el libro que todas las piezas de infraestructura de los capítulos anteriores –máquinas de estado, temporizadores y funciones anónimas, manejo de tiles– conviven en un solo juego, sin que ninguna sea el tema central. El tema central es, precisamente, integrarlas.

## 8.4. Ejercicios propuestos

1. Diseñar e implementar un PauseState para Princess usando StateStack en lugar de la StateMachine que el juego usa actualmente para su flujo de pantallas. Al presionar una tecla de pausa durante la partida, se debe apilar el nuevo estado sobre el de juego (que debe seguir dibujándose, congelado). Sobre ese menú de pausa, hay que apilar todavía un tercer estado, un cuadro de confirmación de “¿Salir al menú principal?”, de forma que la pila llegue a tener tres estados simultáneos y cada pop regrese exactamente al nivel anterior.
2. Extender la máquina de estados de dos nodos de un enemigo (EntityIdleState/EntityWalkState) con un tercer estado, chase, al que se transite cuando el jugador esté dentro de cierto radio de distancia y del que se regrese a idle cuando el jugador se aleje lo suficiente. Describir las tres transiciones posibles como un diagrama de estados.
3. El corazón es, hoy, el único objeto consumible y no usa ningún tween al ser recogido, sino que simplemente desaparece. Añadir una animación de recolección (por ejemplo, que el corazón se encoja y suba unos píxeles antes de desaparecer) usando Timer.tween sobre sus coordenadas y una función anónima como on_finish que recién entonces lo remueva de Room.objects y aplique la curación.
4. Reemplazar la generación procedural de Room por una carga de datos al estilo de Super Martian (Sección 7.2): diseñar un formato, un diccionario en código o un archivo JSON separado, que describa la disposición fija de una habitación (posiciones de enemigos, macetas e interruptores) y escribir el cargador correspondiente, de forma que sea posible diseñar una mazmorra completa sin escribir código adicional para cada habitación nueva.

[^1]: juego de rol de acción, del inglés *Action Role-Playing Game*.
