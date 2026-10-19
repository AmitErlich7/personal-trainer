# Running Coach

A personal endurance coach app for Amit and a few friends. It pulls workouts from Garmin (or a .FIT upload), shows a weekly recap, suggests next week's workouts based on coach articles plus the app's own safety rules, and tracks progress toward a goal race (marathon, half marathon, 70.3, full Ironman). Backend: Python (FastAPI). Frontend: JavaScript (React PWA, Plan 3).

- Design: `running-coach-design.md`
- Plans: `plan-*.md` (start with `plan-1-foundation.md`; tick the checkboxes as tasks are done)
- Design docs and plans live in the project root, not in subfolders.

## Learning mode (always)

This is Amit's first real coding project. He must understand every line.

- Work in small steps, one plan task at a time.
- After each task, explain every new file in plain English. Explain a term the first time it shows up (venv, endpoint, fixture, ...).
- Give one short "try changing X and see what happens" exercise per task.
- Stop and wait for Amit's review before starting the next task.

## Git and GitHub (always, see `GIT-WORKFLOW.md`)

- Never commit or push to `main`. Work on a branch per plan task, e.g. `feat/plan1-task2-database`.
- Every commit is one logical change, with its tests, and `pytest` passes at that commit. Message: `<type>: <imperative summary>` (feat, fix, test, refactor, docs, chore).
- Every push gets a PR (`gh pr create`) using `.github/pull_request_template.md`, one PR per plan task.
- Review fixes go in as new commits on the same branch. No force-push, no rewriting history.
- Never merge PRs. Amit reviews and merges on GitHub.

## Commands

From `backend/`:

- Run tests: `.venv\Scripts\python -m pytest -v`
- Run the API: `.venv\Scripts\uvicorn app.main:app --reload`, then open http://127.0.0.1:8000/docs
