import { expect, test } from "@playwright/test";

import { login } from "./helpers";

let ultimoMensaje = "";

async function openChat(page: import("@playwright/test").Page) {
  await page.getByRole("button", { name: "Abrir asistente" }).click();
}

test("el historial del chat se conserva al actualizar la página", async ({ page }) => {
  test.setTimeout(180_000);
  ultimoMensaje = `hola-${Date.now()}`;
  await login(page);

  await openChat(page);
  await page.locator('textarea[placeholder="Escribí tu consulta..."]').fill(ultimoMensaje);

  const sent = page.waitForResponse(
    (res) => res.url().includes("/chat") && res.request().method() === "POST",
    { timeout: 120_000 },
  );
  await page.getByRole("button", { name: "Enviar" }).click();
  const response = await sent;
  expect(response.status()).toBe(200);
  await expect(page.getByText(ultimoMensaje, { exact: true })).toBeVisible();
  // El turno se persiste al cerrarse el stream; recargar antes cancela y no guarda nada.
  await response.body();

  await page.reload();
  await openChat(page);
  await expect(page.getByText(ultimoMensaje, { exact: true })).toBeVisible({ timeout: 15_000 });
});

test("recupera el historial del usuario aunque no haya nada en el navegador", async ({
  page,
}) => {
  test.skip(!ultimoMensaje, "corre después del test de actualización de página");
  await login(page);
  await openChat(page);
  await expect(page.getByText(ultimoMensaje, { exact: true })).toBeVisible({ timeout: 15_000 });
});

test("recupera el historial del usuario si la clave guardada no le pertenece", async ({
  page,
}) => {
  test.skip(!ultimoMensaje, "corre después del test de actualización de página");
  await login(page);
  await page.addInitScript(() => {
    window.localStorage.setItem("donata.chat.thread", "web-clave-ajena");
  });
  await openChat(page);
  await expect(page.getByText(ultimoMensaje, { exact: true })).toBeVisible({ timeout: 15_000 });
});
