# Editable AI Draft Review

Task 0035K adds a core-owned final review editor to the public AI recipe flow.
After AI generation or follow-up revisions, the user can select **Edit draft**
and directly change the title, description, serving count, ingredient quantity,
unit, name and note, or instruction text. Ingredient and instruction rows can
also be added or removed.

These edits are browser-local draft changes. They do not call the AI provider,
consume a recipe-session change, update grounding, or write a canonical recipe.
The existing authenticated **Save to Cookbook** action remains the only write.

Before Save, core validates a non-empty title, a whole-number serving count from
1 through 24, at least one named ingredient, and at least one non-empty
instruction. Invalid drafts remain visible and cannot be saved.

The sidecar retains no browser session, user identity, cookie, OAuth artifact,
or canonical recipe authority.
