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

## Build123D part-library support in CAD generation

The CAD Designer instructions and research workflow are wired to prefer
Build123D-native approaches plus these installed helper libraries when
appropriate:

- `bd_warehouse`
- `py_gearworks`

`bd_beams_and_bars` is not bundled in the default Python 3.12 environment
because its upstream package currently requires Python 3.13.

During planning/research, manager-generated research topics may include both
engineering/standards questions and Build123D implementation-method questions
(for example: "how to model this feature in Build123D using the installed
libraries").
