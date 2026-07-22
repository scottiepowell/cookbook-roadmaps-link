import { expect, test } from "@playwright/test";

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

type ProviderPayload = { provider_mode?: string; model?: string };

async function selectMode(page, mode: "mock" | "openai") {
  await page.goto("/product");
  await page.getByRole("radio", { name: mode === "mock" ? "Mock offline" : "Live OpenAI" }).check();
  await expect(page.locator("#ai-mode-status")).toContainText(
    mode === "mock" ? "Mock offline selected" : "Live mode is selected",
  );
}

async function captureJsonPost(page, urlPart: string, action: () => Promise<void>): Promise<ProviderPayload> {
  const requestPromise = page.waitForRequest((request) => request.method() === "POST" && request.url().includes(urlPart));
  await action();
  const request = await requestPromise;
  const payload = request.postDataJSON() as ProviderPayload;
  expect(JSON.stringify(payload)).not.toMatch(unsafePayload);
  return payload;
}

function expectMode(payload: ProviderPayload, mode: "mock" | "openai") {
  expect(payload.provider_mode).toBe(mode);
  expect(payload.model).toBe(mode === "openai" ? "gpt-5.4-nano" : "mock-basic");
  expect(payload).not.toEqual({ provider_mode: "live", model: "mock-basic" });
}

test.describe("Cookbook AI Live/Mock toggle troubleshooting", () => {
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

    const cookbook = await page.request.get("/product/cookbook", { maxRedirects: 0 });
    expect([302, 307]).toContain(cookbook.status());
    expect(cookbook.headers()["location"]).toBe("http://127.0.0.1:3000/");

    await page.getByRole("link", { name: "Open AI Recipe Creator" }).click();
    await expect(page).toHaveURL(/\/demo$/);
    await expect(page.getByRole("link", { name: /Back to Cookbook AI Home/ })).toBeVisible();
  });

  test("all persisted aliases normalize to approved mode/model preferences", async ({ page }) => {
    for (const [stored, expectedMode, expectedModel] of [
      ["live", "openai", "gpt-5.4-nano"],
      ["openai", "openai", "gpt-5.4-nano"],
      ["mock", "mock", "mock-basic"],
      ["offline", "mock", "mock-basic"],
    ]) {
      await page.goto("/product");
      await page.evaluate(([key, value]) => localStorage.setItem(key, value), ["cookbook-ai-mode", stored]);
      await page.goto("/demo");
      await expect(page.locator("#demo-ai-mode-status")).toContainText(expectedMode === "openai" ? "Live OpenAI selected" : "Mock offline selected");
      await expect(page.locator("#demo-ai-mode-status")).toContainText(expectedModel);
    }

    await page.goto("/product");
    await expect(page.locator('input[type="radio"][name="ai-mode"]')).toHaveCount(2);
    await expect(page.locator("select")).toHaveCount(0);
    await expect(page.locator("body")).toContainText("gpt-5.4-nano");
  });

  test("mock selection sends mock-basic for every provider-backed workflow", async ({ page }) => {
    await selectMode(page, "mock");
    await page.goto("/demo");

    expectMode(await captureJsonPost(page, "/ai/import-recipe", () => page.getByRole("button", { name: "Run importer" }).click()), "mock");
    expectMode(await captureJsonPost(page, "/ai/recipe-session/start", () => page.getByRole("button", { name: "Start session" }).click()), "mock");
    await expect(page.locator("#session-result")).toContainText("mock");
    expectMode(await captureJsonPost(page, "/message", () => page.getByRole("button", { name: "Send follow-up" }).click()), "mock");
    expectMode(await captureJsonPost(page, "/ai/ask", () => page.getByRole("button", { name: "Ask saved recipes" }).click()), "mock");
    expectMode(await captureJsonPost(page, "/dataset/ask", () => page.getByRole("button", { name: "Ask dataset" }).click()), "mock");
    expectMode(await captureJsonPost(page, "/ai/meal-plan", () => page.getByRole("button", { name: "Create meal plan" }).click()), "mock");

    await expect(page.locator("#import-result")).toContainText("mock");
    await expect(page.locator("#session-result")).toContainText("mock");
  });

  test("live selection sends gpt-5.4-nano for every workflow and reports unavailable safely on a mock server", async ({ page }) => {
    // Start a session in mock mode so the live-mode follow-up can use a real interaction id.
    await selectMode(page, "mock");
    await page.goto("/demo");
    expectMode(await captureJsonPost(page, "/ai/recipe-session/start", () => page.getByRole("button", { name: "Start session" }).click()), "mock");

    // Keep the mock-created interaction id in this page while changing the
    // request-scoped browser preference to Live. This proves a follow-up uses
    // the selected mode rather than the process-wide mock provider.
    await page.evaluate(() => localStorage.setItem("cookbook-ai-mode", "openai"));
    expectMode(await captureJsonPost(page, "/ai/import-recipe", () => page.getByRole("button", { name: "Run importer" }).click()), "openai");
    expectMode(await captureJsonPost(page, "/ai/recipe-session/start", () => page.getByRole("button", { name: "Start session" }).click()), "openai");
    expectMode(await captureJsonPost(page, "/message", () => page.getByRole("button", { name: "Send follow-up" }).click()), "openai");
    expectMode(await captureJsonPost(page, "/ai/ask", () => page.getByRole("button", { name: "Ask saved recipes" }).click()), "openai");
    expectMode(await captureJsonPost(page, "/dataset/ask", () => page.getByRole("button", { name: "Ask dataset" }).click()), "openai");
    expectMode(await captureJsonPost(page, "/ai/meal-plan", () => page.getByRole("button", { name: "Create meal plan" }).click()), "openai");

    await expect(page.locator("#import-result")).toContainText("Live mode is selected but unavailable because this local server was started without live OpenAI opt-in/configuration.");
    await expect(page.locator("#import-result")).not.toContainText("mock-basic");
    await expect(page.locator("#import-result")).not.toContainText(unsafePayload);
  });
});
