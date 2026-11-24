import { expect, test } from "@playwright/test";

import { login } from "./helpers";

test("the coordinator has her own menu and verifies the held invoice", async ({ page }) => {
  await test.step("the clerk files the suspicious invoice (it stays held)", async () => {
    await login(page, "CLERK");
    await page.getByRole("button", { name: "Leer buzón" }).click();
    await expect(page.getByText(/documentos nuevos|No hay correos nuevos/)).toBeVisible();
    await page.getByRole("link", { name: /cambio de cuenta/ }).click();
    await page.getByRole("button", { name: "Alertar a la Dra. Herrera" }).click();
    await page.getByRole("button", { name: "Enviar alerta" }).click();
    await expect(page.getByText("Alerta enviada a la Dra. Herrera")).toBeVisible();
    const clerkNav = page.getByRole("complementary").getByRole("navigation", { name: "Principal" });
    await expect(clerkNav.getByRole("link", { name: "Por verificar" })).toHaveCount(0);
    await page.getByRole("button", { name: "Cerrar sesión" }).first().click();
    await expect(page).toHaveURL(/\/login/);
  });

  await test.step("her menu and home are hers, with what waits on her", async () => {
    await login(page, "COORDINATOR");
    const nav = page.getByRole("complementary").getByRole("navigation", { name: "Principal" });
    await expect(nav.getByRole("link")).toHaveText(["Vencimientos", "Por verificar", "Libro", "Bandeja", "Cumplimiento"]);
    await expect(page.getByRole("link", { name: /1 factura por verificar/ })).toBeVisible();
  });

  await test.step("she compares with the master and releases it after the call", async () => {
    await page.getByRole("link", { name: /1 factura por verificar/ }).click();
    await expect(page).toHaveURL(/\/verifications/);
    await expect(page.getByText("0013-0456-78-0100012345").first()).toBeVisible();
    await page.getByRole("button", { name: "Verificada: liberar" }).click();
    await page.getByLabel("Nota de la verificación").fill("Hablé con tesorería de Aseo Integral al número del maestro");
    await page.getByRole("button", { name: "Liberar", exact: true }).click();
    await expect(page.getByText(/liberada hacia Cuentas por pagar/)).toBeVisible();
    await expect(page.getByText("Liberada para pago").first()).toBeVisible();
  });

  await test.step("the ledger shows it delivered, and filters use design-system selects", async () => {
    await page.goto("/ledger?q=AIB-2026-1189");
    await expect(page.getByRole("cell", { name: /Entregado/ })).toBeVisible();
    await page.getByRole("combobox", { name: "Dependencia" }).click();
    await expect(page.getByRole("listbox")).toBeVisible();
    await page.getByRole("option", { name: "Jurídica" }).click();
    await page.getByRole("button", { name: "Buscar" }).click();
    await expect(page).toHaveURL(/department=LEGAL/);
  });
});

test("an open session lands on its role's home", async ({ page }) => {
  await login(page, "COORDINATOR");
  await page.goto("/");
  await expect(page).toHaveURL(/\/deadlines/);
  await page.goto("/login");
  await expect(page).toHaveURL(/\/deadlines/);
});

test("compliance: retention schedule and a data subject request", async ({ page }) => {
  await login(page, "COORDINATOR");
  await page.goto("/compliance");
  await expect(page.getByRole("heading", { name: "Tabla de retención documental" })).toBeVisible();
  await expect(page.getByText(/Ningún documento ha cumplido su tiempo de retención/)).toBeVisible();
  await page.getByLabel("Cédula o correo del titular").fill("80.123.456");
  await page.getByRole("button", { name: "Buscar" }).click();
  await expect(page.getByText(/Titular \*\*\*\.456/)).toBeVisible();
  await expect(page.getByText(/Responder a más tardar el/)).toBeVisible();
});
