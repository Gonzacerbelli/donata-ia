# Spec Delta

## MODIFIED Requirements

### Requirement: Toda escritura desde el chat exige confirmación humana

Las acciones de escritura SHALL llegar como `pending_action` con `token`, `tool`, `args` y `summary`, y SHALL ejecutarse sólo con `POST /chat/confirm`; la propuesta SHALL durar 10 minutos, servir una sola vez y validar sus argumentos antes de ejecutar.

#### Scenario: Propuesta antes de ejecutar

- **GIVEN** el asistente propone crear un cliente
- **WHEN** se registra la propuesta
- **THEN** la respuesta incluye `pending_action` y el cliente todavía no existe en el sistema

#### Scenario: Confirmación

- **WHEN** el usuario confirma con `POST /chat/confirm` usando el token
- **THEN** la acción se ejecuta, la entidad queda persistida y la respuesta informa que se hizo, sin ids internos

#### Scenario: Token inválido o expirado

- **WHEN** el token no existe, ya se usó o venció (10 minutos)
- **THEN** el servidor responde `404` con "La acción propuesta ya no está vigente" y no se ejecuta nada

#### Scenario: Argumentos inválidos

- **WHEN** los argumentos guardados no cumplen la firma de la herramienta
- **THEN** el servidor responde `422` con el detalle en español y no se ejecuta nada

#### Scenario: El usuario descarta la propuesta

- **WHEN** el usuario cancela la acción pendiente en la interfaz
- **THEN** no se ejecuta ninguna escritura y el chat informa que nada cambió

#### Scenario: La respuesta no afirma una ejecución que no ocurrió

- **GIVEN** un turno que no registró ninguna propuesta y no pasó por `POST /chat/confirm`
- **WHEN** el asistente responde
- **THEN** la respuesta no afirma que una escritura se hizo ("Hecho", "Revisá el resultado") y `pending_action` es nulo

## ADDED Requirements

### Requirement: El asistente no simula propuestas ni ejecuciones

Cuando un pedido de escritura o una afirmación de éxito no se corresponde con una propuesta registrada, el sistema SHALL forzar el registro de la propuesta y SHALL no devolver el texto que simula una acción pendiente o ejecutada; si no lo consigue, SHALL responder un mensaje seguro sin afirmar éxito y con `pending_action` nulo.

#### Scenario: Pedido de escritura conjugado sin propuesta

- **GIVEN** el usuario escribe un pedido de escritura con verbo conjugado ("repone 68 unidades", "agregá un cliente", "cargá una venta")
- **WHEN** el turno termina sin una propuesta registrada
- **THEN** el sistema reintenta registrar la propuesta y, si aun así no la obtiene, responde un mensaje seguro que no afirma éxito y deja `pending_action` nulo

#### Scenario: Texto que pide confirmación sin propuesta

- **GIVEN** el modelo responde "¿Confirmás esta acción?" o "Confirmá en la pantalla"
- **WHEN** no hay ninguna propuesta registrada en el turno
- **THEN** ese texto no se devuelve tal cual: el sistema fuerza el registro de la propuesta con `proponer_accion`

#### Scenario: Texto que afirma ejecución sin propuesta

- **GIVEN** el modelo responde "Reponer stock: sumar 68 unidades al stock del tapiz. Hecho. Revisá el resultado en la pantalla."
- **WHEN** `tool_calls` no contiene ninguna propuesta registrada ni una escritura ejecutada
- **THEN** ese texto no se devuelve como respuesta final y ninguna entidad del negocio cambia

#### Scenario: Detección tolerante a tildes y conjugaciones

- **WHEN** el mensaje o la respuesta usan voseo o formas conjugadas ("confirmás", "reponé", "repone", "agregá")
- **THEN** el sistema los reconoce como confirmación o intención de escritura, respectivamente

### Requirement: Las referencias de una propuesta se resuelven por nombre

Cuando una propuesta de escritura referencia un producto o cliente con un id inexistente, el sistema SHALL resolver la entidad por el nombre presente en el mensaje del usuario y SHALL corregir el id antes de registrar la propuesta; si el nombre es ambiguo, SHALL no adivinar y SHALL responder un mensaje seguro sin afirmar éxito.

#### Scenario: Id inventado por el modelo

- **GIVEN** el modelo propone `reponer_stock` con un `producto_id` inexistente, pero el mensaje nombra un único producto ("repone tapiz mural sol …")
- **WHEN** la propuesta referencia ese id inválido
- **THEN** el sistema corrige el id con el del producto nombrado y registra la propuesta con el id real

#### Scenario: Referencia ambigua

- **GIVEN** el mensaje nombra más de un producto o cliente
- **WHEN** la propuesta referencia un id inexistente
- **THEN** el sistema no elige ninguno, responde un mensaje seguro sin afirmar éxito y deja `pending_action` nulo

#### Scenario: Propuesta inválida repetida

- **GIVEN** el modelo insiste con la misma propuesta inválida
- **WHEN** se repite más de una vez
- **THEN** el sistema corta la iteración en vez de agotar los pasos y responde un mensaje seguro, sin afirmar éxito
