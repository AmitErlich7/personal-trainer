# Working with Git and GitHub

The rules for how code gets into this project. Claude follows them every session. Amit approves every change.

## The short version

1. Nothing is ever pushed straight to `main`.
2. Every piece of work happens on its own **branch**.
3. Every commit is **one logical change**, and the tests pass at that commit.
4. Every push goes into a **pull request (PR)**, and Amit reviews it on GitHub.
5. Only Amit merges. Claude never merges, never pushes to `main`, and never force-pushes.

## Words you'll see

- **Branch:** a separate line of work. `main` is the "official" version. A branch is a copy you can change safely without touching `main`.
- **Commit:** a saved snapshot with a message saying what changed and why.
- **Push:** uploading your branch's commits to GitHub.
- **Pull request (PR):** a request on GitHub to bring a branch into `main`. It shows every changed line, so you can read it, comment, and then merge it or ask for changes.
- **Merge:** bringing an approved branch into `main`.

## 1. Branches

- One branch per plan task (or per fix).
- Name: `<type>/<short-description>`. For example: `feat/plan1-task1-health-check`, `fix/recap-empty-week`, `docs/git-workflow`.
- Always start from an up-to-date `main`:

  ```
  git switch main
  git pull
  git switch -c feat/plan1-task2-database
  ```

## 2. Commits: one logical change each

A commit is **logical** when all of these are true:

- **It does one thing.** "Add the User model" is one thing. "Add the User model and fix a typo in the plan" is two commits.
- **It's complete.** The code and its tests go in the same commit, and `pytest` passes at that commit. Never commit something that's half done or broken.
- **Its message explains it.** Use this format:

  ```
  <type>: <what changed, in the imperative, max ~72 characters>

  <optional: why, if it isn't obvious from the code>
  ```

  Types:

  | Type | Use it for |
  |---|---|
  | `feat` | a new capability |
  | `fix` | a bug fix |
  | `test` | tests only |
  | `refactor` | same behavior, cleaner code |
  | `docs` | documentation |
  | `chore` | setup, tooling, dependencies |

  Good: `feat: add weekly recap endpoint`. Bad: `stuff`, `wip`, `fixes`.

- **No secrets, ever.** Check `git status` before every commit. Tokens, `.env`, and database files are in `.gitignore` for this reason.

## 3. Pull requests: every push is reviewed

- When a task is finished, Claude pushes the branch:

  ```
  git push -u origin feat/plan1-task2-database
  ```

  Claude then gives Amit the PR title and a filled-in description in the chat.
- Amit opens the PR on the GitHub website. Click the yellow **"Compare & pull request"** banner, or the link that `git push` prints. The description box is pre-filled with the template (`.github/pull_request_template.md`). Paste Claude's text over it and click **Create pull request**.
- **One PR per plan task.** That keeps every review small enough to actually read.
- If Amit asks for changes, he copies his comments into the chat. Claude adds **new commits** to the same branch (no rewriting history) and pushes again. The PR updates by itself.

## 4. Reviewing a PR (Amit)

1. Open the PR on GitHub and go to the **Files changed** tab.
2. Read every changed line. Click a line to leave a comment or question, then paste it into the chat with Claude.
3. Check that the tests passed (the "How to test" section, or run them yourself).
4. When you understand all of it and you're happy, merge using **"Create a merge commit"**. This keeps each logical commit in `main`'s history.
5. GitHub deletes the branch after merging. Locally, run:

   ```
   git switch main
   git pull
   ```

## What enforces these rules

- **Locally:** a git hook (`.githooks/pre-push`) refuses any push to `main` from this computer. It's turned on with `git config core.hooksPath .githooks` (run once after cloning).
- **On GitHub (set once by Amit, Settings → General → Pull Requests):** only "Allow merge commits" is ticked, and "Automatically delete head branches" is on.
- **Honest limits:**
  - GitHub's "protected branch" rules, which would block merging without an approval, are not available for **private** repos on a free account.
  - GitHub also doesn't let you formally "Approve" a PR that comes from your own account, and Claude pushes as you.
  - So the review is a **rule we keep**: Amit reads every PR before merging it, and Claude never merges. If you get GitHub Pro later, we can turn on real branch protection.
