# Assignment 1

This repository is scaffolded for the SEZG534 assignment and is intended to be completed in five phases using Spec-Driven Development and independent validation harnesses.

## Repository structure

- `Assignment-1/`
  - `Part-1A/`: deterministic Python task application, harness, and evidence
  - `Part-1B/`: non-deterministic AI reminder agent, evaluation harness, and evidence
  - `.gitignore`: ignores local secrets, virtual environments, Python caches, and generated artifacts
  - `.env.example`: template for required environment variables

## Local setup

1. Ensure Python 3.11+ is installed.
2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```
3. Install the toolchain that will be added during the assignment phases:
   ```bash
   pip install python-dotenv pytest ruff bandit
   ```
4. Copy the example environment file and populate values as needed:
   ```bash
   cp .env.example .env
   ```

## Execution overview

### Part 1A
- Specification artifacts live in `Part-1A/.specify/`.
- Deterministic source code is implemented in `Part-1A/src/`.
- Contract tests are stored in `Part-1A/tests/`.
- Independent validation is executed via:
  ```bash
  python Part-1A/.harness/run_harness.py
  ```

### Part 1B
- AI-spec artifacts live in `Part-1B/.specify/`.
- Prompt templates and source files are in `Part-1B/prompts/` and `Part-1B/src/`.
- Evaluation cases are in `Part-1B/evals/dataset.json`.
- The evaluation pipeline is executed via:
  ```bash
  python Part-1B/.harness/run_eval_harness.py
  ```

## Phase workflow

1. Scaffold this repository (completed in Phase 1).
2. Generate Spec Kit artifacts before implementation in each part.
3. Implement the application logic and tests.
4. Run the independent harness to collect evidence.
5. Repair genuine failures without weakening constraints or lowering thresholds.
6. Record the final human review in harness logs and reflections.

## Notes

- Never commit real secrets to version control.
- Keep all generated evidence under `evidence/` folders for traceability.
- Treat the harness output as the authoritative validation signal for repair cycles.
