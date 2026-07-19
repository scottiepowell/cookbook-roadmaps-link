async function loadProductReadiness() {
  const target = document.getElementById("product-readiness");
  try {
    const response = await fetch("/demo/readiness");
    if (!response.ok) throw new Error("Readiness is unavailable.");
    const data = await response.json();
    const status = document.getElementById("ai-mode-status");
    const liveAvailable = data.provider?.mode === "openai" && data.provider?.model === "gpt-5.4-nano";
    const updateMode = () => {
      const selected = document.querySelector('input[name="ai-mode"]:checked')?.value;
      status.textContent = selected === "mock" ? "Mock offline selected: free, deterministic local demo mode." : liveAvailable ? "Live OpenAI selected and available using gpt-5.4-nano." : "Live OpenAI selected but unavailable: start the sidecar with explicit live opt-in and approved budget configuration. Current runtime remains unchanged.";
    };
    document.querySelectorAll('input[name="ai-mode"]').forEach((input) => input.addEventListener("change", updateMode));
    document.querySelectorAll('input[name="ai-mode"]').forEach((input) => input.addEventListener("change", () => localStorage.setItem("cookbook-ai-mode", input.value)));
    const saved = localStorage.getItem("cookbook-ai-mode");
    if (saved) document.querySelector(`input[name="ai-mode"][value="${saved}"]`)?.click();
    updateMode();
    target.className = "result";
    const mode = data.provider?.mode || "unknown";
    const safety = data.provider?.offline_demo_mode ? "Mock/offline default is active." : "Check provider configuration before a live demo.";
    const reset = data.saved_recipes?.available && data.dataset?.available ? "Fixtures are ready." : "Fixtures are missing; restart scripts\\start-ai-demo-local.ps1.";
    target.textContent = `Provider: ${mode} (${data.provider?.model || "unknown"}). Saved recipes: ${data.saved_recipes?.available ? "ready" : "missing"}. Dataset: ${data.dataset?.available ? "ready" : "missing"}. ${safety} ${reset}`;
  } catch (_) {
    target.className = "result";
    target.textContent = "Readiness could not be loaded. Start the local AI sidecar with scripts\\start-ai-demo-local.ps1, then refresh.";
  }
}

loadProductReadiness();
