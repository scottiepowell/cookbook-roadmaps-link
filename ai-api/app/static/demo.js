const forbiddenText = [
  "OPENAI" + "_API_KEY",
  "s" + "k-",
  "Authorization" + ":",
  "CLOUDFLARE" + "_TUNNEL_TOKEN",
  "AWS" + "_SECRET_ACCESS_KEY",
  "AWS" + "_ACCESS_KEY_ID",
  ".e" + "nv",
];

const workflows = {
  importer: {
    card: "importer",
    result: "import-result",
    button: '[data-action="importer-run"]',
    reset: '[data-reset="importer"]',
    input: "import-text",
    sample: "Lemon beans: warm canned beans with olive oil and lemon juice. Serve with herbs.",
  },
  cookbook: {
    card: "cookbook",
    result: "cookbook-result",
    button: '[data-action="cookbook-run"]',
    reset: '[data-reset="cookbook"]',
    input: "cookbook-question",
    sample: "What saved recipe uses lemon?",
  },
  datasetSearch: {
    card: "dataset-search",
    result: "dataset-search-result",
    button: '[data-action="dataset-search-run"]',
    reset: '[data-reset="dataset-search"]',
    input: "dataset-search-query",
    sample: "tomato pasta",
  },
  datasetRag: {
    card: "dataset-rag",
    result: "dataset-rag-result",
    button: '[data-action="dataset-rag-run"]',
    reset: '[data-reset="dataset-rag"]',
    input: "dataset-question",
    sample: "What indexed recipe uses tomato pasta?",
  },
  mealPlan: {
    card: "meal-plan",
    result: "meal-plan-result",
    button: '[data-action="meal-plan-run"]',
    reset: '[data-reset="meal-plan"]',
    input: "meal-plan-preferences",
    sample: "lemon dinner",
  },
  recipeSession: {
    card: "recipe-session",
    result: "session-result",
    button: '[data-action="session-start"]',
    reset: '[data-reset="recipe-session"]',
    input: "session-start-text",
    followup: "session-followup-text",
    sample: "classic baked cheesecake for 4 with cream cheese sugar eggs vanilla graham cracker crust bake and chill overnight",
    followupSample: "actually make it no-bake",
  },
};

let activeRecipeSessionId = null;

document.getElementById("refresh-readiness").addEventListener("click", refreshReadiness);
document.getElementById("refresh-usage-report").addEventListener("click", refreshUsageReport);
document.querySelector(workflows.importer.button).addEventListener("click", runImporter);
document.querySelector('[data-action="session-start"]').addEventListener("click", startRecipeSession);
document.querySelector('[data-action="session-message"]').addEventListener("click", sendRecipeSessionMessage);
document.querySelector('[data-action="session-get"]').addEventListener("click", getRecipeSession);
document.querySelector('[data-action="session-finalize"]').addEventListener("click", finalizeRecipeSession);
document.querySelector(workflows.cookbook.button).addEventListener("click", runCookbookQuery);

function providerPreference() {
  const selected = localStorage.getItem("cookbook-ai-mode") || "live";
  const mode = selected === "live" || selected === "openai" ? "openai" : "mock";
  return { provider_mode: mode, model: mode === "openai" ? "gpt-5.4-nano" : "mock-basic" };
}
document.querySelector(workflows.datasetSearch.button).addEventListener("click", runDatasetSearch);
document.querySelector(workflows.datasetRag.button).addEventListener("click", runDatasetRag);
document.querySelector(workflows.mealPlan.button).addEventListener("click", runMealPlan);

for (const workflow of Object.values(workflows)) {
  document.querySelector(workflow.reset).addEventListener("click", () => resetWorkflow(workflow));
}

refreshReadiness();
refreshUsageReport();

