# World Cup 26 Wallchart

A single-file interactive wallchart for all 104 matches of the 2026 FIFA World Cup (11 June – 19 July). Filter by group, stage or team, switch timezones, and see live scores update automatically.

**Live version: [wc26-wallchart.duckdns.org](https://wc26-wallchart.duckdns.org/world-cup-2026-schedule_1.html)**

## Features

- All 104 matches with correct IST kick-off times and dates
- Live scores, elapsed time, half-time indicator, and goal scorers via the ESPN scoreboard API — no API key required, polls every 2 minutes; group standings via [worldcup26.ir](https://worldcup26.ir)
- Header banner counts down to the next kick-off; switches to live score during a match; reverts to countdown when the final whistle goes
- Knockout stage team names update automatically once teams qualify — placeholder labels (e.g. "Winner Group A") are replaced with real country names as the API confirms them
- In-play matches show a live score with pulsing indicator and current minute
- Full-time matches show the final score with FT stamp, losing team dimmed, and goal scorers listed under each team name
- Venue (city · stadium) displayed for every match
- Filter by group, stage, or team search
- Timezone conversion — remembers your preference via localStorage
- Late-night kick-off indicator (☾)
- Live group standings (MP, W, D, L, GD, Pts) with flags — visible as a table in the Groups view and as an inline strip above the schedule when a group filter is active; top 2 qualification places highlighted
- Opt-in match alerts — browser notification 15 minutes before each kick-off (requires page to be open)
- Installable as a PWA on iOS, Android, and desktop — add to home screen for a full-screen app experience

## Running locally

All you need is a browser and a way to serve the file over HTTP. A bare `file://` path won't work due to browser fetch restrictions on the scores API.

```bash
python3 server.py
```

Then open `http://localhost:8191/world-cup-2026-schedule_1.html`.

> `server.py` serves static files and proxies `/api/*` requests to the scores API on the server side, bypassing browser CORS restrictions. Using `python3 -m http.server` will serve the page but live scores won't load.

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

## Team profiles

Click any team name, in match cards, group tables, or the standings strip, to open a team profile popup with:

- Squad roster arranged on a CSS football pitch in inferred formation
- Player mugshots with caps, goals, club, age on hover
- Country demographics (population, capital, languages, government)
- National anthem with audio player and collapsible lyrics/subtitles
- Link to the FIFA team page

## Asset management

Team data (rosters, country info, flags, anthems) is pre-cached in `assets/teams/`. Download before first use:

```bash
python3 download_assets.py          # all 48 teams
python3 download_assets.py --team mexico   # single team
python3 download_assets.py --force         # re-download existing
python3 download_assets.py --dry-run       # preview without writing
python3 download_assets.py --anthems-only  # anthems only
python3 download_assets.py --photos-only   # player photos only
```

Anthem audio is sourced from YouTube via an Invidious proxy. Set the `INVIDIOUS_URL` environment variable to point to your Invidious instance. Player photos from TheSportsDB with Wikipedia fallback; players without photos show a position-coloured silhouette.

The app falls back to live APIs (Wikipedia, GeoAPI.info, Wikidata) if local assets are missing.

## Data sources

| Data | Source |
|------|--------|
| Match schedule & times | Verified against Sky Sports BST kick-off times |
| Live scores, elapsed time & goal scorers | ESPN unofficial scoreboard API (no key, ~9s refresh) |
| Group standings & team flags | [worldcup26.ir](https://worldcup26.ir) (free, no key) |
| Venues | worldcup26.ir stadiums endpoint |
