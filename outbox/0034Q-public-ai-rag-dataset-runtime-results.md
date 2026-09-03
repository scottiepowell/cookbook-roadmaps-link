# 0034Q Public AI RAG Dataset Runtime Results

Status: complete and deployed.

The host dataset contains the expected local recipe assets, but the deployed
sidecar had no dataset mount. Its relative configured path therefore resolved
to a missing directory inside the container, producing the visible fallback
warning and skipping importer RAG examples.

The first 5,000-record index build takes approximately one minute on the
current host, so the public sidecar now warms it before reporting healthy.
Warmup remains disabled by default outside the public Compose profile.

## Result

- the dataset is mounted only in the sidecar and Docker reports the mount as
  read-only;
- the configured directory and expected CSV are present inside the container;
- the index limit is 5,000 records;
- startup warmup completed before the sidecar reported healthy;
- safe mock retrieval found 3 examples, packed 2 into bounded context, returned
  3 citations, classified relevance and support as strong, and marked the
  result RAG-grounded;
- the visible missing-directory warning is absent;
- the first post-ready mock importer check completed within the core timeout;
- the first bounded live call returned incomplete structured output and was
  safely classified as retryable;
- the one permitted retry succeeded with `gpt-5.4-nano`, 3 retrieved examples,
  2 packed examples, 3 citations, strong relevance/support, and RAG grounding;
- public health remained 200 and the sidecar still has no host-published port.
- full repository validation passed with 415 tests, 39 offline evals, and all
  7 repository checks including secret scanning.

No raw dataset row, dataset file, generated recipe, provider prompt/response,
API key, operator token, cookie, OAuth value, or user profile is recorded.