async function refreshReadiness() {
  const grid = document.getElementById("readiness-grid");
  grid.innerHTML = readinessSkeleton();
  try {
    const data = await requestJson("/demo/readiness", {}, "readiness");
    grid.innerHTML = "";
    grid.append(
      readinessCard("Sidecar", data.service?.ok, data.service?.ok ? "Healthy" : "Unavailable", "FastAPI sidecar status."),
      readinessCard(
        "Provider",
        true,
        `${data.provider?.mode || "unknown"} / ${data.provider?.model || "unknown"}`,
        data.provider?.offline_demo_mode ? "Offline mock mode is active." : "Live provider mode may be active.",
      ),
      readinessCard("Saved recipes", data.saved_recipes?.available, `${data.saved_recipes?.count || 0} recipe(s)`, data.saved_recipes?.message),
      readinessCard("Dataset", data.dataset?.available, data.dataset?.available ? "Available" : "Unavailable", data.dataset?.message),
      readinessCard(
        "Invite sessions",
        data.invite_sessions?.available,
        data.invite_sessions?.available ? "Enabled" : "Disabled",
        data.invite_sessions?.message || "Invite-only demo sessions are disabled by default.",
      ),
    );
    document.getElementById("readiness-updated").textContent = "Checked just now";
  } catch (error) {
    grid.innerHTML = "";
    grid.append(readinessCard("Readiness", false, "Unable to check", error.message));
  }
}

async function refreshUsageReport() {
  const grid = document.getElementById("usage-report-grid");
  grid.innerHTML = usageReportSkeleton();
  try {
    const data = await requestJson("/ai/admin/usage-report", {}, "usage-report");
    grid.innerHTML = "";
    grid.append(
      readinessCard("Report", true, "Available", "Safe local/operator usage summary."),
      readinessCard(
        "Sessions",
        true,
        `${data.summary?.active_session_count ?? 0} active`,
        `${data.summary?.expired_session_count ?? 0} expired, ${data.summary?.revoked_session_count ?? 0} revoked, ${data.summary?.completed_session_count ?? 0} completed.`,
      ),
      readinessCard(
        "Provider calls",
        true,
        `Allowed ${data.summary?.provider_calls_allowed ?? 0}`,
        `Blocked ${data.summary?.provider_calls_blocked ?? 0}, skipped ${data.summary?.provider_calls_skipped ?? 0}, failed ${data.summary?.provider_calls_failed ?? 0}.`,
      ),
      readinessCard(
        "Budget",
        true,
        formatUsd(data.summary?.estimated_cost_usd_total),
        `Remaining ${formatUsd(data.summary?.remaining_estimated_cost_usd_total)}; threshold warnings ${data.summary?.threshold_warning_count ?? 0}.`,
      ),
    );
    document.getElementById("usage-report-updated").textContent = "Checked just now";
  } catch (error) {
    grid.innerHTML = "";
    grid.append(readinessCard("Usage report", false, "Locked", error.message));
    document.getElementById("usage-report-updated").textContent = "Blocked";
  }
}

async function runImporter() {
  const workflow = workflows.importer;
  const payload = {
    ...providerPreference(),
    text: document.getElementById(workflow.input).value,
    source: "sidecar demo",
  };
  await runWorkflow(workflow, requestJson("/ai/import-recipe", postOptions(payload), "importer"), {
    title: (data) => data.draft?.title || "Structured recipe draft",
    answer: importerAnswer,
    meta: (data) => ({
      ...providerMetadata(data),
      servings: data.draft?.servings ?? "none",
      retrieved: data.retrieval?.retrieved_count ?? 0,
      packed_examples: data.retrieval?.packed_count ?? 0,
      citations: (data.citations || []).length,
      dataset_limit: data.retrieval?.dataset_limit ?? "none",
    }),
    evidence: importerEvidenceSection,
  });
}

async function startRecipeSession() {
  const workflow = workflows.recipeSession;
  const payload = {
    ...providerPreference(),
    text: document.getElementById(workflow.input).value,
    source: "sidecar demo recipe session",
  };
  await runSessionWorkflow(
    workflow,
    requestJson("/ai/recipe-session/start", postOptions(payload), "recipe-session-start"),
    "Starting session...",
  );
}

