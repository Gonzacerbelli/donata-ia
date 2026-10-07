import { expect, test } from "@playwright/test";

import { login } from "./helpers";

test("lista órdenes y abre el detalle", async ({ page }) => {
  await login(page);
  await page.getByRole("link", { name: "Órdenes" }).click();
  await expect(page.getByRole("heading", { name: "Órdenes" })).toBeVisible();

  const rows = page.locator("tbody tr");
  await expect(rows.first()).toBeVisible();
  await rows.first().getByRole("link", { name: "Ver" }).click();

  await expect(page).toHaveURL(/\/ordenes\/[a-f0-9]+/);
  await expect(page.getByText("Ítems")).toBeVisible();
});