# TriviaMillon

## Visión

Juego de trivia estilo "¿Quién Quiere Ser Millonario?" pero multijugador en vivo tipo Kahoot: un host proyecta las preguntas en una pantalla y cada participante responde desde su propio celular en tiempo real. Caso de uso inicial: la escuela dominical de mi novia, con un banco de ~1000 preguntas (actualmente en Excel). Meta a mediano plazo: publicarlo para que cualquiera pueda crear y hostear sus propias partidas con sus propios sets de preguntas.

Flexibilidad respecto al show original (decidido, no reabrir sin razón):
- **Múltiples sets/temas de preguntas**: no solo el banco de 1000, se pueden crear distintos mazos por tema y elegir cuál jugar.
- **Escalera de premios/puntos configurable**: número de preguntas, niveles y valores de cada partida son configurables por set/sesión, no fijos a los 15 niveles del show original.
- Todo lo demás (comodines, elim inación, etc.) se agrega **solo si hace falta** — no se sobre-construye de entrada.

## Decisiones de arquitectura ya tomadas

- **Modo de juego: multijugador en tiempo real (tipo Kahoot)** → requiere WebSockets. Esto es la decisión con más impacto en el stack: no basta con vistas Django normales, necesitamos **Django Channels + Redis** como channel layer.
- **Monolito Django**, sin frontend separado (no SPA en React/Vue). La interactividad en tiempo real se resuelve con WebSockets nativos + Alpine.js del lado del cliente, no con un framework JS pesado.
- **Solo Tailwind para CSS.** Nada de Bootstrap ni frameworks CSS adicionales. CSS custom solo si Tailwind genuinamente no lo resuelve (ej. una animación muy específica de "reveal" de respuesta), y siempre como excepción justificada, no como default.
- **Postgres** ya configurado como base de datos (ver [docker-compose.yml](docker-compose.yml)).
- **Docker para todo.** No se crean virtualenvs en el host; todo comando (`manage.py`, `pip`, tests) corre vía `docker compose exec/run`.

## Clean Architecture aplicada a este monolito

Django empuja naturalmente a mezclar todo en `models.py`/`views.py`. Para este proyecto separamos en capas explícitas **dentro de cada app**, de la más interna (sin dependencias de Django) a la más externa:

1. **Domain** (`domain/`) — Python puro, cero imports de Django/Channels. Entidades y reglas de negocio: motor del juego, cálculo de la escalera de puntos, validación de respuestas, progresión de preguntas. 100% testeable con `pytest` sin base de datos ni servidor.
2. **Application / use cases** (`services/`) — Orquesta el dominio: `CreateSession`, `JoinSession`, `SubmitAnswer`, `AdvanceQuestion`, `EndSession`. Depende de **abstracciones** (interfaces de repositorio), nunca de Django ORM directamente.
3. **Infrastructure** (`infrastructure/`) — Implementaciones concretas: repositorios sobre Django ORM, el channel layer de Redis. Aquí es donde "Django" realmente vive.
4. **Presentation** — Consumers de Channels (WebSocket) y views HTTP normales. Deben ser **delgados**: reciben el evento, llaman un use case, devuelven la respuesta. Nada de lógica de negocio aquí.

### SOLID aplicado (concreto, no genérico)

- **SRP**: `ScoringService` separado de `QuestionSelectionService` separado de `SessionLifecycleService`. Si una clase necesita "y" en su descripción, se parte.
- **OCP**: la escalera de premios y el motor de progresión se definen como estrategias intercambiables (`LadderStrategy`, `GameModeStrategy`) para poder agregar variantes (ej. modo eliminación, modo por equipos) sin tocar el código existente.
- **LSP**: cualquier implementación de `QuestionRepository` o `LadderStrategy` debe ser sustituible sin romper el use case que la consume.
- **ISP**: interfaces chicas y específicas (`QuestionRepository`, `SessionRepository`, `PlayerRepository`) en vez de un repositorio gigante.
- **DIP**: los use cases dependen de interfaces definidas en `domain/`, y las implementaciones concretas (Django ORM) se inyectan desde `infrastructure/`. El dominio nunca importa `django.db`.

