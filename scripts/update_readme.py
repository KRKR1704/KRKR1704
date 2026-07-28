#!/usr/bin/env python3
"""Regenerate the Featured Projects block in README.md from GitHub's live pinned repos.

Queries the GitHub GraphQL API for KRKR1704's pinnedItems (the same 6 repos shown
under "Customize your pins" on the profile page) and rewrites everything between
the <!--PROJECTS:START--> / <!--PROJECTS:END--> markers in README.md. Nothing
outside those markers is touched, and README.md is left completely untouched if
the query fails for any reason (see main()).

Run with --dry-run to write the result to README.preview.md instead of overwriting
README.md, so you can inspect/diff it first: `python scripts/update_readme.py --dry-run`.

profile.overrides.json is optional and only covers what the API can't know: a
per-repo note, or a description override for a repo with an empty/misleading
GitHub description. A repo with no entry there renders from raw API data alone.

Zero third-party dependencies — stdlib only (urllib), so it runs anywhere Python 3
runs with no `pip install` step. Unlike the REST API, GitHub's GraphQL API requires
an authenticated request even for public data — GH_TOKEN (or GITHUB_TOKEN) MUST be
set, or this exits immediately with an explanation instead of guessing.
"""
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request

README_PATH = "README.md"
PREVIEW_PATH = "README.preview.md"
OVERRIDES_PATH = "profile.overrides.json"
START_MARKER = "<!--PROJECTS:START-->"
END_MARKER = "<!--PROJECTS:END-->"
GRAPHQL_URL = "https://api.github.com/graphql"
GITHUB_LOGIN = "KRKR1704"
ACCENT = "39FF14"

# Maps a topic/language name (lowercased) to a simple-icons slug for shields.io.
# Anything not listed here still renders as a plain text badge with no logo.
LOGO_MAP = {
    "python": "python",
    "typescript": "typescript",
    "javascript": "javascript",
    "nextjs": "nextdotjs",
    "next.js": "nextdotjs",
    "fastapi": "fastapi",
    "electron": "electron",
    "react": "react",
    "nodejs": "nodedotjs",
    "node.js": "nodedotjs",
    "docker": "docker",
    "ollama": "ollama",
    "tailwindcss": "tailwindcss",
    "html": "html5",
    "css": "css3",
    "c++": "cplusplus",
    "sql": "postgresql",
    "postgresql": "postgresql",
    "mongodb": "mongodb",
    "openai": "openai",
    "anthropic": "anthropic",
    "claude": "anthropic",
}

PINNED_ITEMS_QUERY = """
query($login: String!) {
  user(login: $login) {
    pinnedItems(first: 6, types: [REPOSITORY]) {
      totalCount
      nodes {
        __typename
        ... on Repository {
          name
          owner { login }
          description
          url
          homepageUrl
          isPrivate
          stargazerCount
          pushedAt
          repositoryTopics(first: 10) {
            nodes { topic { name } }
          }
          languages(first: 6, orderBy: {field: SIZE, direction: DESC}) {
            edges { size node { name } }
          }
        }
      }
    }
  }
}
""".strip()


class GraphQLError(RuntimeError):
    pass


def fetch_pinned_items(token):
    body = json.dumps({"query": PINNED_ITEMS_QUERY, "variables": {"login": GITHUB_LOGIN}}).encode("utf-8")
    req = urllib.request.Request(GRAPHQL_URL, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "profile-readme-bot")
    req.add_header("Authorization", f"Bearer {token}")

    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise GraphQLError(f"HTTP {e.code} from GitHub GraphQL API: {detail}") from e
    except urllib.error.URLError as e:
        raise GraphQLError(f"network error calling GitHub GraphQL API: {e}") from e

    if payload.get("errors"):
        raise GraphQLError(f"GraphQL API returned errors: {payload['errors']}")

    user = (payload.get("data") or {}).get("user")
    if user is None:
        raise GraphQLError(
            f"query returned no user for login {GITHUB_LOGIN!r} — the token may lack "
            "the 'read:user' scope, or be malformed/expired."
        )

    pinned = user.get("pinnedItems") or {}
    total = pinned.get("totalCount", 0)
    nodes = [n for n in (pinned.get("nodes") or []) if n and n.get("__typename") == "Repository"]

    if total > len(nodes):
        print(
            f"WARNING: GitHub reports {total} pinned item(s) but only {len(nodes)} repository "
            "node(s) were returned. This usually means some pinned items are private and the "
            "token can't see them, or a pinned item is a Gist (only Repository pins are rendered). "
            "Continuing with what was returned.",
            file=sys.stderr,
        )

    return nodes


