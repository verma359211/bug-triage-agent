# Bug Triage Agent

A CLI walking skeleton that accepts a GitHub repository and a bug report, investigates the code, identifies a likely file and root cause, and verifies backend bugs with a generated Jest test in GitHub Actions.

Generated code is never executed on the local machine. Frontend reports stop after a source-backed hypothesis in V0.

## Architecture

```text
CLI
 |
 v
LangGraph workflow
 |
 +-- clone/update repository under .workdir/
 +-- parse report -> inspect code/history -> form hypothesis -> assess confidence
 |
 +-- frontend ----------------------------------------------> report
 |
 +-- backend -> write Jest repro -> GitHub Actions sandbox -> interpret -> report
                                      |
                                      +-- bounded retry/reinvestigation paths
```

Repository investigation uses small read-only tools for search, file reads, Git log, and Git blame. The sandbox creates a temporary branch in the target repository, commits only the generated test, dispatches the target's reproduction workflow, downloads its result, classifies it, and cleans up temporary GitHub resources.

## Requirements

- Python 3.11 or newer
- Git
- A Groq API key
- A GitHub token with Actions read/write and Contents read/write access to the target repository
- A target repository containing the reproduction workflow used by this project

## Setup

```bash
python -m venv .venv
```

Activate the environment on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Or on macOS/Linux:

```bash
source .venv/bin/activate
```

Then install dependencies and create the local configuration:

```bash
python -m pip install -r requirements.txt
cp .env.example .env
```

Fill in `GITHUB_TOKEN` and `GROQ_API_KEY` in `.env`. `TARGET_REPO` is used by the evaluation scripts; `LLM_MODEL` selects the Groq model. The `.env` file, cloned repositories, and run reports are ignored by Git.

## Run the web app

The web interface presents the project as a small product named **Trace**. It includes an explainer, bug-submission workspace, real stage-by-stage logs, and a structured result view.

Install and build the frontend once:

```bash
cd frontend
npm install
npm run build
cd ..
```

Start the combined API and production frontend:

```bash
python -m uvicorn agent.web:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000`. The server runs each investigation in an isolated Python subprocess, retains at most 200 log messages per run, limits concurrent work, and removes completed in-memory run records after one hour.

For frontend development, start the API as above and run `npm run dev` inside `frontend/`. Vite proxies `/api` requests to the local API.

## Run the CLI

```bash
python -m agent.cli \
  --repo https://github.com/OWNER/REPOSITORY.git \
  --report "Describe the observed behavior and the expected behavior"
```

The CLI prints Markdown and JSON reports and saves a JSON copy under `runs/`. Reports include the status, likely file, cause, evidence, confidence, reproduction test, attempt count, and elapsed time.

## Safety and limits

- Repository clones stay under `.workdir/`.
- Generated tests run only in GitHub Actions.
- Investigation is limited to three rounds with at most six tool calls per round.
- Invalid reproduction tests can be rewritten up to three total attempts.
- A non-reproducing test can return to investigation at most twice.
- Infrastructure failures retry once.
- Frontend reproduction is intentionally out of scope for V0.

## Verification

Run the local unit tests:

```bash
python -m unittest discover -s tests -v
```

Check the GitHub Actions sandbox with three known classifications, repeated three times each:

```bash
python eval/run_sandbox_check.py
```

Run all four end-to-end cases:

```bash
python eval/run_eval.py
```

Cause matching requires at least 75% of a case's expected keywords in the combined cause and reasoning. The final V0 evaluation produced:

| Case | File match | Cause match | Status | Seconds |
| --- | --- | --- | --- | ---: |
| coupon-stacking | yes | yes | `reproduced` | 85.42 |
| tax-rounding | yes | yes | `reproduced` | 153.14 |
| stock-boundary | yes | yes | `reproduced` | 109.39 |
| stale-cart-total | yes | yes | `hypothesis_only_frontend` | 33.31 |

Overall: 4/4 file matches, 4/4 cause matches, and 4/4 expected statuses.