## Stack técnico (objetivo)

- Django 5.2 (ya instalado)
- **Django Channels** + **channels-redis** para WebSockets — agregado en Fase 1
- **Redis** como servicio en `docker-compose.yml` — agregado en Fase 1
- Postgres (ya configurado)
- **Tailwind CSS** vía CLI standalone (v4, binario descargado en el Dockerfile; sin depender de Node en runtime, solo en build) — integrado en Fase 6
- **Alpine.js** (vía npm bundle, no CDN; ver stage `alpine_vendor` en el Dockerfile) para reactividad ligera del lado del cliente que consume los mensajes WebSocket — integrado en Fase 6
- `openpyxl` + `pandas` para el import de las 1000 preguntas desde Excel/CSV — agregado en Fase 2
- `qrcode[pil]` para el QR de la pantalla de sala del host — agregado en Fase 6
- `pytest` + `pytest-django` + `pytest-asyncio` para tests del dominio y de integración — agregado en Fases 3/5
- Para producción: `daphne` o `uvicorn` (ASGI) en vez de solo `gunicorn` (WSGI), porque Channels necesita ASGI

## Estructura de carpetas objetivo

La app `trivia` actual (blank) se reorganiza en Fase 1 en dos apps con responsabilidades separadas:

```
config/                 # settings, asgi.py, urls.py, routing.py (WS routes)
apps/
  questions/             # banco de preguntas, temas, import de Excel
    models.py            # Category, QuestionSet, Question, AnswerOption
    admin.py
    management/commands/import_questions.py
  game/                  # motor de juego y tiempo real
    models.py            # GameSession, Player, PlayerAnswer, LadderTemplate
    domain/               # Python puro, sin Django
      engine.py
      ladder.py
      scoring.py
      interfaces.py       # QuestionRepository, SessionRepository (Protocols/ABCs)
    services/             # use cases
      create_session.py
      join_session.py
      submit_answer.py
      advance_question.py
    infrastructure/
      django_repositories.py
    consumers.py          # WebSocket consumer, delgado
templates/
  host/                   # vista de proyector
  player/                 # vista de celular, mobile-first
static/src/
  input.css               # Tailwind entry point
```

## Modelo de datos (borrador — se cierra en Fase 2)

- `Category` / `QuestionSet` (tema/mazo, ej. "Biblia", "Cultura general")
- `Question` (texto, set al que pertenece, dificultad, orden opcional)
- `AnswerOption` (texto, `is_correct`)
- `LadderTemplate` / `PrizeLevel` (nivel, puntos, si es "checkpoint seguro")
- `GameSession` (código de sala, host, `QuestionSet` usado, `LadderTemplate` usado, estado: lobby/en curso/terminado, pregunta actual)
- `Player` (nickname, sesión a la que pertenece, canal/conexión)
- `PlayerAnswer` (jugador, pregunta, opción elegida, tiempo de respuesta, puntos obtenidos)

## Roadmap / checklist

**Fase 0 — Scaffold** ✅ completada
- [x] Proyecto Django en blanco, Docker Compose (web + Postgres), settings vía `.env`, git inicializado

**Fase 1 — Infra de tiempo real** ✅ completada
- [x] Agregar `channels`, `channels-redis`, `daphne`/`uvicorn` a `requirements.txt`
- [x] Agregar servicio `redis` a `docker-compose.yml`
- [x] Configurar `ASGI_APPLICATION`, `CHANNEL_LAYERS`, `asgi.py`, `routing.py`
- [x] Reorganizar la app `trivia` en `apps/questions` y `apps/game` (estructura de arriba)
- [x] Consumer de prueba (echo/ping) para validar que el WebSocket funciona de punta a punta en Docker

**Fase 2 — Banco de preguntas** ✅ completada
- [x] Modelos `Category`/`QuestionSet`, `Question`, `AnswerOption`
- [x] Django admin para gestión manual
- [x] Management command `import_questions` (Excel → DB), con reporte de filas inválidas/duplicadas
- [x] Importar las 1000 preguntas reales y validar una muestra a mano