def load_overrides():
    if not os.path.exists(OVERRIDES_PATH):
        return {}
    with open(OVERRIDES_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("overrides", {})


def badge(label, logo=None):
    label_enc = str(label).replace(" ", "%20").replace("+", "%2B")
    logo_part = f"&logo={logo}" if logo else ""
    return (
        f'<img src="https://img.shields.io/badge/-{label_enc}-000000'
        f'?style=flat-square{logo_part}&logoColor={ACCENT}" />'
    )


def build_badges(topics, languages_by_bytes):
    """Prefer GitHub topics (repo owner controls these directly, no code change
    needed). Fall back to the real byte-weighted language breakdown."""
    if topics:
        labels = topics[:5]
    elif languages_by_bytes:
        ranked = sorted(languages_by_bytes.items(), key=lambda kv: -kv[1])
        labels = [name for name, _ in ranked[:4]]
    else:
        labels = []
    return "\n".join(badge(l, LOGO_MAP.get(l.lower())) for l in labels)


def render_card(repo_node, override):
    owner = repo_node["owner"]["login"]
    repo = repo_node["name"]
    full = f"{owner}/{repo}"

    note = (override.get("note") or "").strip()
    note_html = f"<br/><i>{note}</i>" if note else ""

    desc = (override.get("description_override") or "").strip() or repo_node.get("description") or (
        "_No description set on GitHub yet._"
    )

    topics = [t["topic"]["name"] for t in (repo_node.get("repositoryTopics") or {}).get("nodes", [])]
    lang_edges = (repo_node.get("languages") or {}).get("edges", [])
    languages = {e["node"]["name"]: e["size"] for e in lang_edges}
    stars = repo_node.get("stargazerCount", 0)
    pushed = (repo_node.get("pushedAt") or "")[:10]
    html_url = repo_node.get("url", f"https://github.com/{full}")
    homepage = (repo_node.get("homepageUrl") or "").strip()
    is_private = bool(repo_node.get("isPrivate"))

    badges = build_badges(topics, languages)
    link_line = f"**[{full}]({html_url})**"
    if homepage:
        label = homepage.replace("https://", "").replace("http://", "").rstrip("/")
        link_line += f" · **[{label}]({homepage})**"
    star_suffix = f" · ⭐ {stars}" if stars else ""
    private_suffix = " · 🔒 private" if is_private else ""

    return (
        f"### \U0001F4E6 {repo}\n"
        f"{desc}{note_html}\n\n"
        f"{badges}\n\n"
        f"{link_line}{star_suffix}{private_suffix}\n"
        f"<br/><sub>last pushed {pushed}</sub>"
    )


def build_table(cards):
    rows = []
    i = 0
    while i < len(cards):
        if i + 1 < len(cards):
            rows.append(
                '<tr>\n<td width="50%" valign="top">\n\n'
                f"{cards[i]}\n\n</td>\n"
                '<td width="50%" valign="top">\n\n'
                f"{cards[i + 1]}\n\n</td>\n</tr>"
            )
            i += 2
        else:
            rows.append(
                '<tr>\n<td width="100%" valign="top" colspan="2">\n\n'
                f"{cards[i]}\n\n</td>\n</tr>"
            )
            i += 1
    return '<table width="100%">\n' + "\n".join(rows) + "\n</table>"


PAT_HELP = (
    "To fix this, create a classic Personal Access Token at "
    "https://github.com/settings/tokens (Generate new token -> classic) with the "
    "'read:user' scope — that's enough to read public pinned-repo data. If you pin "
    "any PRIVATE repo and want its real data instead of it being dropped from the "
    "results, also add the 'repo' scope. Then add it as a repository secret named "
    "PROFILE_PAT under Settings -> Secrets and variables -> Actions in "
    "KRKR1704/KRKR1704. The workflow already prefers PROFILE_PAT over the default "
    "GITHUB_TOKEN, so no further changes are needed once the secret exists."
)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Regenerate the Featured Projects block in README.md from live GitHub pinned repos."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            f"Write the result to {PREVIEW_PATH} instead of overwriting {README_PATH}. "
            f"{README_PATH} is read (as the template) but never modified in this mode. "
            f"Diff the two yourself before deciding to run without --dry-run."
        ),
    )
    return parser.parse_args()


