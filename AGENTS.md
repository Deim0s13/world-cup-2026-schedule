# World Cup 26 Wallchart — Knowledge Base

**Generated:** 2026-06-12  
**Commit:** c9f7ef9  
**Branch:** main

## OVERVIEW

Single-file interactive FIFA World Cup 2026 wallchart. Zero-dependency vanilla HTML/CSS/JS + Python stdlib server. No framework, no build step, no package manager.

## STRUCTURE

```
wc2026/
├── world-cup-2026-schedule_1.html  # THE APP (1500+ lines — CSS + JS inline)
├── server.py                       # Python HTTP server + 3 proxy endpoints
├── download_assets.py              # Asset pre-fetcher (rosters, flags, anthems, photos)
├── README.md
├── assets/
│   ├── silhouettes/                # 4 position SVGs (gk, df, mf, fw)
│   └── teams/{slug}/              # Per-team: roster.json, country.json, anthem.json, flag.svg, anthem.m4a
└── .claude/launch.json
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Change UI / layout / styling | `world-cup-2026-schedule_1.html` lines 10–308 | `<style>` block; CSS custom properties on `:root` |
| Change app logic / filtering | `world-cup-2026-schedule_1.html` lines 368–864 | `<script>` block; all vanilla JS |
| Edit match schedule data | `world-cup-2026-schedule_1.html` lines 409–478 | Array `D` — 104 hardcoded matches |
| Edit venue map | `world-cup-2026-schedule_1.html` lines 372–407 | Object `VENUES` — match# → "City · Stadium" |
| Edit group/stage colors | `world-cup-2026-schedule_1.html` lines 370–371 | `GROUP_COLORS`, `STAGE_COLORS` objects |
| Team name normalization | `world-cup-2026-schedule_1.html` lines 595–605 | `NAME_MAP` — API names → display names |
| Change API proxy | `server.py` lines 17–37 | Proxies `/api/*` to `worldcup26.ir/get/*` via `curl` subprocess |
| Suppress server logs | `server.py` line 39–40 | `log_message` overridden to no-op |
| Dialog CSS | `world-cup-2026-schedule_1.html` style block | `#teamDialog`, `.td-*` classes |
| Pitch CSS | `world-cup-2026-schedule_1.html` style block | `.pitch`, `.player-card`, `.subs-strip` |
| Country profile CSS | `world-cup-2026-schedule_1.html` style block | `.country-profile`, `.cp-*`, `.cp-anthem` |
| TEAM_META mapping | `world-cup-2026-schedule_1.html` first script block | 48-team lookup |
| `showTeamDialog()` | `world-cup-2026-schedule_1.html` second script block | Dialog open/close |
| `loadTeamData()` | `world-cup-2026-schedule_1.html` second script block | Local assets, then live API fallback |
| `renderPitch()` | `world-cup-2026-schedule_1.html` second script block | Formation + player cards |
| `renderCountryProfile()` | `world-cup-2026-schedule_1.html` second script block | Demographics, anthem, lyrics |
| `inferFormation()` | `world-cup-2026-schedule_1.html` second script block | GK/DF/MF/FW ratio to formation |
| Download anthem (Invidious) | `download_assets.py` | `search_invidious_anthem()`, `download_anthem_invidious()` |
| Download roster (Wikipedia) | `download_assets.py` | `parse_wikipedia_squads()` |

## CONVENTIONS

- **Single-file app**: All HTML, CSS, and JS live in one `.html` file. Do not split without discussing.
- **No build step**: Edit → refresh. No transpilation, no bundling.
- **CSS naming**: Flat BEM-ish classes (`.match`, `.m-home`, `.m-score`, `.gc-head`). Not strict BEM.
- **JS naming**: camelCase functions/vars. `$` is a shorthand for `getElementById`.
- **Theming**: CSS custom properties (`--pitch`, `--chalk`, `--gold`, `--line`, etc.). Dark pitch-green palette.
- **Fonts**: Google Fonts CDN — Anton (display), Archivo (body), Space Mono (mono).
- **State**: Plain object `state={stage:"",group:"",q:""}`. Manual `render()` after mutation.
- **Data format**: Match array `D` entries are `[matchNum, stage, group, date, time, home, away]`. Times are IST (UTC+1).
- **Timezone**: All kick-offs stored as Irish Summer Time strings, converted via `Intl.DateTimeFormat`. User pref in localStorage key `wc26tz`.
- **Live data**: Polls `/api/games`, `/api/teams`, `/api/groups` every 2 minutes. Proxied through `server.py`.
- **API proxy**: `server.py` shells out to `curl` (not `urllib`). Requires `curl` on host.
- **Dialog**: HTML `<dialog>` + `showModal()`, built-in focus trap, Escape, backdrop.
- **Team profile data**: local `assets/teams/{slug}/` first, live APIs as fallback.
- **Anthem audio**: m4a format (broadest browser support), sourced via Invidious proxy.
- **Player photos**: TheSportsDB `strCutout` PNG preferred, Wikipedia thumbnail fallback, position silhouette last.
- **Formation**: auto-inferred from GK/DF/MF/FW counts, never hardcoded per team.

## ANTI-PATTERNS

- **Do not add npm/node dependencies** — this is intentionally zero-dependency
- **Do not use TypeScript** — vanilla JS only, no transpilation
- **Do not split CSS/JS into separate files** unless explicitly requested
- **Do not use `python3 -m http.server`** alone — live scores require the proxy in `server.py`
- **Never substitute match data from `D` array with API data** — `D` is the canonical schedule; API provides only live scores/standings
- **Do NOT add a 3rd server.py proxy** — already at limit (worldcup26.ir, TSDB, Invidious)
- **Do NOT hardcode formations** — `inferFormation()` derives from squad data
- **Do NOT commit player photos** — `assets/teams/*/players/` is .gitignored

## DATA FLOW

```
Invidious ($INVIDIOUS_URL)              ←── server.py (/api/invidious/*) ←── download_assets.py
TheSportsDB                            ←── server.py (/api/tsdb/*)        ←── download_assets.py
worldcup26.ir/get/*                    ←── server.py (/api/*)              ←── browser JS
Wikipedia MediaWiki API (CORS) ─────────────────────────────────────────── browser JS (fallback)
GeoAPI.info (CORS) ─────────────────────────────────────────────────────── browser JS (fallback)
assets/teams/{slug}/ ───────────────────────────────────────────────────── browser JS (primary)
```

- `fetchScores()` → `/api/games` → populates `scores` Map → triggers `render()`
- `fetchStandings()` → `/api/teams` + `/api/groups` → populates `groupStandings` Map → triggers `renderGroups()` + `renderStrip()`
- Knockout team names patched via `teamOverrides` Map when API reports real teams

## COMMANDS

```bash
# Run locally (serves on port 8191)
python3 server.py

# Open in browser
open http://localhost:8191/world-cup-2026-schedule_1.html

# Custom port
python3 server.py 9000

# Pre-fetch all team assets (run once, or re-run with --force)
python3 download_assets.py

# Download single team
python3 download_assets.py --team brazil

# Anthems only (re-fetch from Invidious)
python3 download_assets.py --anthems-only --force

# Player photos (slow: ~45 min for 48 teams)
python3 download_assets.py --photos-only
```

## NOTES

- No tests, no CI, no linting configured
- `!important` used twice: `prefers-reduced-motion` override (line 29) and `.loser` color (line 303) — both intentional
- `console.warn` in `fetchScores` and `fetchStandings` catch blocks — only error handling, scores silently degrade
- README documents macOS Plash desktop wallpaper setup with launchd auto-restart
- Anthem audio files (`anthem.m4a`) are ~1-2MB each (48 teams, ~70MB total)
- Player photos are gitignored; run `download_assets.py --photos-only` after clone
- Invidious proxy in server.py uses `$INVIDIOUS_URL` env var (default: `https://invidious.io`)
- Lyrics VTT files (`anthem.*.vtt`) are small (typically 0-10KB); included in git

## GIT REMOTES

| Remote | URL | Purpose |
|--------|-----|---------|
| `upstream` | `https://github.com/Deim0s13/world-cup-2026-schedule.git` | Original project (PR target) |