async function sendRecipeSessionMessage() {
  const workflow = workflows.recipeSession;
  if (!activeRecipeSessionId) {
    renderError(document.getElementById(workflow.result), "Start a recipe session before sending a follow-up message.");
    return;
  }
  const payload = {
    ...providerPreference(),
    text: document.getElementById(workflow.followup).value,
  };
  await runSessionWorkflow(
    workflow,
    requestJson(`/ai/recipe-session/${encodeURIComponent(activeRecipeSessionId)}/message`, postOptions(payload), "recipe-session-message"),
    "Sending follow-up...",
  );
}

async function getRecipeSession() {
  const workflow = workflows.recipeSession;
  if (!activeRecipeSessionId) {
    renderError(document.getElementById(workflow.result), "Start a recipe session before loading session state.");
    return;
  }
  await runSessionWorkflow(
    workflow,
    requestJson(`/ai/recipe-session/${encodeURIComponent(activeRecipeSessionId)}`, {}, "recipe-session-get"),
    "Loading session...",
  );
}

async function finalizeRecipeSession() {
  const workflow = workflows.recipeSession;
  if (!activeRecipeSessionId) {
    renderError(document.getElementById(workflow.result), "Start a recipe session before finalizing for demo.");
    return;
  }
  await runSessionWorkflow(
    workflow,
    requestJson(`/ai/recipe-session/${encodeURIComponent(activeRecipeSessionId)}/finalize`, postOptions({format: "draft_json"}), "recipe-session-finalize"),
    "Finalizing for demo...",
  );
}

async function runCookbookQuery() {
  const workflow = workflows.cookbook;
  const payload = {
    ...providerPreference(),
    question: document.getElementById(workflow.input).value,
    limit: 2,
  };
  await runWorkflow(workflow, requestJson("/ai/ask", postOptions(payload), "cookbook-query"), {
    title: () => "Saved-recipe answer",
    answer: (data) => data.answer,
    meta: (data) => ({...providerMetadata(data), retrieved: data.retrieval?.retrieved_count ?? 0}),
    citations: (data) => (data.citations || []).map((citation) => ({
      title: citation.title,
      detail: `Recipe ${citation.recipe_id}`,
      snippet: citation.snippet,
    })),
  });
}

async function runDatasetSearch() {
  const workflow = workflows.datasetSearch;
  const params = new URLSearchParams({
    q: document.getElementById(workflow.input).value,
    limit: "3",
    dataset_limit: "25",
  });
  await runWorkflow(workflow, requestJson(`/dataset/search?${params.toString()}`, {}, "dataset-search"), {
    title: (data) => `${data.count} dataset result(s)`,
    answer: (data) => (data.results || []).map((result) => result.title).join("\n") || "No dataset matches returned.",
    meta: (data) => ({
      indexed: data.index?.document_count ?? 0,
      retrieved: data.count,
      warnings: (data.warnings || []).length,
      ...cacheMetadata(data.cache),
    }),
    citations: (data) => (data.results || []).map((result) => ({
      title: result.title,
      detail: `Source ${result.source_id}; ${result.provenance?.license || "license unavailable"}`,
      snippet: result.snippet,
    })),
  });
}

async function runDatasetRag() {
  const workflow = workflows.datasetRag;
  const payload = {
    ...providerPreference(),
    question: document.getElementById(workflow.input).value,
    limit: 2,
    dataset_limit: 25,
  };
  await runWorkflow(workflow, requestJson("/dataset/ask", postOptions(payload), "dataset-rag"), {
    title: () => "Dataset-grounded answer",
    answer: (data) => data.answer,
    meta: (data) => ({...providerMetadata(data), retrieved: data.retrieval?.retrieved_count ?? 0, ...cacheMetadata(data.retrieval?.index?.cache)}),
    citations: (data) => (data.citations || []).map((citation) => ({
      title: citation.title,
      detail: `Source ${citation.source_id}; ${citation.provenance?.license || "license unavailable"}`,
      snippet: citation.snippet,
    })),
  });
}