def main():
    args = parse_args()
    output_path = PREVIEW_PATH if args.dry_run else README_PATH

    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        print(
            "ERROR: no GitHub token available (GH_TOKEN / GITHUB_TOKEN unset). "
            f"Unlike the REST API, GitHub's GraphQL API requires authentication for "
            f"every request, even to read public data. {README_PATH} was left untouched.",
            file=sys.stderr,
        )
        print(PAT_HELP, file=sys.stderr)
        sys.exit(1)

    try:
        nodes = fetch_pinned_items(token)
    except GraphQLError as e:
        print(f"ERROR: could not fetch pinned repositories for {GITHUB_LOGIN} — {e}", file=sys.stderr)
        print(f"{README_PATH} was left untouched.", file=sys.stderr)
        print(PAT_HELP, file=sys.stderr)
        sys.exit(1)

    if not nodes:
        print(
            f"ERROR: {GITHUB_LOGIN} has no pinned repositories (or none were visible to this "
            "token). Pin at least one repo at https://github.com/KRKR1704?tab=repositories -> "
            f"'Customize your pins'. {README_PATH} was left untouched.",
            file=sys.stderr,
        )
        sys.exit(1)

    overrides = load_overrides()

    cards = []
    for node in nodes:
        full = f"{node['owner']['login']}/{node['name']}"
        cards.append(render_card(node, overrides.get(full, {})))

    generated = build_table(cards)

    with open(README_PATH, encoding="utf-8") as f:
        readme = f.read()

    pattern = re.compile(re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER), re.DOTALL)
    if not pattern.search(readme):
        print(f"ERROR: {START_MARKER} / {END_MARKER} markers not found in {README_PATH}", file=sys.stderr)
        sys.exit(1)

    replacement = (
        f"{START_MARKER}\n"
        "<!-- This block is auto-generated by scripts/update_readme.py from KRKR1704's "
        "live pinned repos (GitHub GraphQL pinnedItems), with optional overrides from "
        "profile.overrides.json. Do not hand-edit — your changes will be overwritten on "
        "the next run. -->\n\n"
        f"{generated}\n\n"
        f"{END_MARKER}"
    )
    new_readme = pattern.sub(lambda _m: replacement, readme)

    with open(output_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(new_readme)

    if args.dry_run:
        print(
            f"DRY RUN: wrote preview to {output_path} — {README_PATH} was NOT modified. "
            f"Regenerated {len(cards)} pinned project card(s) from {GITHUB_LOGIN}'s live pinned repos.\n"
            f"Diff it yourself with: git diff --no-index {README_PATH} {output_path}"
        )
    else:
        print(f"Regenerated {len(cards)} pinned project card(s) from {GITHUB_LOGIN}'s live pinned repos.")


if __name__ == "__main__":
    main()
