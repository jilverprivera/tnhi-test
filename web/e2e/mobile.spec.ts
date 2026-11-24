import { expect, test } from "@playwright/test";

import { login } from "./helpers";

test("phone: bottom tab bar, no horizontal scroll, installable manifest", async ({ page }) => {
  await login(page, "COORDINATOR");
  const tabbar = page.getByRole("navigation", { name: "Principal" }).last();
  await expect(tabbar).toBeVisible();
  await tabbar.getByRole("link", { name: "Libro" }).click();
  await expect(page).toHaveURL(/\/ledger/);
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  expect(overflow).toBeLessThanOrEqual(0);
  const manifest = await page.request.get("/manifest.webmanifest");
  expect((await manifest.json()).display).toBe("standalone");
});