async function runMealPlan() {
  const workflow = workflows.mealPlan;
  const payload = {
    ...providerPreference(),
    days: 1,
    meals_per_day: 1,
    preferences: document.getElementById(workflow.input).value,
    candidate_limit: 3,
  };
  await runWorkflow(workflow, requestJson("/ai/meal-plan", postOptions(payload), "meal-plan"), {
    title: () => "Meal plan",
    answer: (data) => {
      const meals = (data.plan?.days || []).flatMap((day) => day.meals || []);
      return meals.length ? meals.map((meal) => `${meal.slot}: ${meal.title}\n${meal.reason}`).join("\n\n") : "No meal slots returned.";
    },
    meta: (data) => ({...providerMetadata(data), candidates: data.selection?.candidate_count ?? 0}),
    citations: (data) => (data.citations || []).map((citation) => ({
      title: citation.title,
      detail: `Recipe ${citation.recipe_id}`,
      snippet: citation.snippet,
    })),
  });
}

async function runWorkflow(workflow, promise, view) {
  setLoading(workflow, true);
  const target = document.getElementById(workflow.result);
  target.className = "result";
  target.innerHTML = '<div class="answer-card">Running request...</div>';
  try {
    const data = await promise;
    renderSuccess(target, data, view);
  } catch (error) {
    renderError(target, error.message);
  } finally {
    setLoading(workflow, false);
  }
}

async function runSessionWorkflow(workflow, promise, loadingLabel) {
  setLoading(workflow, true);
  const target = document.getElementById(workflow.result);
  target.className = "result";
  target.innerHTML = `<div class="answer-card">${loadingLabel || "Running session request..."}</div>`;
  try {
    const data = await promise;
    if (data.interaction_id) {
      activeRecipeSessionId = data.interaction_id;
    }
    renderRecipeSession(target, data);
  } catch (error) {
    renderError(target, error.message);
  } finally {
    setLoading(workflow, false);
  }
}

async function requestJson(url, options = {}, workflow = "manual") {
  const mergedOptions = withWorkflowHeader(options, workflow);
  const response = await fetch(url, mergedOptions);
  const text = await response.text();
  const data = parseJson(text);
  if (!response.ok) {
    const detail = data?.detail || response.statusText || "Request failed.";
    throw new Error(friendlyError(response.status, detail));
  }
  return sanitizeData(data);
}

function postOptions(payload) {
  return {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(payload),
  };
}

function withWorkflowHeader(options, workflow) {
  const headers = new Headers(options.headers || {});
  headers.set("X-AI-Demo-Workflow", workflow);
  return {...options, headers};
}

function renderSuccess(target, data, view) {
  target.innerHTML = "";
  if (data.input_quality?.status === "needs_clarification") {
    target.append(inputQualityCard("Needs one more detail", data.input_quality));
    target.append(warningSection(data.warnings || data.input_quality?.warnings || []));
    target.append(jsonDetails(data));
    return;
  }
  if (data.input_quality?.status === "rejected") {
    target.append(inputQualityCard("Input not usable yet", data.input_quality));
    target.append(warningSection(data.warnings || data.input_quality?.warnings || []));
    target.append(jsonDetails(data));
    return;
  }
  target.append(answerCard(view.title(data), view.answer(data)));
  target.append(metadataGrid(view.meta(data)));
  target.append(view.evidence ? view.evidence(data) : citationSection(view.citations(data)));
  target.append(warningSection(data.warnings || []));
  target.append(jsonDetails(data));
}

