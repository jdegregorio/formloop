# Formloop

Formloop is an agentic CAD application that turns natural-language design intent into managed CAD work. It owns the agent harness, run state, review and revision loop, artifact plumbing, operator tooling, and developer evals, while delegating deterministic geometry work to `cad-cli`.

Today, the implemented part of the project is the harness layer: the multi-agent orchestration, CLI, API, run store, eval framework, and UAT tooling. The end-user web UI is not built yet.

## Status

| Area | Status | Notes |
| --- | --- | --- |
| Harness and runtime | Implemented | Manager and specialist orchestration, run persistence, artifact handling, review loop, config profiles, and diagnostics are in place. |
| Operator CLI | Implemented | `run`, `doctor`, `ui`, `eval`, `uat`, and `update` commands are available. |
| Harness API | Implemented | FastAPI server for submitting runs and retrieving run state and artifacts. |
| Eval framework | Implemented | Dataset-backed eval runs, aggregate reporting, and smoke/UAT support are available. |
| Web UI | Not implemented yet | Placeholder section below. |
| Real `cad-cli` and Blender pipeline | Partial | The harness integrates against the `cad` contract today and uses a deterministic fake CAD fixture for local closed-loop testing. |
| Open Agent Skills standard parity | Partial | Built-in skills exist, but full standard compliance is still tracked as future work. |

## What Formloop Is

Formloop is the product-facing application layer for an agentic CAD system. It is responsible for:

- accepting design requests and revisions
- maintaining a normalized fit, form, and function spec
- routing work across a small manager-plus-specialists harness
- running an internal design review loop
- invoking deterministic CAD tooling
- storing artifacts, traces, and revision history
- running repeatable developer evals and UAT flows

Formloop is intentionally separate from `cad-cli`.

- Formloop decides what work should happen and how to validate it.
- `cad-cli` performs deterministic CAD work and returns artifacts plus structured results.

## What Is Available Today

The currently implemented v1 surface is the harness and developer tooling:

- Profile-based execution built on the OpenAI Agents SDK
- OpenAI-first runtime with Anthropic support through the LiteLLM provider path
- A stable operator CLI
- A FastAPI harness API
- Run persistence with artifacts, events, review summaries, and runtime metadata
- Dataset-backed eval execution and reporting
- Self-run UAT coverage for critical user and operator flows
- A deterministic fake CAD fixture for local testing without a full CAD stack

## Architecture At A Glance

The current harness uses a small, controlled agent set:

- Manager
- CAD Designer
- Design Researcher
- Render Specialist
- Review Specialist
- Eval Specialist

Key design rules:

- The manager owns the active spec and routing, not heavy CAD authoring.
- The manager attempts a first pass by default and only blocks for clarification when critical gaps make a credible first model impossible.
- The CAD Designer behaves like a mechanical design engineer and may pull in the Design Researcher when standards, named parts, or engineering conventions matter.
- The Review Specialist runs the internal closed loop for normal design runs.
- The Eval Specialist is separate and only for dataset-backed benchmarking and CI-style evaluation.

## Installation

### Prerequisites

- Python 3.12+
- A local checkout of this repo
- For live model execution: OpenAI and/or Anthropic API keys
- For deterministic local testing: no live model keys are required if you use the heuristic backend and fake CAD fixture

### Environment setup

Create a local secrets file at the repo root:

```bash
cp .env.example .env.local
```

Then set at minimum:

```env
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
```

`formloop.harness.toml` contains the checked-in non-secret runtime defaults and named profiles.

### Install the project

With `uv`:

```bash
uv sync --extra dev
source .venv/bin/activate
```

Or with standard `venv` + `pip`:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Quick Start

### 1. Validate the environment

For a deterministic local check that does not require live model calls:

```bash
FORMLOOP_LLM_BACKEND=heuristic python -m formloop doctor \
  --cad-command /Users/jdegregorio/Repos/formloop/scripts/fake_cad
```

For a normal configured run against the checked-in default profile:

```bash
python -m formloop doctor
```

### 2. Run the harness locally

Deterministic smoke path:

```bash
FORMLOOP_LLM_BACKEND=heuristic python -m formloop run \
  --cad-command /Users/jdegregorio/Repos/formloop/scripts/fake_cad \
  "Create a 20 mm cube with a centered 5 mm through hole"
```

Live model path:

```bash
python -m formloop run "Create a small mounting bracket with two M3 clearance holes"
```

Useful options:

- `--profile normal`
- `--profile dev_test`
- `--profile anthropic_normal`
- `--reference-image /absolute/path/to/reference.png`
- `--json`

### 3. Start the harness API

```bash
python -m formloop ui start
python -m formloop ui status
```

