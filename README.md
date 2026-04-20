# Formloop

Formloop is the agent harness that turns natural-language design intent into
managed CAD work. It orchestrates a manager agent and a small set of
specialists (CAD Designer, Design Researcher, Quality Specialist) around the
deterministic `cad-cli` toolchain, producing inspectable STEP / GLB / render
artifacts plus structured review output.

See `REQUIREMENTS_HARNESS.md` for the authoritative requirements, `SPEC.md`
for architecture context, and `AGENTS.md` for coding-agent working rules.

## Live narration

The harness emits a two-channel progress stream: machine-readable milestone
events (`spec_normalized`, `revision_built`, `review_completed`, …) and short
LLM-written narrations from a dedicated lightweight Narrator agent that say
what just finished, what's starting next, and why. `formloop run` prints the
latest narration inline above the next final block — `--quiet` suppresses it,
`--verbose` dumps the full structured payload, and `--no-color` forces the
plain renderer. Polling clients see the same narrations on the event stream
plus a convenience `latest_narration` field on the run snapshot, so a UI can
mirror the in-place reasoning-trace pattern without scanning the event tail.

## Quick start

```bash
# inside the formloop/ directory
uv sync --extra dev
cp .env.example .env.local     # add OPENAI_API_KEY

uv run formloop doctor
uv run formloop run "a 20mm cube" --profile dev_test
```

Run artifacts land under `var/runs/run-NNNN/`.
