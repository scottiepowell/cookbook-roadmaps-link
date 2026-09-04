# 0034W Initial Recipe Ingredient Fidelity Results

Status: complete and deployed.

## Diagnosis and repair

The recipe-session start route parsed the complete request, then rebuilt a
short generation string from only recognized requirement fields. Once enough
recognized fields existed, it omitted the original text entirely. Ingredients
outside the small deterministic vocabulary therefore never reached the model.

The start route now sends the complete bounded initial request through the same
importer and RAG path. The obsolete lossy reconstruction helper was removed.
Cauliflower, generic cheese, and mushroom terms were added to deterministic
requirements so they also participate in retrieval and later requirement diffs.

## Validation

- Repository validation passed all 7 checks.
- 425 tests passed, including full-input forwarding and deterministic ingredient
  extraction coverage.
- 39 offline evaluations passed.
- `git diff --check` and public Compose validation passed.
- `local/cookbook-ai-sidecar:0034w` built and deployed; the existing
  `local/vanilla-cookbook-adapter:0034v` core remained running.
- Sidecar health and public health both passed; the independent tunnel was not
  recreated and no sidecar host port was published.
- Safe funded live nano check using the reported ingredient pattern: initial
  generation succeeded at revision zero; chicken, cauliflower, and cheese were
  each present; the model pin was correct. Only booleans and the revision count
  were recorded, not the generated draft or provider output.
