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
   - `.github/workflows/snake.yml`
6. Commit and push to `main`.

```bash
git clone https://github.com/KRKR1704/KRKR1704.git
cd KRKR1704
# copy README.md and .github/workflows/snake.yml into this folder
git add .
git commit -m "Add profile README"
git push origin main
```

GitHub will show a green "Add a README on your profile" banner on your profile page once this is set up correctly (may take a minute to appear).

## 2. Where to swap in real links

Search the README for these placeholders and replace them:

| Placeholder | Location | What to put there |
|---|---|---|
| `[ADD LINKEDIN URL]` | Header badge row | Your LinkedIn profile URL |
| `[ADD EMAIL]` | Header badge row (`mailto:`) | The email you want people to reach you at |
| `[ADD LINK]` (OweWise) | Featured Projects | OweWise repo or landing page URL |
| `[ADD LINK]` (ULTRON) | Featured Projects | ULTRON repo URL |
| `[ADD LINK]` (AgentVerifier) | Featured Projects | AgentVerifier/AgentRed repo URL |
| `[ADD LINK]` (DemoPilot) | Featured Projects | DemoPilot repo URL |
| `[ADD LINK]` (Founder Pet) | Featured Projects | Founder Pet repo URL |

Merchant Marquee is already linked to `merchantmarquee.com` — update it if the URL changes.

Everything else (typing SVG, badges, stats cards, streak card, top languages, snake animation, visitor counter) is already wired up to your username `KRKR1704` and needs no manual editing.

## 3. Enable the snake contribution animation

The snake animation (`.github/workflows/snake.yml`) needs GitHub Actions to have **write** permission so it can push the generated SVGs to an `output` branch.

1. In the `KRKR1704/KRKR1704` repo, go to **Settings → Actions → General**
2. Scroll to **Workflow permissions**
3. Select **Read and write permissions**
4. Click **Save**
5. Go to the **Actions** tab, find **"Generate Snake Animation"**, and click **Run workflow** once manually to generate the first output (it also runs automatically on every push to `main` and once daily via cron).
6. After it runs successfully, an `output` branch will appear in the repo containing the generated SVGs — this is what the README's `<picture>` tag points to.

If the workflow fails with a permissions error, it's almost always step 3 above (the default for new repos is read-only).

## 4. Notes on the color theme

The whole README uses one accent color — neon green (`#39FF14`) — against a dark background (`#0D1117`, GitHub's native dark background) across:

- The typing SVG
- All shields.io badges (`labelColor`/logo colors)
- The stats, streak, and top-languages cards

If you want to change the accent color, it's a find-and-replace of `39FF14` across `README.md` (and `0D1117` for the background if you want a different dark shade).

## 5. Optional polish

- Replace the capsule-render header banner text/colors if you want a different header style: https://github.com/kyechan99/capsule-render
- Pin actual repos on your GitHub profile (separately from this README) via **Profile → Customize your pins** so the Featured Projects section and your pinned repos stay consistent.
- Once OweWise, ULTRON, etc. have public repos, consider swapping the manual project cards for live `github-readme-stats` repo cards (`?username=KRKR1704&repo=<name>`) for auto-updating stars/forks.
