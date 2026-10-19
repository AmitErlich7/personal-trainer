# Personal Running Coach: Design & Build Plan

## Context
Amit wants a personal endurance coach app for himself and a few friends. It pulls workouts from Garmin watches, gives a weekly recap, suggests next week's workouts, and tracks progress toward a goal race (marathon, half marathon, 70.3, or full Ironman). The suggestions follow the logic of known coaches, taken from articles Amit loads, with the app's own safety rules on top. This is Amit's first real coding project, so every step has to be understandable and come with an explanation. The project folder (`C:\Users\amitb\OneDrive\Documentos\personal-trainer`) is empty and not yet a git repo.

## Intent and success
- **Success:** each Sunday you open the app on your phone and see what you did, what to do next week, and where you stand against your goal. The suggestions feel realistic for your level.
- **Anti-goal (from Amit):** an unrealistic suggestion that doesn't fit the goal or current level. If that happens, the app has failed even though it technically works.
- **Learning goal:** Amit understands every piece. Claude writes the code in small steps. After each step comes a plain-English walkthrough and a short "try changing X" exercise, and Amit reviews it before we continue.

## Goals
1. Sync workouts from Garmin per user, with manual .FIT upload as a backup.
2. Weekly recap: sessions, volume per sport, intensity mix, comparison to plan.
3. Next-week suggestions: concrete workouts (day, sport, duration/distance, target pace/HR/power zone, purpose).
4. Progress toward goal: weeks to race, current training phase, actual vs target volume curve, long-session progression.
5. Coach libraries: admin (Amit) creates named libraries per goal type from articles. Each user picks one library for their goal.