function renderRecipeSession(target, data) {
  target.innerHTML = "";
  target.append(sessionStatusHeader(data));

  if (data.response_state === "clarification_needed") {
    target.append(sessionQuestionCard(data));
  }

  target.append(metadataGrid({
    interaction_id: data.interaction_id || "none",
    response_state: data.response_state || "none",
    revision_count: data.revision_count ?? 0,
    confidence_label: data.requirements?.confidence_label || "none",
    rag_refreshed: data.rag_refreshed ? "true" : "false",
    rag_refresh_reason: data.rag_refresh_reason || "none",
    changed_fields: (data.changed_fields || []).join(", ") || "none",
    revision_summary: data.revision_summary || "none",
    support_level: data.support_level || "none",
    last_citation_ids: (data.citations || []).map((citation) => citation.id).filter(Boolean).join(", ") || "none",
    expires_at: data.expires_at || "none",
  }));

  target.append(sessionRequirementsSection(data.requirements || {}));

  if (data.requirement_diff || data.revision_summary) {
    target.append(answerCard("Latest requirement change", data.revision_summary || data.requirement_diff?.summary_message || "No change summary available."));
  }

  if (data.draft) {
    target.append(answerCard(`Draft: ${data.draft.title || "Recipe draft"}`, importerAnswer(data)));
  } else if (data.response_state === "clarification_needed") {
    target.append(answerCard("Draft", "No draft was generated because one clarification is needed."));
  }

  if (data.retrieval || data.citations?.length) {
    target.append(importerEvidenceSection(data));
  }

  if (data.response_state === "no_material_change") {
    target.append(answerCard("No refresh", "No material recipe requirements changed. Existing draft and citations were reused; no RAG refresh was needed."));
  }

  if (data.response_state === "rag_refreshed" || data.response_state === "draft_revised") {
    target.append(answerCard(
      "RAG refresh status",
      data.rag_refreshed ? (data.rag_refresh_reason || "RAG was refreshed because material recipe requirements changed.") : "Draft revised without a required RAG refresh.",
    ));
  }

  if (data.response_state === "ready_to_finalize") {
    target.append(answerCard("Finalize for demo", "Ready to finalize for demo only. This alpha action does not write to production storage."));
  }

  target.append(warningSection(data.warnings || []));
  target.append(jsonDetails(data));
}

function sessionStatusHeader(data) {
  const wrapper = document.createElement("div");
  wrapper.className = "session-status";
  const state = document.createElement("span");
  state.className = `status-pill ${data.response_state === "rejected" ? "error" : data.response_state === "clarification_needed" ? "warn" : "ok"}`;
  state.textContent = data.response_state || "unknown";
  const id = document.createElement("span");
  id.className = "meta-pill";
  id.textContent = data.interaction_id ? `Session ${data.interaction_id}` : "No active session";
  wrapper.append(state, id);
  return wrapper;
}

function sessionQuestionCard(data) {
  const card = document.createElement("div");
  card.className = "question-card";
  const heading = document.createElement("h3");
  heading.textContent = "Clarification question";
  const body = document.createElement("p");
  body.textContent = data.clarification_question || "One more recipe detail is needed.";
  card.append(heading, body);
  return card;
}

function sessionRequirementsSection(requirements) {
  const section = document.createElement("div");
  section.className = "subsection";
  const heading = document.createElement("h3");
  heading.textContent = "Interpreted requirements";
  section.append(heading, metadataGrid({
    dish_intent: requirementValue(requirements.dish_intent),
    serving_count: requirementValue(requirements.serving_count),
    required_ingredients: requirementList(requirements.required_ingredients),
    excluded_ingredients: requirementList(requirements.excluded_ingredients),
    cooking_method: requirementValue(requirements.cooking_method),
    equipment_constraints: requirementList(requirements.equipment_constraints),
    dietary_constraints: requirementList(requirements.dietary_constraints),
    open_questions: (requirements.open_questions || []).join("; ") || "none",
    resolved_questions: (requirements.resolved_questions || []).map((item) => `${item.question} -> ${item.answer}`).join("; ") || "none",
    assumptions: requirementList(requirements.assumptions),
  }));
  return section;
}

function requirementValue(field) {
  if (!field) {
    return "none";
  }
  return `${field.value} (${field.source || "source unknown"})`;
}

function requirementList(items) {
  if (!items || !items.length) {
    return "none";
  }
  return items.map((item) => requirementValue(item)).join(", ");
}

function inputQualityCard(title, inputQuality) {
  const body = [inputQuality?.clarifying_question, inputQuality?.reason].filter(Boolean).join("\n");
  const card = answerCard(title, body || "Please add one specific cooking detail and try again.");
  card.classList.add(inputQuality?.status === "rejected" ? "error-card" : "warning-card");
  return card;
}

