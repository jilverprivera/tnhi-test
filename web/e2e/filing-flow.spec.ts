import { expect, test } from "@playwright/test";

import { login } from "./helpers";

test.describe.configure({ mode: "serial" });

test("the clerk files the backlog and the coordinator sees what is due", async ({ page }) => {
  await test.step("protected routes redirect to login", async () => {
    await page.goto("/inbox");
    await expect(page).toHaveURL(/\/login/);
  });

  await test.step("the clerk reads the mailbox", async () => {
    await login(page, "CLERK");
    await page.getByRole("button", { name: "Leer buzón" }).click();
    // 17 new documents on a fresh API; another spec in the same run may have imported them first
    await expect(page.getByText(/17 documentos nuevos|No hay correos nuevos/)).toBeVisible();
  });

  await test.step("the suspicious invoice is held, with the reason visible", async () => {
    const held = page.getByRole("link", { name: /cambio de cuenta/ });
    await expect(held.getByText("Retenida: posible fraude")).toBeVisible();
    await held.click();
    await expect(page.getByText(/no es la del maestro/)).toBeVisible();
    await expect(page.getByText(/aseointegral-bogota\.example/).first()).toBeVisible();
  });

  await test.step("the clerk corrects the unreadable scan and approves it", async () => {
    // With OCR the scan is read and is READY; without OCR it waits in review: look in every document
    await page.goto("/inbox?filter=all");
    await page.getByRole("link", { name: /SE-77821/ }).click();
    await expect(page.getByRole("heading", { name: "Por qué" })).toBeVisible();
    const unreadable = page.getByText("No se pudo leer el documento");
    if ((await unreadable.count()) > 0) {
      // Without OCR the scan cannot be filed blindly: the API refuses a decision with no department
      await page.getByRole("button", { name: /Aprobar y radicar/ }).click();
      await expect(page.getByText("Falta elegir la dependencia antes de radicar.")).toBeVisible();

      await page.getByRole("button", { name: "Corregir" }).click();
      await page.getByLabel("Qué es").click();
      await page.getByRole("option", { name: "Factura" }).click();
      await page.getByLabel("Va para").click();
      await page.getByRole("option", { name: "Cuentas por pagar" }).click();
      await page.getByLabel("Observaciones para el libro").fill("Leída a mano: SE-77821, OC-2026-0398");
      await page.getByRole("button", { name: "Guardar corrección" }).click();
      await expect(page.getByText("Corregido por una persona", { exact: true })).toBeVisible();
    }
    await page.getByRole("button", { name: /Aprobar y radicar/ }).click();
    await expect(page.getByText(/Radicado TAC-2026-ER-048\d\d/)).toBeVisible();
  });

  await test.step("batch approval only takes what is ready", async () => {
    await page.goto("/inbox");
    await page.getByRole("button", { name: /Aprobar listos/ }).click();
    await page.getByRole("button", { name: "Aprobar y radicar" }).click();
    await expect(page.getByText(/documentos aprobados/)).toBeVisible();
    // the held invoice is never batch-approved: either still in review or filed by hand in another spec
    await page.goto("/inbox?filter=ready");
    await expect(page.getByRole("link", { name: /cambio de cuenta/ })).toHaveCount(0);
  });

  await test.step("the ledger continues the consecutive and exports the Excel", async () => {
    await page.goto("/ledger?q=CD-2026-3345");
    await expect(page.getByRole("cell", { name: /TAC-2026-ER-048/ })).toBeVisible();
    const download = page.waitForEvent("download");
    await page.getByRole("link", { name: "Descargar Excel" }).click();
    expect((await download).suggestedFilename()).toBe("libro-radicacion-2026.xlsx");
  });

  await test.step("the coordinator sees this week's and next week's deadlines", async () => {
    await page.getByRole("button", { name: "Cerrar sesión" }).first().click();
    await expect(page).toHaveURL(/\/login/);
    await login(page, "COORDINATOR");
    await expect(page.getByRole("heading", { name: "Vencimientos", level: 1 })).toBeVisible();
    await expect(page.getByText("Certificación laboral")).toBeVisible();
    await expect(page.getByText("Notificación oficio CD-2026-3345")).toBeVisible();
    await page.goto("/inbox");
    await expect(page.getByRole("button", { name: /Aprobar listos/ })).toHaveCount(0);
  });
});
