import { expect, type Page } from "@playwright/test";

export async function login(page: Page, role: "CLERK" | "COORDINATOR") {
  await page.goto("/login");
  await page.getByText(role === "CLERK" ? "Radicación" : "Coordinación", { exact: true }).click();
  await page.getByLabel("Código de acceso").fill(role === "CLERK" ? "martha-demo" : "herrera-demo");
  const submit = page.getByRole("button", { name: "Ingresar" });
  await expect(submit).toHaveCSS("cursor", "pointer"); // buttons must look clickable
  await submit.click();
  await expect(page).toHaveURL(role === "CLERK" ? /\/inbox/ : /\/deadlines/);
  // The header always says who is signed in
  const name = role === "CLERK" ? "Martha Rojas" : "Claudia Herrera";
  await expect(page.getByRole("banner").getByLabel(new RegExp(`Sesión de ${name}`))).toBeVisible();
}
