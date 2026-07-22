const { test, expect } = require("@playwright/test");

const unsafePayload = new RegExp([
  "OPENAI" + "_API_KEY",
  "Authorization",
  "raw_provider_" + "prompt",
  "raw_provider_" + "response",
  "s" + "k-proj-",
  "s" + "k_live_",
  "s" + "k_test_",
  "Traceback",
].join("|"), "i");

async function selectMode(page, mode) {
  await page.goto("/product");
  await page.getByRole("radio", { name: mode === "mock" ? "Mock offline" : "Live OpenAI" }).check();
  await expect(page.locator("#ai-mode-status")).toContainText(mode === "mock" ? "Mock offline selected" : "Live mode is selected");
}

async function collectProviderRequest(page, action, expectedPath) {
  const requestPromise = page.waitForRequest((request) => request.method() === "POST" && request.url().includes(expectedPath));
  await action();
  const request = await requestPromise;
  const payload = request.postDataJSON();
  expect(JSON.stringify(payload)).not.toMatch(unsafePayload);
  return payload;
}

test.describe("Cookbook AI local troubleshooting", () => {
  test("product shell is visible, responsive, and links to the local AI workspace", async ({ page }) => {
    await page.goto("/product");
    await expect(page.getByRole("heading", { name: "Cookbook AI" })).toBeVisible();
    await expect(page.getByRole("radio", { name: "Live OpenAI" })).toBeVisible();
    await expect(page.getByRole("radio", { name: "Mock offline" })).toBeVisible();
    await expect(page.locator("#product-readiness")).toBeVisible();
    await expect(page.getByRole("link", { name: "Open AI Recipe Creator" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Open Cookbook" })).toBeVisible();

    const geometry = await page.evaluate(() => ({ scrollWidth: document.documentElement.scrollWidth, innerWidth: window.innerWidth }));
    expect(geometry.scrollWidth).toBeLessThanOrEqual(geometry.innerWidth);
    const actionsStayInCards = await page.locator(".product-card .card-action a").evaluateAll((links) => links.every((link) => {
      const card = link.closest(".product-card").getBoundingClientRect();
      const button = link.getBoundingClientRect();
      return button.left >= card.left && button.right <= card.right && button.bottom <= card.bottom;
    }));
    expect(actionsStayInCards).toBeTruthy();

    const cookbook = await page.request.get("/product/cookbook", { maxRedirects: 0 });
    expect([302, 307]).toContain(cookbook.status());
    expect(cookbook.headers()["location"]).toBe("http://127.0.0.1:3000/");

    await page.getByRole("link", { name: "Open AI Recipe Creator" }).click();
    await expect(page).toHaveURL(/\/demo$/);
    await expect(page.getByRole("link", { name: /Back to Cookbook AI Home/ })).toBeVisible();
  });

  test("mode state propagates and stale aliases normalize in demo", async ({ page }) => {
    await page.goto("/product");
    await page.evaluate(() => localStorage.setItem("cookbook-ai-mode", "live"));
    await page.goto("/demo");
    await expect(page.locator("#demo-ai-mode-status")).toContainText("Live OpenAI selected");
    await expect(page.locator("#demo-ai-mode-status")).toContainText("gpt-5.4-nano");

    await selectMode(page, "mock");
    await expect(page.locator('input[type="radio"][name="ai-mode"]')).toHaveCount(2);
    await expect(page.locator("select")).toHaveCount(0);
    await page.goto("/demo");
    await expect(page.locator("#demo-ai-mode-status")).toContainText("Mock offline selected");
    await expect(page.locator("#demo-ai-mode-status")).toContainText("mock-basic");
  });

  test("mock payloads are normalized for every provider-backed workflow", async ({ page }) => {
    await selectMode(page, "mock");
    await page.goto("/demo");
    const assertMock = (payload) => {
      expect(payload.provider_mode).toBe("mock");
      expect(payload.model).toBe("mock-basic");
    };

    assertMock(await collectProviderRequest(page, () => page.getByRole("button", { name: "Run importer" }).click(), "/ai/import-recipe"));
    assertMock(await collectProviderRequest(page, () => page.getByRole("button", { name: "Start session" }).click(), "/ai/recipe-session/start"));
    await expect(page.locator("#session-result")).toContainText("mock");
    assertMock(await collectProviderRequest(page, () => page.getByRole("button", { name: "Send follow-up" }).click(), "/message"));
    assertMock(await collectProviderRequest(page, () => page.getByRole("button", { name: "Ask saved recipes" }).click(), "/ai/ask"));
    assertMock(await collectProviderRequest(page, () => page.getByRole("button", { name: "Ask dataset" }).click(), "/dataset/ask"));
    assertMock(await collectProviderRequest(page, () => page.getByRole("button", { name: "Create meal plan" }).click(), "/ai/meal-plan"));
    await expect(page.locator("#import-result")).toContainText("mock");
    await expect(page.locator("#session-result")).toContainText("mock");
  });

  test("live selection sends approved payload and reports safe unavailable guidance on mock server", async ({ page }) => {
    await selectMode(page, "openai");
    await page.goto("/demo");
    const payload = await collectProviderRequest(page, () => page.getByRole("button", { name: "Run importer" }).click(), "/ai/import-recipe");
    expect(payload.provider_mode).toBe("openai");
    expect(payload.model).toBe("gpt-5.4-nano");
    await expect(page.locator("#import-result")).toContainText(/Live mode requires|Live provider configuration is unavailable/);
    await expect(page.locator("#import-result")).not.toContainText("mock-basic");
    await expect(page.locator("#import-result")).not.toContainText(unsafePayload);
  });
});