## Non-goals
- No chat or conversation with a coach. Output is data on screen only (Amit's words).
- No native iOS/Android app and no app stores.
- No pushing workouts to the watch, no nutrition, no social features or leaderboards (v1).
- Friends don't see each other's data *(my call)*.

## Decisions Amit made
- Phone-first. All output lives inside the app.
- Backend in **Python**, frontend in **JavaScript**.
- Garmin via a library, plus a backup input path.
- Libraries per goal type. Each person picks which one to follow.
- Hosted, budget **under ~$10/month**.
- Learning mode: Claude writes the code, Amit reviews each step.

## My calls (Amit can override)
- **PWA (installable web app)** instead of a native app: one codebase, friends just open a link.
- **Garmin library: `python-garminconnect` 0.3.x** (cyberjunky). `garth` was deprecated in March 2026 and most other projects on the topic page depend on it. The library is unofficial and Garmin blocked it several times in 2026, so the sync code is isolated in one module and failures show as "sync failed, upload a .FIT file" rather than crashing.
- **Backup input: manual .FIT upload**, parsed with `fitdecode`. Strava isn't used because new Strava API apps are limited to a single athlete until Strava reviews them.
- **Backend:** FastAPI + SQLModel + SQLite (a single file, easy to inspect while learning). Hosting on Railway with a persistent volume (~$5/mo). If the database ever needs to grow, switching to Postgres is a one-line change.
- **Frontend:** React + Vite in plain JavaScript (no TypeScript, to keep the learning curve lower). Chart.js for progress charts.
- **AI:** Claude API (Sonnet-class model) for (a) distilling articles into coaching principles and (b) generating weekly workouts as structured JSON. Estimated $1–5/month.
- **App login:** invite code + email/password (hashed). Garmin tokens are encrypted at rest (Fernet key in an environment variable), because a token gives access to the person's Garmin account.
- **Weekly job:** runs automatically Sunday evening (sync → metrics → recap → plan), plus a "Refresh now" button.

## Goal setup and status (decided by Amit after the review)
- **New-goal intake:** when a user sets a new goal, the app asks a few short questions about their current state: current weekly volume per sport, longest recent session, a recent race or time-trial result, training history, and injuries. Garmin data fills in whatever it can.
- **Realism check:** if the goal is unrealistic for that state and date, the app shows a realistic time span (for example "a full Ironman from where you are needs ~9–12 months; your race is in 10 weeks"). If the user submits the same goal and date again, the app accepts it and generates a plan. *My call:* the guardrails still apply in that case, so the plan builds safely from the user's real level, and the Progress screen keeps showing the gap honestly.
- **Status buttons** on the This Week screen: sick, injured, traveling, want an easier week. The next week's plan reads them. Sick or injured triggers a "returning from a break" ramp, traveling reduces available days, and easier week cuts volume. No chat.

## Also my calls (from the review)
- **Training zones:** taken from Garmin user settings (HR zones, FTP, threshold) where the library exposes them. Otherwise worked out from recent workouts. Editable in Settings. "Hard day" means any session with meaningful time above the threshold zone, or a session marked as a key workout.
- **Load for triathlon:** measured in **time** (hours) per sport *and* in total. The ramp limit applies to the total and to each sport. Runners also see distance. The Progress chart shows actual vs target weekly hours (and km for running).

## How the coaching works
1. **Library creation (admin, rare):** paste article text or upload a PDF into a library tagged with a goal type. Claude distills the library into a structured "principles" document (phases, intensity distribution, long-session rules, key workout types, taper). Amit reviews and edits it in the app. Weekly plans use this document, not the raw articles, which keeps them consistent and cheap.
2. **Athlete level (pure Python, no AI):** from the last 4–6 weeks per sport: average weekly volume, longest session, sessions/week, recent paces/HR/power, and Garmin VO2max if available.
3. **Profile inputs:** goal type, race date, optional target time, available days and max hours per week, chosen library.
4. **Plan generation:** Claude receives the principles + level + phase (from weeks to race) + last week's recap + availability, and returns JSON workouts.
5. **Guardrails (pure Python, unit-tested):** this layer answers the anti-goal. The plan is checked against hard limits: weekly volume ≤ ~10% above the recent 4-week average, long session ≤ ~10% longer than the recent longest, workouts only on available days, no back-to-back hard days, paces derived from recent actual performance, and taper/recovery-week rules. A violation is clamped or triggers one regeneration. Each limit is a named constant that's easy to read and change.

## Screens (PWA)
Login/invite → Onboarding (goal, race date, library, availability, connect Garmin or upload FIT) → **This Week** (recap) → **Next Week** (suggested workouts) → **Progress** (charts) → Settings. Admin only: **Libraries**.

## Build milestones (each step: build, walkthrough, exercise, Amit reviews)
0. Tooling: install Python, Node, Git. `git init`. Project layout `backend/`, `frontend/`. Design and plan files live directly in the project root.
1. Backend skeleton: FastAPI hello-world, data models (User, Activity, Goal, Library, Article, WeeklyPlan).
2. Garmin sync for one user via a script → store activities. FIT upload parser.
3. Metrics/level calculation + pytest tests.
4. Weekly recap endpoint.
5. Libraries + article ingestion + principles distillation.
6. Plan generation + guardrails (heavily tested).
7. Frontend PWA screens + charts.
8. Multi-user: invites, auth, encrypted Garmin tokens, MFA prompt flow.
9. Deploy to Railway + Sunday scheduler + install on phones.

## Left to the builder
- Exact guardrail numbers per sport, tuned with Amit later.
- Mapping Garmin activity types to swim/bike/run/other.
- Whether `python-garminconnect` can load and save tokens from a string (needed for DB storage) or needs a per-user temp directory. Verify in step 2.
- Chart design details.

## Verification
- `pytest` for metrics, guardrails, FIT parsing, and plan JSON validation (fixtures from real exported activities).
- Run locally: `uvicorn` + `npm run dev`, open on phone over LAN, and check all screens with real data from Amit's Garmin.
- Feed a deliberately aggressive fake AI response into the guardrails and confirm it gets clamped.
- After deploy: friend onboarding end-to-end, and the Sunday job runs and produces a recap + plan.