This starts the harness API server, not the future end-user web UI. By default it listens on `http://127.0.0.1:8040`.

Useful API endpoints:

- `GET /healthz`
- `POST /runs`
- `GET /runs/{run_id}`
- `GET /runs/{run_id}/events`
- `GET /runs/{run_id}/events/stream`
- `GET /artifacts/{run_id}/{artifact_path}`

### 4. Run evals

Example dataset eval:

```bash
FORMLOOP_LLM_BACKEND=heuristic python -m formloop eval run \
  --cad-command /Users/jdegregorio/Repos/formloop/scripts/fake_cad \
  basic_shapes
```

View the latest report:

```bash
python -m formloop eval report basic_shapes
```

### 5. Run UAT

```bash
python -m formloop uat run \
  --cad-command /Users/jdegregorio/Repos/formloop/scripts/fake_cad
```

The built-in UAT flow exercises the important harness paths defined in `REQUIREMENTS_HARNESS.md`, including clarification behavior, assumptions, research traces, review-driven revision, profile-aware execution, eval execution, and traceability.

## CLI Reference

The top-level operator interface is:

```bash
python -m formloop --help
```

Available commands:

- `python -m formloop run "..."` runs a single design request outside the UI.
- `python -m formloop doctor` validates profiles, keys, config, and CAD command setup.
- `python -m formloop ui start|status|stop` manages the harness API server.
- `python -m formloop eval run <dataset>` runs a dataset-backed eval batch.
- `python -m formloop eval report <dataset>` prints the latest eval report.
- `python -m formloop uat run` executes the harness UAT suite.
- `python -m formloop update` is reserved for future repo update automation.

## Profiles And Runtime Configuration

The runtime is intentionally profile-based instead of exposing a large matrix of per-agent model controls.

Current checked-in profiles live in `formloop.harness.toml`:

- `normal`: OpenAI Responses, `gpt-5.4`, `high`
- `dev_test`: OpenAI Responses, `gpt-5.4-nano`, `low`
- `eval`: OpenAI Responses, `gpt-5.4`, `high`
- `anthropic_normal`: LiteLLM provider path, Anthropic Sonnet model, `high`

The primary knobs intended for operators are:

- profile
- provider/model selection through that profile
- a normalized thinking level
- backend and CAD command overrides when needed

## Repository Guide

Important paths:

- `src/formloop/`: harness implementation
- `src/formloop/api/`: FastAPI surface for the harness
- `datasets/`: developer eval datasets
- `scripts/fake_cad`: deterministic fake CAD command used for smoke tests, evals, and UAT
- `formloop.harness.toml`: checked-in runtime defaults and profiles
- `SPEC.md`: system-level architecture and product boundaries
- `REQUIREMENTS_HARNESS.md`: canonical harness checklist and UAT requirements
- `REQUIREMENTS_UI.md`: planned UI requirements

## Validation Culture

Formloop is built around closed-loop validation. A passing unit test is not enough by itself.

The intended evidence chain is:

- request or prompt
- normalized spec
- generated artifacts
- review findings
- revision decisions
- persisted run state
- eval or UAT outputs when relevant

For the current harness, that means:

- unit and integration tests
- smoke-friendly deterministic runs using the fake CAD fixture
- dataset eval runs with reports
- a self-run UAT suite over critical user and operator flows

## Current Limitations

- The user-facing web UI is not implemented yet.
- The harness API exists, but the browser app described in `REQUIREMENTS_UI.md` is still future work.
- The repo currently uses a fake CAD fixture for most closed-loop local validation; a real `cad-cli` plus Blender-backed artifact pipeline still needs to be wired in fully.
- `python -m formloop update` is a placeholder.
- Full open Agent Skills standard compliance is still incomplete.

## Planned Sections

### Web UI

Planned. This will become the primary design-review workspace and will integrate against the existing harness API.

### Production CAD Integration

Planned. This will replace the fake local CAD fixture with the real `cad-cli` execution path, authoritative STEP handling, GLB generation, rendering, and richer deterministic inspection.

### Deployment And Operations

Planned. This section will eventually cover packaged installation, hosted execution, production secrets management, and operational guidance.

## Where To Find More Information

- See `SPEC.md` for the system architecture and ownership boundaries.
- See `REQUIREMENTS_HARNESS.md` for the harness contract, validation expectations, and UAT matrix.
- See `REQUIREMENTS_UI.md` for the planned user-facing web application.
- See `formloop.harness.toml` for the currently supported runtime profiles and defaults.

## Getting Help

If you are working in this repo and something is unclear, start with the spec and requirements files before changing behavior. They are the source of truth for what the harness is supposed to do and how completion should be judged.