function renderError(target, message) {
  target.innerHTML = "";
  const card = answerCard("Recoverable demo issue", message || "The request could not be completed.");
  card.classList.add("error-card");
  target.append(card);
  target.append(answerCard("Next step", "Check readiness, confirm local demo data is configured, then retry this workflow. Other workflows can continue."));
}

function answerCard(title, body) {
  const card = document.createElement("div");
  card.className = "answer-card";
  const heading = document.createElement("h3");
  heading.textContent = title || "Result";
  const text = document.createElement("p");
  text.textContent = body || "No answer text returned.";
  card.append(heading, text);
  return card;
}

function metadataGrid(values) {
  const grid = document.createElement("div");
  grid.className = "metadata-grid";
  for (const [label, value] of Object.entries(values || {})) {
    const item = document.createElement("div");
    item.className = "metadata-item";
    const labelNode = document.createElement("span");
    labelNode.textContent = label;
    const valueNode = document.createElement("strong");
    valueNode.textContent = value === undefined || value === null ? "none" : String(value);
    item.append(labelNode, valueNode);
    grid.append(item);
  }
  return grid;
}

function citationSection(items) {
  const section = document.createElement("div");
  section.className = "subsection";
  const heading = document.createElement("h3");
  heading.textContent = "Citations and provenance";
  section.append(heading);
  if (!items.length) {
    const empty = document.createElement("p");
    empty.className = "hint";
    empty.textContent = "No citations returned for this response.";
    section.append(empty);
    return section;
  }
  const list = document.createElement("ul");
  list.className = "citation-list";
  for (const item of items) {
    const child = document.createElement("li");
    child.textContent = `${item.title || "Untitled"} - ${item.detail || "source detail unavailable"}${item.snippet ? ` - ${item.snippet}` : ""}`;
    list.append(child);
  }
  section.append(list);
  return section;
}

function importerEvidenceSection(data) {
  const section = document.createElement("div");
  section.className = "subsection";
  const heading = document.createElement("h3");
  heading.textContent = "Citations and provenance";
  section.append(heading);

  const citations = Array.isArray(data?.citations) ? data.citations : [];
  const retrieval = data?.retrieval || {};
  const supportLevel = retrieval.support_level || "none";
  const supportMessage = retrieval.support_message || supportMessageForLevel(supportLevel);
  const cache = retrieval.cache || retrieval.index?.cache || {};
  const summary = document.createElement("p");
  summary.className = "hint";
  summary.textContent = `${citations.length} citation(s) returned${retrieval.retrieved_count !== undefined ? ` from ${retrieval.retrieved_count} retrieved example(s)` : ""}${retrieval.packed_count !== undefined ? `; ${retrieval.packed_count} packed for prompt context` : ""}.`;
  section.append(summary);

  const supportCard = document.createElement("p");
  supportCard.className = "hint";
  supportCard.textContent = `RAG support: ${capitalize(supportLevel)}. ${supportMessage}`;
  section.append(supportCard);

  if (!citations.length) {
    const empty = document.createElement("p");
    empty.className = "hint";
    empty.textContent = supportLevel === "none"
      ? "No useful dataset examples were available for this response."
      : "No importer citations were returned for this response.";
    section.append(empty);
  } else {
    const list = document.createElement("ul");
    list.className = "citation-list";
    const citationLabel = supportLevel === "strong" ? "Citation" : supportLevel === "moderate" ? "Partial example" : "Broad example";
    for (const citation of citations) {
      const child = document.createElement("li");
      const provenance = citation.provenance || {};
      const provenanceLabel = [provenance.dataset, provenance.license].filter(Boolean).join(" / ") || "provenance unavailable";
      const matched = (citation.matched_fields || []).length ? `Matched: ${citation.matched_fields.join(", ")}` : "Matched: none";
      child.textContent = [
        `${citationLabel}: ${citation.title || "Untitled"}`,
        `Source ID: ${citation.source_id || "unknown"}`,
        `Provenance: ${provenanceLabel}`,
        matched,
        citation.snippet ? `Snippet: ${citation.snippet}` : "Snippet unavailable",
      ].join(" - ");
      list.append(child);
    }
    section.append(list);
  }

  if (retrieval && Object.keys(retrieval).length) {
    const retrievalHeading = document.createElement("h4");
    retrievalHeading.textContent = "Retrieval metadata";
    section.append(retrievalHeading, metadataGrid({
      query: retrieval.query || "none",
      anchors: (retrieval.anchors_used || []).join(", ") || "none",
      retrieved_examples: retrieval.retrieved_count ?? 0,
      packed_examples: retrieval.packed_count ?? 0,
      packed_ids: (retrieval.packed_ids || []).join(", ") || "none",
      dropped_ids: (retrieval.dropped_ids || []).join(", ") || "none",
      context_chars_used: retrieval.packed_context_chars ?? 0,
      max_context_chars: retrieval.max_context_chars ?? "none",
      weak_examples_included: retrieval.weak_examples_included ? "yes" : "no",
      context_budget_warning: retrieval.context_budget_warning || "none",
      limit: retrieval.limit ?? "none",
      dataset_limit: retrieval.dataset_limit ?? "none",
      matched_ids: (retrieval.matched_result_ids || []).join(", ") || "none",
      scores: (retrieval.matched_result_scores || []).join(", ") || "none",
      relevance: retrieval.relevance_category || "none",
      support_level: retrieval.support_level || "none",
      support_reason: retrieval.support_reason || "none",
      citation_support_count: retrieval.citation_support_count ?? 0,
      weak_citation_count: retrieval.weak_citation_count ?? 0,
      strong_citation_count: retrieval.strong_citation_count ?? 0,
      support_message: retrieval.support_message || "none",
      should_claim_rag_grounded: retrieval.should_claim_rag_grounded ? "yes" : "no",
      should_show_weak_support_warning: retrieval.should_show_weak_support_warning ? "yes" : "no",
      cache: cacheSummary(cache),
      warning: retrieval.warning || "none",
      documents: retrieval.index?.document_count ?? "none",
    }));
  }

  return section;
}

