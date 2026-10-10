import { expect, test } from "@playwright/test";

import { login } from "./helpers";

test("tablero de trabajo: mover una tarjeta, comentar y filtrar", async ({ page }) => {
  await login(page);
  await page.getByRole("link", { name: "Trabajo" }).click();
  await expect(page.getByRole("heading", { name: "Trabajo" })).toBeVisible();

  const pendiente = page.getByTestId("work-column-pendiente");
  const enCurso = page.getByTestId("work-column-en_curso");

  const handle = pendiente.getByLabel("Mover tarjeta").first();
  await handle.scrollIntoViewIfNeeded();
  const source = await handle.boundingBox();
  const destination = await enCurso.boundingBox();
  if (source && destination) {
    await page.mouse.move(source.x + source.width / 2, source.y + source.height / 2);
    await page.mouse.down();
    await page.mouse.move(destination.x + destination.width / 2, destination.y + 40, {
      steps: 12,
    });
    await page.mouse.up();
  }
  await expect(enCurso.getByRole("button", { name: /Comentarios \(/ }).first()).toBeVisible();

  await enCurso.getByRole("button", { name: /Comentarios \(/ }).first().click();
  const note = `Revisar con el proveedor ${Date.now()}`;
  await page.getByLabel("Nuevo comentario").fill(note);
  await page.getByRole("button", { name: "Comentar", exact: true }).click();
  await expect(page.getByRole("paragraph").filter({ hasText: note }).first()).toBeVisible();
  await page.getByRole("button", { name: "Cerrar", exact: true }).last().click();

  await page.getByLabel("Filtrar por prioridad").selectOption("alta");
  await expect(page).toHaveURL(/priority=alta/);
});
