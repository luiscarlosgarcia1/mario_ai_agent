# Docs Layout

This directory uses a sibling planning structure so a fresh chat can find the right PRD context with minimal token overhead.

## Convention

- Keep each PRD at `docs/<name>_prd.md`.
- Keep the PRD's plan and closely-related issue slices under `docs/plans/<name>_prd/`.
- Prefer `docs/plans/<name>_prd/plan.md` as the canonical implementation artifact for that PRD.
- Keep only clearly-mapped issue docs beside a PRD; leave ambiguous or legacy issue docs in `docs/issues/` until they are explicitly rehomed.

## Current organized PRDs

- `observer_json_first_schema_prd.md` -> `docs/plans/observer_json_first_schema_prd/`
