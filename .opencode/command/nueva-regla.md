---
description: >
  Agrega una regla de negocio que se debe respetar siempre en este proyecto, con su
  justificación. Úsalo cuando aparece una invariante nueva o una restricción del cliente.
agent: build
---

Registrá esta regla en la memoria del proyecto: **$ARGUMENTS**

## Por qué existe este comando

Las reglas de `AGENTS.md` son lo que permite que la IA acierte sin que se le explique el
dominio en cada prompt. Una regla que no está escrita se pierde en la sesión siguiente.

## Pasos

1. **Verificá que sea una regla, no una preferencia de estilo.** Las reglas son
   invariantes que, si se violan, producen datos incorrectos o funcionalidades rotas.

2. **Buscá el lugar correcto** en `AGENTS.md`:
   - Regla de negocio → §3 (Decisiones de alcance) o `docs/ARQUITECTURA.md` §4.
   - Convención de código → §5.
   - Regla de seguridad → §6 y el checklist de `docs/SEGURIDAD.md`.
   - Comando → §4 (Comandos canónicos).

3. **Escribí la regla** con esta estructura:

   ```markdown
   ### <Título corto>

   **Regla.** Qué se hace, en imperativo, sin ambigüedad.

   **Por qué.** La razón de negocio o el error que la motivó.

   **Cómo se verifica.** El test o la comprobación que demuestra que se respeta.

   **Cómo se rompe.** El error típico que alguien (o un agente) va a cometer.
   ```

4. **Agregá el ítem correspondiente** al checklist del agente que la tiene que cumplir
   (`backend-engineer` o `frontend-engineer`) si es una regla de implementación.

5. **Verificá que no contradiga** ninguna regla existente. Si la contradice, **frená y
   consultame**: probablemente haya que reemplazar una regla, no agregar otra.

6. Si la regla tiene impacto en un caso de uso, actualizá también `docs/CASOS_DE_USO.md`.

## Ejemplo del nivel de detalle esperado

```markdown
### Stock nunca queda negativo

**Regla.** Ninguna operación puede dejar `product.stock` menor a cero, incluidos los ajustes
manuales y las correcciones de inventario.

**Por qué.** El stock es la base del cálculo de qué se puede vender. Un stock negativo
corrupte la decisión de reposición y genera órdenes que no se pueden cumplir.

**Cómo se verifica.** Test que intenta un ajuste de -999 sobre un producto con stock 5 y
espera `400` con el disponible en el mensaje.

**Cómo se rompe.** Usando `$inc` sin condición: `{"$inc": {"stock": -999}}` funciona igual
pero deja el stock en negativo.
```
