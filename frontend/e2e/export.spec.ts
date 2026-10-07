import { expect, test } from "@playwright/test";

import { login } from "./helpers";

test("exporta clientes a CSV", async ({ page }) => {
  await login(page);
  await page.getByRole("link", { name: "Clientes" }).click();
  await expect(page.getByRole("heading", { name: "Clientes" })).toBeVisible();

  const [download] = await Promise.all([
    page.waitForEvent("download"),
    page.getByRole("button", { name: "Exportar CSV" }).click(),
  ]);

  expect(download.suggestedFilename()).toMatch(/client.*\.csv$/i);
});