**Fase 3 — Motor del juego (dominio puro)** ✅ completada
- [x] `LadderStrategy` (escalera de puntos configurable)
- [x] `GameEngine` (selección de siguiente pregunta, cálculo de puntaje, condiciones de fin de partida)
- [x] Interfaces de repositorio (`QuestionRepository`, `SessionRepository`, `PlayerRepository`)
- [x] Tests unitarios del dominio (sin DB, sin Django) — cobertura alta porque es la parte más crítica

**Fase 4 — Use cases + repositorios Django** ✅ completada
- [x] `CreateSession`, `JoinSession` (código de sala + nickname), `StartQuestion`, `SubmitAnswer`, `RevealAnswer`, `AdvanceQuestion`, `EndSession`
- [x] Implementación de los repositorios sobre el ORM
- [x] Tests de integración de los use cases contra Postgres real (en Docker)

**Fase 5 — Consumer WebSocket** ✅ completada
- [x] `GameConsumer`: conecta cliente ↔ use cases, delgado, sin lógica de negocio
- [x] Eventos: join, start, answer, reveal, next, end, disconnect/reconexión

**Fase 6 — UI del host (proyector)** ✅ completada
- [x] Pantalla de sala: código + QR para unirse
- [x] Pantalla de pregunta: texto, opciones, timer, conteo de quién ya respondió
- [x] Pantalla de resultados por pregunta + leaderboard
- [x] Tailwind, pensado para pantalla grande, pero responsive igual

**Fase 7 — UI del jugador (celular)** ✅ completada
- [x] Pantalla de unirse (código + nickname)
- [x] Sala de espera
- [x] Pantalla de respuesta (botones grandes, mobile-first)
- [x] Feedback correcto/incorrecto + puntaje personal + posición en leaderboard
- [x] Tailwind, 100% mobile-first, probado en viewport real de celular — pendiente confirmar visualmente en navegador/celular real (ver nota de la Fase 6, sin herramienta de browser en este entorno)

**Fase 8 — Multi-set / configuración de partida**
- [ ] Host elige `QuestionSet` y `LadderTemplate` al crear la sala
- [ ] Admin puede gestionar múltiples mazos independientes

**Fase 9 — Tests end-to-end**
- [ ] Suite de tests del flujo completo (crear sala → unirse varios jugadores → jugar → terminar)
- [ ] Manejo de reconexión de un jugador que pierde la señal

**Fase 10 — Producción**
- [ ] Servidor ASGI (`daphne`/`uvicorn`) en vez de `runserver`
- [ ] Redis persistente, Postgres con backups
- [ ] Static files (`whitenoise` o nginx), `collectstatic`
- [ ] HTTPS/WSS, `ALLOWED_HOSTS`, `SECRET_KEY` real, `DEBUG=0`
- [ ] Definir dónde se despliega (VPS, Railway, Fly.io, etc.) — **pendiente de decidir**

**Fase 11 — Pulido**
- [ ] Sonidos, animaciones de reveal (aquí sí se justifica algo de CSS custom puntual)
- [ ] Controles de host: pausar, saltar pregunta, expulsar jugador
- [ ] Leaderboard final animado

## Reglas de colaboración para las próximas sesiones

- Trabajar **fase por fase**, no saltar a UI sin tener el dominio/use cases probados.
- El código en `domain/` nunca importa Django. Si una clase de dominio "necesita" el ORM, es señal de que esa lógica pertenece a `infrastructure/` o `services/`.
- Todo cambio se prueba corriendo el stack en Docker (no solo "compila"), especialmente el flujo WebSocket con al menos dos clientes simulados.
- Tailwind primero; si se necesita CSS custom, decirlo explícitamente y justificar por qué Tailwind no alcanza.
- Mobile-first siempre para la vista de jugador; la vista de host se diseña para pantalla grande/proyector.
- Commits pequeños, verificables, sin features a medio terminar.

## Pendientes por decidir (no bloquean el roadmap, se resuelven cuando toque su fase)

- Dónde se despliega en producción (Fase 10)
- Si habrá cuentas de usuario para hosts (login) desde el MVP o se agrega al publicar
- Si el leaderboard es solo por partida o hay persistencia histórica entre partidas