function warningSection(warnings) {
  const section = document.createElement("div");
  section.className = "subsection";
  if (!warnings.length) {
    return section;
  }
  const card = document.createElement("div");
  card.className = "warning-card";
  card.textContent = warnings.join(" ");
  section.append(card);
  return section;
}

function jsonDetails(data) {
  const details = document.createElement("details");
  const summary = document.createElement("summary");
  summary.textContent = "Show raw JSON";
  const code = document.createElement("pre");
  code.textContent = safeJson(data);
  details.append(summary, code);
  return details;
}

function readinessCard(title, ok, value, message) {
  const card = document.createElement("div");
  card.className = "readiness-card";
  const heading = document.createElement("h3");
  heading.textContent = title;
  const pill = document.createElement("span");
  pill.className = `status-pill ${ok ? "ok" : "warn"}`;
  pill.textContent = value || (ok ? "Ready" : "Needs data");
  const body = document.createElement("p");
  body.textContent = message || "";
  card.append(heading, pill, body);
  return card;
}

function readinessSkeleton() {
  return '<div class="readiness-card"><h3>Checking readiness</h3><span class="status-pill warn">Loading</span><p>Contacting the sidecar.</p></div>';
}

function usageReportSkeleton() {
  return '<div class="readiness-card"><h3>Checking usage report</h3><span class="status-pill warn">Loading</span><p>Contacting the local operator report endpoint.</p></div>';
}

function resetWorkflow(workflow) {
  const input = document.getElementById(workflow.input);
  input.value = workflow.sample;
  if (workflow.followup) {
    document.getElementById(workflow.followup).value = workflow.followupSample || "";
  }
  if (workflow.card === "recipe-session") {
    activeRecipeSessionId = null;
  }
  const target = document.getElementById(workflow.result);
  target.className = "result empty";
  target.textContent = "Reset complete. Run this workflow when ready.";
}

