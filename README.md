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

### System prerequisites

- Python 3.12+
- [`uv`](https://docs.astral.sh/uv/) for dependency management
- **Blender** — required for `cad render` and `cad compare --render-diffs`. Install it once for your platform:

  ```bash
  brew install --cask blender             # macOS
  # Linux: install via your package manager or download from https://www.blender.org/
  # Windows: install from https://www.blender.org/ and ensure `blender` is on PATH
  ```

### Install

```bash
# inside the formloop/ directory
uv sync --extra dev
cp .env.example .env.local     # add OPENAI_API_KEY

uv run formloop doctor
uv run formloop run "a 20mm cube" --profile dev_test
```

`uv sync` installs `cad-cli` (pinned to a tagged release in `pyproject.toml`)
and the build123d ecosystem libraries directly into formloop's `.venv`.
There is no separate `uv tool install cad-cli` step — formloop and cad-cli
share one Python environment so the model evaluated by `cad build --python`
sees the same packages the rest of the harness uses. Run artifacts land under
`var/runs/run-NNNN/`.

### Hacking on cad-cli alongside formloop

When iterating on cad-cli locally, override the pinned source with a personal
`.uv.toml` (uncommitted) at the repo root:

```toml
[sources]
cad-cli = { path = "../cad-cli", editable = true }
```

…or run `uv pip install -e ../cad-cli` after `uv sync`. `pyproject.toml` keeps
the git tag pin so fresh clones do not need a sibling cad-cli checkout.

## Build123D part-library support in CAD generation

The CAD Designer instructions and research workflow are wired to prefer
Build123D-native approaches plus these installed helper libraries when
appropriate:

- `bd_warehouse`
- `py_gearworks`

These libraries live in formloop's own venv and are visible to `cad build`
because every build is invoked with `--python <formloop-venv-python>` (cad-cli
v0.1.2+). Adding or removing a designer-advertised library is therefore a
formloop-side dependency change; `formloop doctor` verifies each advertised
library is importable in the venv that `cad build` will use.

`bd_beams_and_bars` is not bundled in the default Python 3.12 environment
because its upstream package currently requires Python 3.13.

During planning/research, manager-generated research topics may include both
engineering/standards questions and Build123D implementation-method questions
(for example: "how to model this feature in Build123D using the installed
libraries").
