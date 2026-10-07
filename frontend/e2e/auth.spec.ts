import { expect, test } from "@playwright/test";

import { login } from "./helpers";

test("redirige a login cuando no hay sesión", async ({ page }) => {
  await page.goto("/ordenes");
  await expect(page).toHaveURL(/\/login/);
  await expect(page.getByRole("button", { name: "Ingresar", exact: true })).toBeVisible();
});

test("inicia sesión y muestra el dashboard", async ({ page }) => {
  await login(page);
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Órdenes" })).toBeVisible();
});