function setLoading(workflow, loading) {
  const card = document.querySelector(`[data-workflow-card="${workflow.card}"]`);
  for (const button of card.querySelectorAll("button")) {
    button.disabled = loading;
  }
}

function providerMetadata(data) {
  return {
    provider: data.provider || "none",
    model: data.model || "none",
    warnings: (data.warnings || []).length,
  };
}

function supportMessageForLevel(level) {
  if (level === "strong") {
    return "Dataset examples closely matched this dish and informed the draft.";
  }
  if (level === "moderate") {
    return "Dataset examples were related, but the draft is still driven by your notes.";
  }
  if (level === "weak") {
    return "Examples were broad matches, so the draft relies mainly on your notes and disclosed estimates.";
  }
  return "No useful dataset examples were available; the draft was generated from your notes and defaults.";
}

function cacheMetadata(cache) {
  if (!cache) {
    return {};
  }
  return {
    cache: cacheSummary(cache),
  };
}

function formatUsd(value) {
  if (value === null || value === undefined) {
    return "$0.00";
  }
  const numeric = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(numeric)) {
    return "$0.00";
  }
  return `$${numeric.toFixed(2)}`;
}

function cacheSummary(cache) {
  if (!cache) {
    return "none";
  }
  const parts = [];
  if (cache.index_cache_hit !== undefined && cache.index_cache_hit !== null) {
    parts.push(`index ${cache.index_cache_hit ? "hit" : "miss"}`);
  }
  if (cache.retrieval_cache_hit !== undefined && cache.retrieval_cache_hit !== null) {
    parts.push(`retrieval ${cache.retrieval_cache_hit ? "hit" : "miss"}`);
  }
  if (cache.cache_entry_count !== undefined) {
    const maxEntries = cache.cache_max_entries !== undefined && cache.cache_max_entries !== null ? cache.cache_max_entries : "none";
    parts.push(`entries ${cache.cache_entry_count}/${maxEntries}`);
  }
  if (cache.cache_ttl_seconds !== undefined && cache.cache_ttl_seconds !== null) {
    parts.push(`ttl ${cache.cache_ttl_seconds}s`);
  }
  return parts.length ? parts.join("; ") : "none";
}

function capitalize(value) {
  const text = String(value || "none");
  return text ? text.charAt(0).toUpperCase() + text.slice(1) : "None";
}

function importerAnswer(data) {
  const draft = data.draft || {};
  const ingredients = (draft.ingredients || []).map((item) => {
    const amount = [item.quantity, item.unit].filter(Boolean).join(" ");
    return `${amount ? `${amount} ` : ""}${item.name}${item.note ? ` (${item.note})` : ""}`;
  });
  const instructions = (draft.instructions || []).map((step) => `${step.step}. ${step.text}`);
  return [
    `Servings: ${draft.servings ?? "not specified"}`,
    "",
    "Ingredients:",
    ingredients.length ? ingredients.join("\n") : "None",
    "",
    "Instructions:",
    instructions.length ? instructions.join("\n") : "None",
    draft.notes ? `\nNotes: ${draft.notes}` : "",
  ].filter((line) => line !== "").join("\n");
}

function friendlyError(status, detail) {
  const safeDetail = String(detail || "Request failed.").replace(/\s+/g, " ").slice(0, 220);
  if (status === 422) {
    return `${safeDetail} Configure local saved recipe or dataset fixtures, then retry.`;
  }
  if (status === 404) {
    return "Recipe session was not found or has expired. Start a new local alpha session and retry.";
  }
  if (status >= 500) {
    return "The sidecar could not complete this workflow. Check service logs and retry after confirming provider and data readiness.";
  }
  return `${safeDetail} (HTTP ${status})`;
}

function sanitizeData(data) {
  const text = safeJson(data);
  return parseJson(text) || data;
}

function safeJson(data) {
  const text = JSON.stringify(data, null, 2);
  for (const marker of forbiddenText) {
    if (text.includes(marker)) {
      return "{\"message\":\"Response hidden because it contained a forbidden sensitive marker.\"}";
    }
  }
  return text;
}

function parseJson(text) {
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}
