import { expect, type Page } from "@playwright/test";

export const USERNAME = process.env.E2E_USERNAME ?? "admin";
export const PASSWORD = process.env.E2E_PASSWORD ?? "cambiar-esta-clave";

export async function login(page: Page): Promise<void> {
  await page.goto("/login");
  await page.locator('input[name="username"]').fill(USERNAME);
  await page.locator('input[name="password"]').fill(PASSWORD);
  await page.getByRole("button", { name: "Ingresar", exact: true }).click();
  await expect(page).toHaveURL(/\/dashboard/);
}