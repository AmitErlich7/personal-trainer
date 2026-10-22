# Plan 1: Foundation (data in → level → weekly recap) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A Python backend that pulls one person's workouts from Garmin (or a .FIT upload), stores them, calculates their current training level, and returns a weekly recap through an API you can try in the browser.

**Architecture:** A FastAPI app with a SQLite database through SQLModel. Garmin code stays in one module (`app/ingest/garmin_sync.py`), so when Garmin breaks, only that file changes. Everything that calculates (sport mapping, weeks, level, recap) is pure Python with no database or network access, which keeps it easy to test and easy to read.

**Tech Stack:** Python 3.12, FastAPI, Uvicorn, SQLModel (SQLite), python-garminconnect 0.3.x, fitdecode, python-multipart, pytest, httpx.

**Spec:** `running-coach-design.md` (project root) covers milestones 0–4 of that design. Later plans: **Plan 2:** coach libraries, goals, intake, plan generation, and guardrails (milestones 5–6). **Plan 3:** the PWA frontend (7). **Plan 4:** multi-user, encrypted tokens, and deploy (8–9).

**Scope note:** The spec's milestone 1 lists all models. This plan creates only `User` and `Activity`. `Goal`, `Library`, `Article`, and `WeeklyPlan` arrive in Plan 2 with the code that uses them. Also, "comparison to plan" in the recap needs plans to exist, so it moves to Plan 2.

## Global Constraints

