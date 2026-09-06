# AI-First Recipe Entry

Task 0035E makes Add Recipe a single AI-first entry point inside Vanilla
Cookbook. The existing `/ai` core route remains responsible for the bounded
recipe conversation and reviewable draft. Navigation and the empty-cookbook
call to action now open that route.

The AI page exposes a clear **Manual entry** alternative. It opens the existing
core `/recipe/new` form, preserving URL, text, and image import plus direct
editing of recipe name, description, ingredients, directions, source URL,
times, servings, notes, and other canonical fields. Bookmarklet requests still
open `/recipe/new` directly so capture behavior does not change.

The opt-in core sample seed contains five recipes. Two original Cookbook sample
recipes supplement the existing three import fixtures. Seed identity is scoped
to user, recipe name, and source, so rerunning the showcase seed adds missing
samples without duplicating those already present.

Recipe and account ownership remains in core. The sidecar does not save
canonical recipes, and the AI workflow still saves nothing automatically.
