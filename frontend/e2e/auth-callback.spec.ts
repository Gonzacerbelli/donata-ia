import { expect, request, test } from "@playwright/test";

test("el canje del código de Google se pide una sola vez", async ({ page }) => {
  const posts: string[] = [];
  await page.route("**/auth/exchange", async (route) => {
    posts.push(route.request().url());
    await route.fulfill({
      status: 401,
      contentType: "application/json",
      body: JSON.stringify({ detail: "El enlace de inicio de sesión ya no es válido o expiró" }),
    });
  });
  await page.goto("http://localhost:5173/auth/callback?code=prueba-123");
  await page.waitForTimeout(1500);
  console.log("EXCHANGE_POSTS=" + posts.length);
  expect(posts.length).toBe(1);
});

test("canje único y entrada al dashboard", async ({ page }) => {
  const api = await request.newContext();
  const login = await api.post("http://localhost:8000/auth/login", {
    data: { username: "admin", password: "cambiar-esta-clave" },
  });
  expect(login.ok()).toBeTruthy();
  const token = (await login.json()).access_token;
  await api.dispose();

  let posts = 0;
  await page.route("**/auth/exchange", async (route) => {
    posts += 1;
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        access_token: token,
        token_type: "bearer",
        user: { id: "1", email: "admin@local", name: "admin" },
      }),
    });
  });

  await page.goto("http://localhost:5173/auth/callback?code=prueba-456");
  await page.waitForURL("**/dashboard", { timeout: 10_000 });
  console.log("EXCHANGE_POSTS_OK=" + posts);
  expect(posts).toBe(1);
});
