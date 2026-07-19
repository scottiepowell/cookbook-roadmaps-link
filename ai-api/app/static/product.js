async function loadProductReadiness() {
  const target = document.getElementById("product-readiness");
  try {
    const response = await fetch("/demo/readiness");
    if (!response.ok) throw new Error("Readiness is unavailable.");
    const data = await response.json();
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
