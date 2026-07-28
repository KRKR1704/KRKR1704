# Setup Guide

Everything needed to get this README live on your GitHub profile.

## 1. Create the special repository

GitHub renders a repo's `README.md` on your profile page only if the repo:

- Is named **exactly** the same as your username → `KRKR1704/KRKR1704`
- Is **public**
- Contains a `README.md` at the root

Steps:

1. Go to https://github.com/new
2. Repository name: `KRKR1704` (must match your username exactly)
3. Visibility: **Public**
4. Initialize with a README (or leave empty — you're pushing one anyway)
5. Clone it locally, then copy in the contents of this folder:
   - `README.md`
   - `profile.overrides.json`
   - `scripts/update_readme.py`
   - `.github/workflows/snake.yml`
   - `.github/workflows/update-readme.yml`
6. Commit and push to `main`.

```bash
git clone https://github.com/KRKR1704/KRKR1704.git
cd KRKR1704
# copy the files listed above into this folder, preserving their paths
git add .
git commit -m "Add profile README"
git push origin main
```

GitHub will show a green "Add a README on your profile" banner on your profile page once this is set up correctly (may take a minute to appear).

## 2. Featured Projects mirrors your GitHub pins — no file to hand-edit for that

The Featured Projects section between `<!--PROJECTS:START-->` and `<!--PROJECTS:END-->` in `README.md` is **generated**, not hand-written. Don't edit that block directly — anything you type there gets overwritten the next time the pipeline runs.

**To change what's featured, just pin or unpin repos on your GitHub profile normally** — go to your profile → **Customize your pins** → check up to 6 repos → Save. That's it. There is no file in this repo that lists which repos are featured; the script reads your live pins via the GitHub GraphQL API (`pinnedItems`) every time it runs, in the order they're pinned.

> ⚠️ **Action needed right now:** as of this update, your profile has `virtual-assistant`, `study-buddy`, and `DMSD_Project` pinned — not `ultron_v2` or `desktop_pet`. Until you re-pin `ultron_v2` and `desktop_pet` (and unpin whichever of the current three you don't want featured), a live run of this pipeline will show cards for your **current actual pins**, not the ULTRON/Founder Pet cards you're used to seeing in this README. Go to https://github.com/KRKR1704?tab=repositories → **Customize your pins** and fix this before the next scheduled run (or before you trigger one manually).

### Pin changes don't auto-trigger a run

Because pinning happens on github.com, not in this repo, it doesn't push a commit anywhere this workflow can see. The README picks up new pins on the **next scheduled daily run**, or immediately if you trigger the Action manually (see below) — it does not update the instant you click "Save" on the pins page.

### `profile.overrides.json` — for the two things the API can't know

The API gives real, live data for everything except: a short editorial note you want attached to a card, or a replacement description if a repo's GitHub description is empty or misleading. That's what this file is for, and it's the *only* file you should ever hand-edit for Featured Projects content:

```json
{
  "overrides": {
    "KRKR1704/some-repo": {
      "note": "Optional short note, e.g. \"(in progress) X, Y, Z — self-attested, not yet reflected in the repo\"",
      "description_override": "Optional replacement for an empty/bad GitHub description"
    }
  }
}
```

Key it by `owner/repo` exactly as it appears in the URL. A pinned repo with no entry here renders purely from live API data — no manual input required at all. Right now the only entry is `KRKR1704/ultron_v2`, carrying forward the "(in progress)" feature note from before — `desktop_pet` has no override because it didn't need one.

### What the generator actually pulls live, and what it can't

For each pinned repo it fetches: description, topics, byte-weighted language breakdown, star count, URL, homepage, private/public status, and last-pushed date. Badges come from GitHub **topics** if the repo has any set, otherwise from the real language breakdown (top 4 by bytes) — so if you want more descriptive badges (`fastapi`, `ollama`, `electron`, etc. instead of just `Python`/`TypeScript`), **add Topics to the repo on GitHub** (repo page → gear icon next to "About" → Topics). No code or override-file change needed; the next run picks them up.

If a repo has no description set on GitHub, the card shows `_No description set on GitHub yet._` unless you set `description_override` — but fixing the real GitHub description is the more durable option since it also improves how the repo looks everywhere else, not just here.

Card titles are currently the raw repo name (`ultron_v2`, `desktop_pet`) rather than a pretty display name like "ULTRON" — the pinned-items API doesn't carry a separate display name, and the current `profile.overrides.json` intentionally only carries the one note field, not a name override. If you want prettier titles back, say so and a `display_name` override field can be added to the schema.

### Remaining non-project placeholders

| Placeholder | Location | What to put there |
|---|---|---|
| `[ADD LINKEDIN URL]` | Header badge row | Your LinkedIn profile URL |
| `[ADD EMAIL]` | Header badge row (`mailto:`) | The email you want people to reach you at |

Everything else (typing SVG, badges, stats cards, streak card, top languages, snake animation, visitor counter) is already wired up to your username `KRKR1704` and needs no manual editing.

## 3. Permissions the Featured Projects Action needs

`update-readme.yml` needs the same **Settings → Actions → General → Workflow permissions → Read and write permissions** setting as the snake workflow (see below) — it commits `README.md` back to the repo.

**Unlike before, a PAT is effectively required now, not just optional.** GitHub's GraphQL API (needed to read `pinnedItems`) requires an authenticated request for *any* query, including public data — a plain unauthenticated request gets `403`, confirmed by testing directly. The default `GITHUB_TOKEN` Actions provides *might* be sufficient for reading your own public pinned-repo data, but this hasn't been verified against your account (no token was available while building this), so treat it as unverified rather than assume it works:

1. Create a **classic** Personal Access Token at https://github.com/settings/tokens → **Generate new token (classic)**.
2. Scope: **`read:user`** — this is enough to read public pinned-repo data. If you ever pin a **private** repo and want its real data (rather than it silently dropping out of the results), also check **`repo`**.
3. In `KRKR1704/KRKR1704` → **Settings → Secrets and variables → Actions**, add a repository secret named **`PROFILE_PAT`** with that token's value.
4. The workflow already prefers `PROFILE_PAT` over the default token (`secrets.PROFILE_PAT || secrets.GITHUB_TOKEN`) — no YAML changes needed once the secret exists.

To verify your token actually works before relying on the Action, test it directly:

```bash
curl -s -X POST https://api.github.com/graphql \
  -H "Authorization: Bearer YOUR_PAT_HERE" \
  -H "Content-Type: application/json" \
  -d '{"query":"query{ user(login:\"KRKR1704\"){ pinnedItems(first:6, types:[REPOSITORY]){ totalCount nodes { ... on Repository { name } } } } }"}'
```

A working token returns your pinned repo names in `data.user.pinnedItems.nodes`. If it instead returns an `errors` array or a null `user`, the error message tells you what's wrong (usually a missing scope) — the Action log shows the same detail if this fails in CI, and the workflow will **not** commit a broken README in that case; it just fails the step and leaves the last good README in place.

### Manually triggering a refresh

Don't want to wait for the daily 06:17 UTC cron? Go to the **Actions** tab → **"Update Featured Projects"** → **Run workflow**. It also runs automatically on every push to `main` that touches `profile.overrides.json` (pin changes themselves don't trigger it — see above).

## 4. Enable the snake contribution animation

**Status: already working.** As of this update, the repo's Actions permissions are correctly set to read/write, the workflow has run once successfully (triggered by your first push), and the `output` branch contains real generated SVGs pulling from your actual contribution graph — verified directly, not assumed. No action needed unless it ever breaks.

For reference, or if you ever need to re-enable this from scratch:

1. In the `KRKR1704/KRKR1704` repo, go to **Settings → Actions → General**
2. Scroll to **Workflow permissions**
3. Select **Read and write permissions**
4. Click **Save**
5. Go to the **Actions** tab, find **"Generate Snake Animation"**, and click **Run workflow** to regenerate manually (it also runs automatically on every push to `main` and once daily via cron).
6. Check the `output` branch for the regenerated SVGs — that's what the README's `<picture>` tag points to.

If the workflow ever fails with a permissions error, it's almost always step 3 above reverting (e.g. after a repo re-creation).

## 5. Notes on the color theme

The whole README uses one accent color — neon green (`#39FF14`) — against a dark background (`#0D1117`, GitHub's native dark background) across:

- The typing SVG
- All shields.io badges (`labelColor`/logo colors)
- The stats, streak, and top-languages cards

If you want to change the accent color, it's a find-and-replace of `39FF14` across `README.md` (and `0D1117` for the background if you want a different dark shade).

## 6. Stats card host — and what to do if it breaks again

The stats and top-languages cards point at `github-readme-stats-rickstaa.vercel.app`, a community-hosted mirror of the [anuraghazra/github-readme-stats](https://github.com/anuraghazra/github-readme-stats) project. The *official* `github-readme-stats.vercel.app` deployment was returning `503 DEPLOYMENT_PAUSED` for both endpoints at the time of this update — a real outage, confirmed by directly querying it, not assumed. The streak card (`streak-stats.demolab.com`) was unaffected and needed no change.

Community mirrors like this one aren't guaranteed to stay up. If either card ever shows a broken image or an "Application Error"/"Something went wrong" SVG instead of your stats:
1. Confirm it's actually broken by opening the image URL directly in a browser.
2. Try the official host again (`github-readme-stats.vercel.app`) — it may be back.
3. Or self-host your own instance by deploying the [github-readme-stats repo](https://github.com/anuraghazra/github-readme-stats) to your own Vercel account (the project's README has one-click deploy instructions) — this is the most durable fix since it's not dependent on a stranger's free-tier deployment staying alive.

Do not replace a broken card with a static image or hardcoded numbers — that defeats the purpose of a "live" stats section.

## 7. Optional polish

- Replace the capsule-render header banner text/colors if you want a different header style: https://github.com/kyechan99/capsule-render
- Add GitHub **Topics** and a real **description** to `ultron_v2` and `desktop_pet` (repo page → gear icon next to "About") — this is now the only way to get richer badges and card text, since there's no config file carrying that information anymore.
