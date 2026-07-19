async function loadProductReadiness() {
  const target = document.getElementById("product-readiness");
  try {
    const response = await fetch("/demo/readiness");
    if (!response.ok) throw new Error("Readiness is unavailable.");
    const data = await response.json();
    target.className = "result";
    target.textContent = `Provider: ${data.provider?.mode || "unknown"} (${data.provider?.model || "unknown"}). Saved recipes: ${data.saved_recipes?.available ? "ready" : "missing"}. Dataset: ${data.dataset?.available ? "ready" : "missing"}.`;
  } catch (_) {
    target.className = "result";
    target.textContent = "Readiness could not be loaded. Start the local AI sidecar with scripts\\start-ai-demo-local.ps1, then refresh.";
  }
}

loadProductReadiness();
