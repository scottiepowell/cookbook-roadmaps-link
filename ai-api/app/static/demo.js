const forbiddenText = [
  "OPENAI_API_KEY",
  "Authorization:",
  "CLOUDFLARE_TUNNEL_TOKEN",
  "AWS_SECRET_ACCESS_KEY",
  "AWS_ACCESS_KEY_ID",
  ".env",
];

document.getElementById("check-status").addEventListener("click", checkStatus);
document.querySelector('[data-action="import"]').addEventListener("click", runImporter);
document.querySelector('[data-action="cookbook-query"]').addEventListener("click", runAsk);
document.querySelector('[data-action="dataset-search"]').addEventListener("click", runDatasetSearch);
document.querySelector('[data-action="dataset-rag"]').addEventListener("click", runDatasetAsk);
document.querySelector('[data-action="meal-plan"]').addEventListener("click", runMealPlan);

checkStatus();

async function checkStatus() {
  setText("health-output", "Checking...");
  setText("config-output", "Checking...");
  await renderPre("health-output", requestJson("/health"));
  await renderPre("config-output", requestJson("/ai/config"));
}

async function runImporter() {
  const payload = {
    text: document.getElementById("import-text").value,
    source: "sidecar demo",
  };
  await renderResult("import-result", requestJson("/ai/import-recipe", postOptions(payload)), {
    answer: (data) => data.draft?.title || "Importer returned a draft.",
    meta: providerMeta,
    citations: () => [],
  });
}

async function runAsk() {
  const payload = {
    question: document.getElementById("cookbook-question").value,
    limit: 2,
  };
  await renderResult("cookbook-result", requestJson("/ai/ask", postOptions(payload)), {
    answer: (data) => data.answer,
    meta: providerMeta,
    citations: (data) => (data.citations || []).map((citation) => `${citation.title} (${citation.recipe_id})`),
  });
}

async function runDatasetSearch() {
  const params = new URLSearchParams({
    q: document.getElementById("dataset-search-query").value,
    limit: "3",
    dataset_limit: "25",
  });
  await renderResult("dataset-search-result", requestJson(`/dataset/search?${params.toString()}`), {
    answer: (data) => `${data.count} dataset result(s)`,
    meta: (data) => `indexed=${data.index?.document_count ?? 0}; warnings=${(data.warnings || []).length}`,
    citations: (data) => (data.results || []).map((result) => `${result.title} (${result.source_id})`),
  });
}

async function runDatasetAsk() {
  const payload = {
    question: document.getElementById("dataset-question").value,
    limit: 2,
    dataset_limit: 25,
  };
  await renderResult("dataset-rag-result", requestJson("/dataset/ask", postOptions(payload)), {
    answer: (data) => data.answer,
    meta: (data) => `${providerMeta(data)}; retrieved=${data.retrieval?.retrieved_count ?? 0}`,
    citations: (data) => (data.citations || []).map((citation) => `${citation.title} (${citation.source_id})`),
  });
}

async function runMealPlan() {
  const payload = {
    days: 1,
    meals_per_day: 1,
    preferences: document.getElementById("meal-plan-preferences").value,
    candidate_limit: 3,
  };
  await renderResult("meal-plan-result", requestJson("/ai/meal-plan", postOptions(payload)), {
    answer: (data) => {
      const meals = (data.plan?.days || []).flatMap((day) => day.meals || []);
      return meals.length ? meals.map((meal) => `${meal.slot}: ${meal.title}`).join("\n") : "No meal slots returned.";
    },
    meta: (data) => `${providerMeta(data)}; candidates=${data.selection?.candidate_count ?? 0}`,
    citations: (data) => (data.citations || []).map((citation) => `${citation.title} (${citation.recipe_id})`),
  });
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, options);
  const text = await response.text();
  const data = parseJson(text);
  if (!response.ok) {
    const detail = data?.detail || response.statusText || "Request failed.";
    throw new Error(friendlyError(response.status, detail));
  }
  return data;
}

function postOptions(payload) {
  return {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(payload),
  };
}

async function renderPre(id, promise) {
  try {
    const data = await promise;
    setText(id, safeJson(data));
  } catch (error) {
    setText(id, error.message);
  }
}

async function renderResult(id, promise, view) {
  const target = document.getElementById(id);
  target.innerHTML = '<div class="summary">Running...</div>';
  try {
    const data = await promise;
    target.innerHTML = "";
    target.append(summary(view.answer(data)));
    target.append(meta(view.meta(data)));
    target.append(list("Citations / Provenance", view.citations(data)));
    target.append(list("Warnings", data.warnings || []));
    target.append(preview(data));
  } catch (error) {
    target.innerHTML = "";
    const node = summary(error.message);
    node.classList.add("error");
    target.append(node);
  }
}

function summary(text) {
  const node = document.createElement("div");
  node.className = "summary";
  node.textContent = text || "No answer text returned.";
  return node;
}

function meta(text) {
  const node = document.createElement("div");
  node.className = "meta";
  node.textContent = text || "No provider metadata.";
  return node;
}

function list(title, items) {
  const wrapper = document.createElement("div");
  const heading = document.createElement("div");
  heading.className = "meta";
  heading.textContent = title;
  wrapper.append(heading);
  if (!items.length) {
    const empty = document.createElement("div");
    empty.className = "meta";
    empty.textContent = "None";
    wrapper.append(empty);
    return wrapper;
  }
  const listNode = document.createElement("ul");
  for (const item of items) {
    const child = document.createElement("li");
    child.textContent = item;
    listNode.append(child);
  }
  wrapper.append(listNode);
  return wrapper;
}

function preview(data) {
  const node = document.createElement("pre");
  node.textContent = safeJson(data);
  return node;
}

function providerMeta(data) {
  const provider = data.provider || "none";
  const model = data.model || "none";
  const warnings = (data.warnings || []).length;
  return `provider=${provider}; model=${model}; warnings=${warnings}`;
}

function friendlyError(status, detail) {
  if (status === 422) {
    return `${detail} Configure local saved recipe or dataset fixtures, then retry.`;
  }
  return `${detail} (HTTP ${status})`;
}

function parseJson(text) {
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}

function safeJson(data) {
  const text = JSON.stringify(data, null, 2);
  for (const marker of forbiddenText) {
    if (text.includes(marker)) {
      return "Response hidden because it contained a forbidden sensitive marker.";
    }
  }
  return text;
}

function setText(id, value) {
  document.getElementById(id).textContent = value;
}
