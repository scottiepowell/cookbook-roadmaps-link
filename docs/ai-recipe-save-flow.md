# AI Recipe Save Flow

The authenticated AI recipe conversation remains a draft workspace until the
user selects **Save to Cookbook**. A complete draft is converted to the core's
existing recipe-create payload and submitted to the authenticated `/api/recipe`
route. The core assigns the current user, writes the canonical recipe, and
returns its opaque identifier; the browser then opens the normal recipe view.

The save maps title, description, serving count, ingredient quantities, units,
names and notes, instructions, and an optional source URL or note. It also uses
the user's existing default for public recipes. The normal recipe editor remains
the place for subsequent corrections and optional media.

## Failure and ownership behavior

- An incomplete draft cannot be saved.
- The control is locked while a request is active to avoid duplicate clicks.
- A failed save leaves the draft, conversation, and change count visible so the
  user can retry.
- A successful save clears the transient AI chat and redirects to the canonical
  recipe page.
- The core owns authentication, recipe ownership, validation, and persistence.
- The private AI sidecar never writes the Cookbook database and never receives a
  browser session or user identity.
- No automatic saving or background canonical writes are introduced.
