# Spec Delta

## ADDED Requirements

### Requirement: Endpoint de streaming SSE para el chat

El sistema SHALL exponer `POST /chat/stream` que responde con `Content-Type: text/event-stream` y emite los eventos del turno de conversación en orden.

#### Scenario: Stream exitoso

- **WHEN** un cliente autenticado envía `thread_id` y `message` a `POST /chat/stream`
- **THEN** el sistema responde 200 con `text/event-stream` y emite al menos los eventos `start` y `done` en ese turno

#### Scenario: Sin token de autenticación

- **WHEN** la solicitud a `POST /chat/stream` no incluye un JWT válido
- **THEN** el sistema responde 401 sin abrir el stream

### Requirement: Texto incremental del asistente

El sistema SHALL emitir el texto de la respuesta final del modelo en eventos `token` incrementales mientras se genera.

#### Scenario: Respuesta larga visible progresivamente

- **WHEN** el modelo genera una respuesta de varias oraciones
- **THEN** el cliente recibe eventos `token` con fragmentos de texto en orden antes del evento `done`

#### Scenario: Turno fuera de tema no genera tokens

- **WHEN** el mensaje del usuario está fuera del dominio del negocio
- **THEN** el sistema emite `start` y `done` con la respuesta predeterminada, sin eventos `token` ni de herramientas

### Requirement: Eventos de herramientas durante el turno

El sistema SHALL emitir un evento `tool_start` al invocar una herramienta y `tool_end` al terminar, identificando a la herramienta y sus argumentos.

#### Scenario: Herramienta de lectura

- **WHEN** el agente consulta datos mediante una herramienta de lectura
- **THEN** el cliente recibe `tool_start` con nombre y argumentos y luego `tool_end` con el resultado

#### Scenario: Escritura propuesta, no ejecutada

- **WHEN** el modelo intenta una operación de escritura
- **THEN** el sistema no ejecuta la escritura, emite los eventos de la herramienta y emite `pending_action` con la propuesta para confirmación humana

### Requirement: Evento done con la respuesta final saneada

El sistema SHALL emitir un evento `done` que contiene la respuesta final completa ya pasada por los guardrails, junto con `thread_id`, `tool_calls` y `pending_action`.

#### Scenario: Guardrails reescriben la respuesta

- **WHEN** el saneado final modifica el texto ya emitido durante el stream
- **THEN** el evento `done` contiene la versión final saneada y el cliente la usa para reemplazar el texto parcial acumulado

#### Scenario: Persistencia del turno

- **WHEN** el stream termina con el evento `done`
- **THEN** el turno queda persistido en el hilo y es visible en el historial por usuario

### Requirement: Errores posteriores a la apertura del stream

El sistema SHALL emitir un evento `error` con el mensaje en español cuando el turno falla después de abierto el stream.

#### Scenario: Modelo local no disponible

- **WHEN** el modelo local no responde durante el turno
- **THEN** el cliente recibe un evento `error` con el mensaje de que el asistente no está disponible en este momento

### Requirement: Fallback sin streaming

El sistema SHALL mantener `POST /chat` con contrato request/response sin cambios.

#### Scenario: Cliente sin soporte de streaming

- **WHEN** un cliente envía el turno por `POST /chat`
- **THEN** recibe la respuesta completa en el cuerpo de la respuesta, con el mismo contenido que el evento `done` del stream

### Requirement: Rate limit del stream

El sistema SHALL aplicar a `POST /chat/stream` el mismo límite de turnos por minuto que `POST /chat`.

#### Scenario: Límite excedido

- **WHEN** un usuario supera el límite de turnos por ventana de 60 segundos en `/chat/stream`
- **THEN** el sistema responde 429 con header `Retry-After` antes de abrir el stream

### Requirement: Cancelación del stream por el cliente

El sistema SHALL dejar de generar la respuesta cuando el cliente desconecta antes del evento `done`, y no debe persistir el turno interrumpido.

#### Scenario: El cliente aborta la conexión

- **WHEN** el navegador cancela la solicitud del stream antes de que termine el turno
- **THEN** el servidor detiene la generación y no persiste mensajes de ese turno
