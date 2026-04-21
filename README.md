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

## Build123D knowledge pack

The CAD Designer is grounded in a curated Build123D knowledge pack shipped
inside the package at `src/formloop/agents/knowledge/build123d/`. The pack
contains 12 scraped pages from the official Build123D docs (key concepts,
objects, operations, topology selection, builders, joints, assemblies,
import/export, cheat sheet) plus a hand-audited overlay that points at the
external ecosystem libraries `bd_warehouse` (threads, fasteners, bearings,
pipes), `bd_vslot` (aluminum extrusions), `py_gearworks` (gear generators),
and `bd_beams_and_bars` (structural shapes). The designer reaches into the
pack through a `build123d_lookup` function tool for on-demand topic excerpts
— the full corpus is not baked into every prompt.

### Updating the knowledge pack

The scraper lives at `scripts/scrape_build123d_docs.py`. Its optional deps
(`beautifulsoup4`, `markdownify`) are isolated to the `scrape` extra so the
runtime install stays small:

```bash
uv sync --extra scrape
uv run python scripts/scrape_build123d_docs.py
```

The scraper rewrites the 12 pages under
`src/formloop/agents/knowledge/build123d/pages/`, regenerates `index.json`,
refreshes `last-scraped.json` with the current UTC timestamp, and weaves the
external-library annotations from `external_libs_overlay.md` into the
`objects.md` catalog. Review the diff before committing.

## Quick start

```bash
# inside the formloop/ directory
uv sync --extra dev
cp .env.example .env.local     # add OPENAI_API_KEY

uv run formloop doctor
uv run formloop run "a 20mm cube" --profile dev_test
```

Run artifacts land under `var/runs/run-NNNN/`.
