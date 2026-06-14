# World Cup 26 Wallchart

A single-file interactive wallchart for all 104 matches of the 2026 FIFA World Cup (11 June – 19 July). Filter by group, stage, team or date; switch timezones; watch live scores, lineups and substitutions update automatically; and click any played match for full post-match stats.

**Live version: [wc26-wallchart.duckdns.org](https://wc26-wallchart.duckdns.org/world-cup-2026-schedule_1.html)**

## Features

- All 104 matches with correct kick-off times and dates
- Live scores, elapsed time, half-time indicator, and goal scorers via the ESPN scoreboard API — no API key required, polls every 2 minutes
- Header banner counts down to the next kick-off; switches to live score during a match; reverts to countdown when the final whistle goes. When several matches are live at once, it shows them side by side
- During a live match, the banner expands to show both **starting XIs and formations**, with **substitutions** appearing as they happen and subbed-off players struck through (via the ESPN match summary)
- **Click any finished or in-play match to expand a post-match detail panel** — a team-stat comparison (possession, shots, shots on target, corners, fouls, offsides, cards, passes, saves) shown as two-tone bars, plus a full event timeline of goals, cards, and substitutions
- Knockout stage team names update automatically once teams qualify — placeholder labels (e.g. "Winner Group A") are replaced with real country names as the API confirms them
- In-play matches show a live score with pulsing indicator and current minute
- Full-time matches show the final score with FT stamp, losing team dimmed, and goal scorers (surname + minute) listed under each team name — the list wraps so even high-scoring games show every scorer
- Venue (city · stadium) displayed for every match
- Filter by group, stage, team search, or **match day** (date selector listing every day with fixtures, timezone-aware)
- Timezone conversion — remembers your preference via localStorage
- Late-night kick-off indicator (☾)
- Group standings computed live from match results (MP, W, D, L, GD, Pts) with flags — visible as a table in the Groups view and as an inline strip above the schedule when a group filter is active; top 2 qualification places highlighted
- **Best third-placed teams table** at the bottom of the Groups view — ranks all 12 third-placed teams across groups (the 8 best advance to the Round of 32), with the qualifying top 8 highlighted and a cut line marking the boundary; updates live as group games finish
- Opt-in match alerts — browser notification 15 minutes before each kick-off (requires page to be open; desktop and installed-PWA only, and automatically hidden where the browser doesn't expose notifications, e.g. mobile Safari)
- Installable as a PWA on iOS, Android, and desktop — add to home screen for a full-screen app experience

## Running locally

All you need is a browser and a way to serve the file over HTTP. A bare `file://` path won't work due to browser fetch restrictions on the scores API.

```bash
python3 server.py
```

Then open `http://localhost:8191/world-cup-2026-schedule_1.html`.

> `server.py` serves static files and proxies the upstream APIs server-side, bypassing browser CORS restrictions (and slimming the large match-summary payload down before it reaches the browser). Using `python3 -m http.server` will serve the page but live scores won't load. The proxy routes are:
>
> | Route | Upstream | Purpose |
> |-------|----------|---------|
> | `/scores` | ESPN scoreboard | Live & final scores, elapsed time, goal scorers |
> | `/flags` | worldcup26.ir | Team flags for the standings tables |
> | `/lineup?event=ID` | ESPN match summary | Starting XIs, formations, substitutions (slimmed to ~3 KB) |
> | `/matchdata?event=ID` | ESPN match summary | Post-match team stats + event timeline (slimmed to ~3 KB) |

## Running as an interactive desktop wallpaper (macOS)

This setup uses [Plash](https://apps.apple.com/app/plash/id1494023538) to render the wallchart as a live, interactive macOS wallpaper that survives reboots and sleep.

### 1. Serve the file on login

Create a launchd agent so the HTTP server starts automatically and restarts if it ever dies:

```bash
cat > ~/Library/LaunchAgents/dev.YOUR_USERNAME.wallchart-server.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>dev.YOUR_USERNAME.wallchart-server</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/python3</string>
    <string>/Users/YOUR_USERNAME/PATH/TO/fifa-wc-2026-wallpaper/server.py</string>
    <string>8191</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>StandardOutPath</key>
  <string>/tmp/wallchart-server.log</string>
  <key>StandardErrorPath</key>
  <string>/tmp/wallchart-server.log</string>
</dict>
</plist>
EOF

launchctl load ~/Library/LaunchAgents/dev.YOUR_USERNAME.wallchart-server.plist
```

Replace `YOUR_USERNAME` with your macOS username and `PATH/TO` with the path to the folder. The agent loads at login and restarts automatically if the process exits.

### 2. Configure Plash

1. Install Plash from the [Mac App Store](https://apps.apple.com/app/plash/id1494023538)
2. Click the Plash menu bar icon → **Add Website…**
3. Enter `http://localhost:8191/world-cup-2026-schedule_1.html`
4. Click the Plash menu bar icon → **Browsing Mode** to bring the wallchart to the front and interact with it (filters, search, scroll). Toggle it off to send it back behind your windows
5. Click the Plash menu bar icon → **⋯** → **Settings…** → enable **Launch at Login**

### 3. Blend the edges (optional)

Set your macOS wallpaper to a solid `#0c1713` so the page background matches seamlessly.

### Stopping the server

```bash
launchctl unload ~/Library/LaunchAgents/dev.YOUR_USERNAME.wallchart-server.plist
```

## Data sources

| Data | Source |
|------|--------|
| Match schedule & times | Verified against Sky Sports kick-off times |
| Live scores, elapsed time & goal scorers | ESPN unofficial scoreboard API (no key, ~9s refresh) |
| Lineups, formations, substitutions, post-match stats & timeline | ESPN unofficial match-summary API (no key) |
| Group standings | Computed in-browser from finished ESPN results (no external standings API) |
| Team flags | [worldcup26.ir](https://worldcup26.ir) (free, no key) |
| Venues | Built-in lookup table in the page |