- **Learning mode (Amit's decision):** every task ends with a **Walkthrough** step. It explains each new file in plain English, gives one short "try changing X and see what happens" exercise, and then **stops and waits for Amit's review** before the next task starts.
- Python **3.12** (`py -3.12`), in a virtual env at `backend/.venv`.
- Weeks run **Monday–Sunday** and are based on the activity's **local** start time.
- Sports are exactly: `"run"`, `"bike"`, `"swim"`, `"other"`.
- Volume is measured in **time** (hours) per sport and in total. Distance (km) is also reported.
- Level window: `LEVEL_WINDOW_WEEKS = 4` (spec: "last 4–6 weeks"), a named constant.
- Garmin failures never crash the app. The API returns **HTTP 502** with the detail `"Garmin sync failed: <reason>. You can upload a .FIT file instead."`
- Secrets and tokens are never committed. `backend/.garmin_tokens/`, `.env`, `*.db`, `.venv/`, and `node_modules/` go in `.gitignore`.
- Style: small files, type hints, a short docstring on every public function (Amit is learning from them).

## Review Focus

1. **The same workout arrives twice** (Garmin sync and a .FIT upload of the same run) → it's stored once. Tested in Task 4.
2. **An empty week** (sick, vacation) → the recap returns zeros and an empty session list, with no error. Tested in Task 8.
3. **Garmin refuses the login or the request** (expired token, 401/429) → 502 with the friendly message, never 500. Tested in Task 6.
4. **Activities missing data** (strength session with no distance, indoor swim with no HR) → stored with `None` fields, and their time counts as `unknown` intensity. Tested in Tasks 5 and 8.
5. **A corrupt or non-FIT file is uploaded** → 400 `"Could not read this file as a .FIT activity."` Tested in Task 5.

---

## File Structure

```
personal-trainer/
  .gitignore
  CLAUDE.md                      # standing instructions: learning mode
  running-coach-design.md        # the design
  plan-1-foundation.md           # this plan (later plans sit next to it)
  backend/
    requirements.txt
    app/
      __init__.py
      main.py                    # creates FastAPI app, includes routers, /health
      db.py                      # engine, init_db(), get_session()
      models.py                  # User, Activity tables
      sports.py                  # map Garmin/FIT sport names -> run/bike/swim/other
      weeks.py                   # week_start(), week_range()
      ingest/
        __init__.py
        schemas.py               # ActivityIn (data coming in, before saving)
        store.py                 # save_activities() with dedupe
        fit_upload.py            # .FIT -> ActivityIn
        garmin_sync.py           # ALL Garmin code lives here
      metrics/
        __init__.py
        zones.py                 # HR zone seconds -> easy/moderate/hard
        level.py                 # compute_level()
        recap.py                 # build_recap()
      routes/
        __init__.py
        users.py
        activities.py            # upload-fit, sync-garmin
        reports.py               # level, recap
    scripts/
      garmin_login.py            # one-time interactive login (handles MFA)
    tests/
      conftest.py                # in-memory DB + TestClient fixtures
      fixtures/garmin_activity_run.json
      fixtures/sample_run.fit    # exported by Amit (Task 5)
      test_*.py
```

---

### Task 1: Project setup + health check

**Files:**
- Create: `.gitignore`, `CLAUDE.md`, `backend/requirements.txt`, `backend/app/__init__.py`, `backend/app/main.py`, `backend/tests/test_health.py`

**Interfaces:**
- Produces: `app.main.app` (the FastAPI instance). `GET /health` → `{"status": "ok"}`.

- [x] **Step 1: `git init` at the project root.** Create `.gitignore` with the entries from Global Constraints plus `__pycache__/`, `.pytest_cache/`.
- [x] **Step 2: Create `CLAUDE.md`.** Describe the project in one paragraph and link `running-coach-design.md` and the `plan-*.md` files in the project root. Learning-mode rules: small steps, plain-English walkthrough of every new file, one "try changing X" exercise per task, wait for Amit's review before continuing. Amit is new to coding, so explain terms the first time they appear.
- [x] **Step 3: Create the venv and install.** Run `py -3.12 -m venv backend/.venv`. List `fastapi uvicorn[standard] sqlmodel garminconnect fitdecode python-multipart pytest httpx` in `backend/requirements.txt`. Install them, then pin exact versions using the output of `pip freeze` (only those packages).
- [x] **Step 4: Write the failing test** `backend/tests/test_health.py`:

```python
from fastapi.testclient import TestClient
from app.main import app

def test_health_returns_ok():
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [x] **Step 5: Run** `cd backend; .venv\Scripts\python -m pytest tests/test_health.py -v`. Expected: FAIL (`No module named 'app.main'`).
- [x] **Step 6: Implement `app/main.py`** with `app = FastAPI(title="Running Coach")` and the `/health` route.
- [x] **Step 7: Run the test.** Expected: PASS. Also run `.venv\Scripts\uvicorn app.main:app --reload` and open `http://127.0.0.1:8000/docs` to show Amit the auto-generated API page.
- [x] **Step 8: Commit** everything, including the design and plan files: `git commit -m "chore: project setup, design doc, health check"`.
- [ ] **Step 9: Walkthrough.** Explain: what a virtual env is, what FastAPI does, and how the test works. Exercise: add `"app": "running-coach"` to the health response, watch the test fail, then fix the test. Wait for review.

---

### Task 2: Database + User and Activity models

**Files:**
- Create: `backend/app/db.py`, `backend/app/models.py`, `backend/app/routes/__init__.py`, `backend/app/routes/users.py`, `backend/tests/conftest.py`, `backend/tests/test_users.py`
- Modify: `backend/app/main.py` (include users router, call `init_db()` on startup)

**Interfaces:**
- Produces:
  - `db.get_session()`: a FastAPI dependency that yields a `Session`. `db.init_db()` creates the tables. The database URL comes from env var `DATABASE_URL`, default `sqlite:///./coach.db`.
  - `models.User`: `id: int | None (pk)`, `name: str`, `email: str (unique)`, `max_hr: int | None`, `is_admin: bool = False`.
  - `models.Activity`: `id: int | None (pk)`, `user_id: int (fk users.id, index)`, `source: str` ("garmin"|"fit"), `external_id: str`, `sport: str`, `name: str | None`, `start_time_local: datetime (index)`, `duration_s: float`, `distance_m: float | None`, `avg_hr: float | None`, `max_hr: float | None`, `avg_power: float | None`, `elevation_gain_m: float | None`, `hr_zone_seconds: list[float] | None` (JSON column, 5 entries Z1..Z5). Unique constraint `(user_id, source, external_id)`.
  - `POST /users` (body `name`, `email`; `max_hr` is not part of signup and starts empty) → 201 + user JSON. `GET /users/{user_id}` → user or 404 `"User not found"`.
  - `tests/conftest.py`: fixture `session` (in-memory SQLite, `StaticPool`) and fixture `client` (TestClient with `get_session` overridden to use it).

- [x] **Step 1: Write the failing tests** in `test_users.py`:
  - `test_create_user_returns_201_and_id`: posting `{"name": "Amit", "email": "a@x.com"}` returns 201, `id` is an int, and `max_hr` is `None`.
  - `test_get_user_404`: `GET /users/999` returns 404 with detail `"User not found"`.
  - `test_duplicate_email_rejected`: a second POST with the same email returns 409.
- [x] **Step 2: Run** `pytest tests/test_users.py -v`. Expected: FAIL (import errors).
- [x] **Step 3: Implement** `db.py`, `models.py`, `routes/users.py`. Wire them into `main.py` using a FastAPI lifespan that calls `init_db()`.
- [x] **Step 4: Run** `pytest -v`. Expected: all PASS.
- [x] **Step 5: Commit** `feat: database with User and Activity models`.
- [ ] **Step 6: Walkthrough.** Explain tables and rows, primary/foreign keys, what a "dependency" is in FastAPI, and why tests use an in-memory database. Exercise: open `coach.db` with the free "DB Browser for SQLite" after creating a user through `/docs`. Wait for review.

---

### Task 3: Sport mapping + week helpers

**Files:**
- Create: `backend/app/sports.py`, `backend/app/weeks.py`, `backend/tests/test_sports.py`, `backend/tests/test_weeks.py`

**Interfaces:**
- Produces:
  - `sports.to_sport(raw: str | None) -> str`: the mapping is case-insensitive. Run: `running, trail_running, treadmill_running, track_running, indoor_running, virtual_run`. Bike: `cycling, road_biking, mountain_biking, gravel_cycling, indoor_cycling, virtual_ride`. Swim: `swimming, lap_swimming, open_water_swimming`. Anything else, including `None`, is `"other"`. FIT sport names `running`, `cycling`, and `swimming` are covered by the same table.
  - `weeks.week_start(d: date | datetime) -> date`: returns the Monday on or before `d`.
  - `weeks.week_range(monday: date) -> tuple[datetime, datetime]`: returns `[Monday 00:00, next Monday 00:00)`, naive local times.

- [ ] **Step 1: Write failing tests:**
  - `to_sport("Trail_Running") == "run"`, `to_sport("virtual_ride") == "bike"`, `to_sport("open_water_swimming") == "swim"`, `to_sport("strength_training") == "other"`, `to_sport(None) == "other"`.
  - `week_start(date(2026, 10, 18)) == date(2026, 10, 12)` (Sunday → previous Monday). `week_start(date(2026, 10, 12)) == date(2026, 10, 12)`. `week_start(datetime(2026, 10, 18, 23, 59)) == date(2026, 10, 12)`.
  - `week_range(date(2026, 10, 12)) == (datetime(2026, 10, 12), datetime(2026, 10, 19))`.
- [ ] **Step 2: Run them.** Expected: FAIL.
- [ ] **Step 3: Implement** both modules. `to_sport` uses a dict of sets.
- [ ] **Step 4: Run.** Expected: PASS.
- [ ] **Step 5: Commit** `feat: sport mapping and week helpers`.
- [ ] **Step 6: Walkthrough.** Explain dicts and sets, `date` vs `datetime`, and half-open ranges. Exercise: add `"hiking"` → `"other"` explicitly and write the test first. Wait for review.

---

### Task 4: Incoming activity schema + storage with dedupe

**Files:**
- Create: `backend/app/ingest/__init__.py`, `backend/app/ingest/schemas.py`, `backend/app/ingest/store.py`, `backend/tests/test_store.py`

**Interfaces:**
- Consumes: `models.Activity`, `models.User` (Task 2).
- Produces:
  - `schemas.ActivityIn`: a pydantic model with the same fields as `Activity`, minus `id` and `user_id`.
  - `store.save_activities(session: Session, user_id: int, items: list[ActivityIn]) -> int`: returns the number of **new** rows saved. It skips an item when either of these is true:
    - (a) the same `(user_id, source, external_id)` already exists, or
    - (b) a **cross-source duplicate** exists: same user, same sport, `start_time_local` within **60 s**, and `duration_s` within **5 %**.

- [ ] **Step 1: Write failing tests:**
  - `test_saves_new_activities`: saving two different items returns 2.
  - `test_same_external_id_not_saved_twice`: saving the same item twice returns 1 and then 0.
  - `test_garmin_and_fit_copy_counted_once` (Review Focus #1): a garmin item, then a fit item of the same run starting 20 s later with a 2 % longer duration. Returns 1, then 0, and the table has 1 row.
  - `test_different_sport_same_time_both_saved`: a run and a bike at the same time both get saved (brick workouts).
- [ ] **Step 2: Run.** Expected: FAIL.
- [ ] **Step 3: Implement** `save_activities`. Query the user's activities of that sport within ±60 s of the start time, then check duration. Commit the session once at the end.
- [ ] **Step 4: Run.** Expected: PASS.
- [ ] **Step 5: Commit** `feat: store activities with duplicate detection`.
- [ ] **Step 6: Walkthrough.** Explain why the data coming in (`ActivityIn`) is kept separate from the table (`Activity`), and how the duplicate rule works. Exercise: change the window to 10 s and see which test breaks. Wait for review.

---

### Task 5: .FIT file parsing + upload endpoint

**Files:**
- Create: `backend/app/ingest/fit_upload.py`, `backend/app/metrics/__init__.py`, `backend/app/metrics/zones.py`, `backend/app/routes/activities.py`, `backend/tests/test_fit_upload.py`, `backend/tests/test_zones.py`, `backend/tests/fixtures/sample_run.fit`
- Modify: `backend/app/main.py` (include activities router)

**Interfaces:**
- Consumes: `to_sport` (Task 3), `ActivityIn`, `save_activities` (Task 4).
- Produces:
  - `zones.hr_zone_seconds(hr_samples: list[tuple[float, float]], max_hr: int) -> list[float]`: the samples are `(seconds_elapsed, bpm)`. Each interval goes to a zone by %max HR: Z1 <60, Z2 60–<70, Z3 70–<80, Z4 80–<90, Z5 ≥90. The time of each interval is attributed to the HR at its start.
  - `zones.intensity_buckets(zone_seconds: list[float] | None) -> dict`: returns `{"easy": Z1+Z2, "moderate": Z3, "hard": Z4+Z5}`, or `None` if the input is `None`.
  - `fit_upload.FitParseError(Exception)`.
  - `fit_upload.parse_fit(data: bytes, max_hr: int | None) -> ActivityIn`: reads the `session` message (sport, start_time, total_timer_time, total_distance, avg/max_heart_rate, avg_power, total_ascent) and the `record` messages (timestamp, heart_rate). `source="fit"`, and `external_id` is the sha256 hex of the bytes. `hr_zone_seconds` is computed only when `max_hr` is set and records have HR. Otherwise it's `None`. Local time: if an `activity` message has `local_timestamp`, apply its offset. Otherwise use UTC. Raises `FitParseError` on any fitdecode error or when no `session` message exists.
  - `POST /users/{user_id}/activities/upload-fit` (multipart `file`) → `{"saved": int}`. Unknown user → 404. Parse error → **400** `"Could not read this file as a .FIT activity."`

- [ ] **Step 1: Get a real fixture.** Ask Amit to export one recent run from Garmin Connect (web: activity → ⚙ → "Export Original", then unzip) and save it as `backend/tests/fixtures/sample_run.fit`.
- [ ] **Step 2: Write failing tests:**
  - zones: `hr_zone_seconds([(0, 100), (60, 150), (120, 185), (180, 185)], max_hr=200)` returns `[60, 0, 60, 0, 60]`. `intensity_buckets([10, 20, 30, 40, 50]) == {"easy": 30, "moderate": 30, "hard": 90}`. `intensity_buckets(None) is None`.
  - `test_parse_real_fit_file`: `parse_fit(fixture_bytes, max_hr=190)` gives `sport == "run"`, `duration_s > 0`, `distance_m > 0`, `len(hr_zone_seconds) == 5`.
  - `test_parse_without_max_hr_has_no_zones`: `hr_zone_seconds is None`.
  - `test_upload_garbage_returns_400` (Review Focus #5): uploading `b"not a fit file"` returns 400 with the exact message.
  - `test_upload_twice_saves_once`: two uploads of the fixture return `saved` 1, then 0.
- [ ] **Step 3: Run.** Expected: FAIL.
- [ ] **Step 4: Implement** `zones.py`, `fit_upload.py`, `routes/activities.py`. The route reads the user's `max_hr` from the DB.
- [ ] **Step 5: Run.** Expected: PASS.
- [ ] **Step 6: Commit** `feat: .FIT upload with HR zones` (the fixture contains Amit's GPS track; ask Amit before committing it, and if he'd rather not, add it to `.gitignore` and mark the real-file tests `skipif` missing).
- [ ] **Step 7: Walkthrough.** Explain what a FIT file is, how bytes become fields, and what a hash is. Exercise: change the Z2 boundary to 65 % and predict which zone test fails. Wait for review.

---

### Task 6: Garmin sync (isolated module) + login script + sync endpoint

**Files:**
- Create: `backend/app/ingest/garmin_sync.py`, `backend/scripts/garmin_login.py`, `backend/tests/fixtures/garmin_activity_run.json`, `backend/tests/test_garmin_sync.py`
- Modify: `backend/app/routes/activities.py`

**Interfaces:**
- Consumes: `to_sport`, `ActivityIn`, `save_activities`.
- Produces:
  - `garmin_sync.GarminSyncError(Exception)`.
  - `garmin_sync.token_dir_for(user_id: int) -> Path`: returns `backend/.garmin_tokens/<user_id>` (gitignored; replaced by encrypted DB storage in Plan 4).
  - `garmin_sync.summary_to_activity(summary: dict) -> ActivityIn`: a pure function. Fields: `activityId`→external_id (str), `activityName`, `activityType.typeKey`→`to_sport`, `startTimeLocal` ("YYYY-MM-DD HH:MM:SS"), `duration`, `distance`, `averageHR`, `maxHR`, `avgPower`, `elevationGain`, and `hrTimeInZone_1..5` → `hr_zone_seconds` (`None` if all are missing). `source="garmin"`.
  - `garmin_sync.fetch_activities(user_id: int, start: date, end: date) -> list[ActivityIn]`: resumes the session from `token_dir_for(user_id)`, then calls `get_activities_by_date(start.isoformat(), end.isoformat())`. **Any** exception from the library becomes a `GarminSyncError(str(e))`. Missing tokens raise `GarminSyncError("not logged in, run scripts/garmin_login.py")`.
  - `scripts/garmin_login.py --user-id N`: prompts for email and password (`getpass`) and the MFA code via `input()`, then logs in and saves tokens to `token_dir_for(N)`. It never prints or stores the password.
  - `POST /users/{user_id}/sync-garmin?days=28` → `{"fetched": int, "saved": int}`. A `GarminSyncError` becomes **502** with `"Garmin sync failed: <reason>. You can upload a .FIT file instead."`

- [ ] **Step 1: Check the installed library.** Run `.venv\Scripts\python -c "import garminconnect, inspect; print(garminconnect.__version__); print(inspect.signature(garminconnect.Garmin.__init__)); print(inspect.signature(garminconnect.Garmin.login))"`. Confirm how a token directory is passed and how MFA is prompted, and write the exact calls in a comment at the top of `garmin_sync.py`. **This is the only place those calls are allowed.** Also note whether tokens can be loaded from or saved to a string (the spec's open question for Plan 4).
- [ ] **Step 2: Create the fixture** `garmin_activity_run.json` with this sample summary: `{"activityId": 123456789, "activityName": "Morning Run", "activityType": {"typeKey": "running"}, "startTimeLocal": "2026-10-12 07:01:22", "duration": 3605.2, "distance": 10012.5, "averageHR": 148.0, "maxHR": 171.0, "avgPower": null, "elevationGain": 64.0, "hrTimeInZone_1": 120.0, "hrTimeInZone_2": 2400.0, "hrTimeInZone_3": 900.0, "hrTimeInZone_4": 185.2, "hrTimeInZone_5": 0.0}`.
- [ ] **Step 3: Write failing tests:**
  - `test_summary_to_activity_maps_fields`: `sport == "run"`, `external_id == "123456789"`, `start_time_local == datetime(2026, 10, 12, 7, 1, 22)`, `hr_zone_seconds == [120.0, 2400.0, 900.0, 185.2, 0.0]`, `avg_power is None`.
  - `test_summary_without_zones_or_distance`: delete the zone keys and set `distance` to None. The result has `hr_zone_seconds is None` and `distance_m is None` (Review Focus #4).
  - `test_sync_endpoint_returns_502_on_garmin_error` (Review Focus #3): monkeypatch `garmin_sync.fetch_activities` to raise `GarminSyncError("429 Too Many Requests")`. The response is 502 and the detail is `"Garmin sync failed: 429 Too Many Requests. You can upload a .FIT file instead."`
  - `test_sync_endpoint_saves`: monkeypatch it to return `[summary_to_activity(fixture)]`. The response is `{"fetched": 1, "saved": 1}`.
- [ ] **Step 4: Run.** Expected: FAIL.
- [ ] **Step 5: Implement** the module, the script, and the route.
- [ ] **Step 6: Run.** Expected: PASS.
- [ ] **Step 7: Real-world check with Amit:** run `.venv\Scripts\python scripts/garmin_login.py --user-id 1` (Amit types his own credentials), then call `POST /users/1/sync-garmin` from `/docs`. Expected: `fetched` > 0. If Garmin's real field names differ from the fixture, update the fixture and the mapping together.
- [ ] **Step 8: Commit** `feat: Garmin sync isolated behind GarminSyncError`.
- [ ] **Step 9: Walkthrough.** Explain why all Garmin code lives in one file, what a token is and why it's secret, and what monkeypatching does in tests. Exercise: sync 7 days instead of 28 and compare the counts. Wait for review.

---

### Task 7: Athlete level

**Files:**
- Create: `backend/app/metrics/level.py`, `backend/app/routes/reports.py`, `backend/tests/test_level.py`
- Modify: `backend/app/main.py` (include reports router)

**Interfaces:**
- Consumes: `Activity`, `week_start`, `week_range`.
- Produces:
  - `level.LEVEL_WINDOW_WEEKS = 4`.
  - `level.SportLevel` (pydantic): `avg_weekly_hours: float`, `avg_weekly_km: float | None`, `sessions_per_week: float`, `longest_session_min: float`, `longest_session_km: float | None`, `avg_pace_min_per_km: float | None` (run), `avg_speed_kmh: float | None` (bike), `avg_pace_min_per_100m: float | None` (swim), `avg_hr: float | None`, `avg_power: float | None`.
  - `level.AthleteLevel`: `as_of_week: date`, `weeks_with_data: int`, `total_avg_weekly_hours: float`, `by_sport: dict[str, SportLevel]` (only sports that have activities).
  - `level.compute_level(activities: list[Activity], as_of: date) -> AthleteLevel`: the window is the `LEVEL_WINDOW_WEEKS` full weeks **before** `week_start(as_of)`. Averages always divide by `LEVEL_WINDOW_WEEKS`, not by the number of weeks with data, so missed weeks honestly lower the level. Paces and speeds are computed from total distance ÷ total time for activities that have a distance. HR and power averages are weighted by duration, ignoring `None`.
  - `GET /users/{user_id}/level?as_of=YYYY-MM-DD` (default today) → `AthleteLevel`.

- [ ] **Step 1: Write failing tests** using in-memory `Activity` objects (no DB):
  - Four weeks before 2026-10-19 with one 60-min, 10-km run per week, plus one 90-min, 15-km run in the week of 2026-09-28. The result: `by_sport["run"].avg_weekly_hours == 1.375` (5.5 h / 4), `sessions_per_week == 1.25`, `longest_session_min == 90`, `avg_pace_min_per_km == 6.0`.
  - An activity in the current week (2026-10-19) is **excluded**.
  - Only 2 of 4 weeks have data, at 2 h each: `avg_weekly_hours == 1.0` and `weeks_with_data == 2`.
  - No activities: `by_sport == {}`, `total_avg_weekly_hours == 0`, `weeks_with_data == 0`.
  - A swim of 1500 m in 30 min gives `avg_pace_min_per_100m == 2.0`.
- [ ] **Step 2: Run.** Expected: FAIL.
- [ ] **Step 3: Implement** `compute_level` and the route. The route loads the user's activities in the window and passes them in.
- [ ] **Step 4: Run.** Expected: PASS.
- [ ] **Step 5: Commit** `feat: athlete level from last 4 weeks`.
- [ ] **Step 6: Walkthrough.** Explain why level is plain math and not AI (this is the base the guardrails will use in Plan 2), and why the averages divide by 4. Exercise: change `LEVEL_WINDOW_WEEKS` to 6 and look at your own level in `/docs`. Wait for review.

---

### Task 8: Weekly recap

**Files:**
- Create: `backend/app/metrics/recap.py`, `backend/tests/test_recap.py`
- Modify: `backend/app/routes/reports.py`

**Interfaces:**
- Consumes: `Activity`, `week_range`, `intensity_buckets`, `compute_level`.
- Produces:
  - `recap.SessionSummary`: `date: date`, `sport: str`, `name: str | None`, `duration_min: float`, `distance_km: float | None`, `avg_hr: float | None`.
  - `recap.SportTotals`: `hours: float`, `km: float | None`, `sessions: int`.
  - `recap.WeeklyRecap`:
    - `week_start: date`, `week_end: date` (Sunday)
    - `sessions: list[SessionSummary]` (sorted by start time)
    - `by_sport: dict[str, SportTotals]`, `total_hours: float`
    - `intensity: dict` with keys `easy`, `moderate`, `hard`, `unknown` (in **minutes**). The time of an activity with no zone data goes to `unknown`.
    - `vs_level: dict[str, float | None]`: per sport, this week's hours ÷ that sport's `avg_weekly_hours` from `compute_level(..., as_of=week_start)`. `None` if there's no level for that sport.
  - `recap.build_recap(week_activities: list[Activity], level: AthleteLevel, monday: date) -> WeeklyRecap`
  - `GET /users/{user_id}/recap?week_start=YYYY-MM-DD` (default: the current week's Monday. A date that isn't a Monday gets snapped with `week_start()`) → `WeeklyRecap`.

- [ ] **Step 1: Write failing tests:**
  - A week with a 60-min run (zones `[0, 3000, 600, 0, 0]` s), a 120-min ride with no zones, and a 30-min strength session (`other`, no distance) gives:
    - `total_hours == 3.5`
    - `by_sport["bike"].sessions == 1`
    - `by_sport["other"].km is None`
    - `intensity == {"easy": 50, "moderate": 10, "hard": 0, "unknown": 150}`
  - `vs_level["run"] == 0.5` when the level says 2.0 run hours/week and this week has 1 h. `vs_level["bike"] is None` when the level has no bike.
  - `test_empty_week` (Review Focus #2): no activities gives `sessions == []`, `total_hours == 0`, `by_sport == {}`, and all intensity values 0.
  - Endpoint: `GET /users/1/recap?week_start=2026-10-14` (a Wednesday) returns `week_start == "2026-10-12"`.
- [ ] **Step 2: Run.** Expected: FAIL.
- [ ] **Step 3: Implement** `build_recap` and the route.
- [ ] **Step 4: Run the whole suite** with `pytest -v`. Expected: everything passes.
- [ ] **Step 5: Real-data check with Amit:** after the Garmin sync from Task 6, open `/users/1/recap` for last week and `/users/1/level` in `/docs`, and compare by eye with Garmin Connect's weekly totals. Hours per sport should match within a few minutes.
- [ ] **Step 6: Commit** `feat: weekly recap endpoint`.
- [ ] **Step 7: Walkthrough + wrap-up.** Explain how the pieces connect (sync → store → level → recap), and show the whole flow in `/docs`. Exercise: add a `longest_session_min` field to `SportTotals`, test first. Preview Plan 2 (coach libraries and AI plans). Wait for review.
