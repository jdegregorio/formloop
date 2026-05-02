# Formloop

Formloop is the agent harness that turns natural-language design intent into
managed CAD work. It orchestrates a manager agent and a small set of
specialists (CAD Designer, Reviewer, Judge, Narrator), plus direct
search-enabled research calls, around the deterministic `cad-cli` toolchain,
producing inspectable STEP / GLB / render artifacts plus structured review
output.

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
# inside the formloop/ directory — single step installs everything
uv sync --extra dev
cp .env.example .env.local     # add OPENAI_API_KEY

uv run formloop doctor
uv run formloop run "a 20mm cube" --profile dev_test
```

`uv sync` installs `cad-cli`, `build123d`, and all CAD helper libraries into
one shared virtualenv. No separate `uv tool install` step is needed — `cad
build` invokes models with `--python <venv>/bin/python3` so that `bd_warehouse`
and `py_gearworks` are always visible.

Run artifacts land under `var/runs/run-NNNN/`.

## Browser UI

The v1 web UI lives in `web/` and is built as a React/Vite TypeScript app.
During development, run it beside the polling API:

```bash
uv run uvicorn formloop.api.app:app --host 127.0.0.1 --port 8765
npm --prefix web install
npm --prefix web run dev
```

For the same-origin operator surface, build the UI and start the Formloop API:

```bash
npm --prefix web run build
uv run formloop ui start
```

`formloop ui start` serves the API and the built `web/dist` assets from the
same host/port. The UI stores one browser-local design thread, polls run
snapshots/events, renders the latest narration inline, keeps trace details
collapsed by default, and uses the latest GLB as the primary geometry surface.

## Build123D part-library support in CAD generation

The CAD Designer agent carries a comprehensive cheat sheet covering
Build123D core primitives, operations, and these installed extension libraries:

- `bd_warehouse` — parametric fasteners, bearings, threads, flanges, pipes, sprockets, gears
- `py_gearworks` — accurate involute/cycloid/bevel gear generation

The cheat sheet includes required-vs-optional argument signatures for every
advertised constructor, so the designer can author correct imports and
constructors without external lookups.

During planning/research, manager-generated research topics may include both
engineering/standards questions and Build123D implementation-method questions
(for example: "how to model this feature in Build123D using the installed
libraries").
