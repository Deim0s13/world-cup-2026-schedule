#!/usr/bin/env python3
"""
download_assets.py — Pre-cache team data from Wikipedia for WC2026 wallchart.
Usage: python3 download_assets.py [--team SLUG] [--dry-run] [--force] [--enrich]
"""
import urllib.request
import urllib.parse
import json
import os
import re
import time
import sys
import argparse

WORKDIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(WORKDIR, "assets")
UA = "wc2026-wallchart/1.0 (https://github.com/Deim0s13/world-cup-2026-schedule)"
INVIDIOUS_BASE = os.environ.get("INVIDIOUS_URL", "https://invidious.io")

ANTHEM_NAMES = {
    "algeria": "Kassaman", "argentina": "Himno Nacional Argentino",
    "australia": "Advance Australia Fair", "austria": "Bundeshymne",
    "belgium": "La Brabançonne", "bosnia-and-herzegovina": "Intermeco",
    "brazil": "Hino Nacional Brasileiro", "cabo-verde": "Cântico da Liberdade",
    "canada": "O Canada", "colombia": "Himno Nacional de Colombia",
    "congo-dr": "Debout Congolais", "cote-d-ivoire": "L'Abidjanaise",
    "croatia": "Lijepa naša domovino", "curacao": "Himno di Kòrsou",
    "czechia": "Kde domov můj", "ecuador": "Salve, Oh Patria",
    "egypt": "Bilady, Bilady, Bilady", "england": "God Save the King",
    "france": "La Marseillaise", "germany": "Das Lied der Deutschen",
    "ghana": "God Bless Our Homeland Ghana", "haiti": "La Dessalinienne",
    "ir-iran": "Soroud-e Melli-e Jomhouri-e Eslami-e Iran",
    "iraq": "Mawtini", "japan": "Kimigayo",
    "jordan": "As-salam al-malaki al-urdoni", "korea-republic": "Aegukga",
    "mexico": "Himno Nacional Mexicano", "morocco": "Hymne Chérifien",
    "netherlands": "Het Wilhelmus", "new-zealand": "God Defend New Zealand",
    "norway": "Ja, vi elsker dette landet", "panama": "Himno Istmeño",
    "paraguay": "Himno Nacional del Paraguay", "portugal": "A Portuguesa",
    "qatar": "As-Salam al-Amiri", "saudi-arabia": "Aash Al Maleek",
    "scotland": "Flower of Scotland", "senegal": "Pincez Tous vos Koras, Frappez les Balafons",
    "south-africa": "Nkosi Sikelel' iAfrika", "spain": "Marcha Real",
    "sweden": "Du gamla, du fria", "switzerland": "Schweizer Psalm",
    "tunisia": "Humat al-Hima", "turkiye": "İstiklal Marşı",
    "uruguay": "Himno Nacional de Uruguay", "usa": "The Star-Spangled Banner",
    "uzbekistan": "O'zbekiston Respublikasining Davlat Madhiyasi",
}

# All 48 teams: display_name → {slug, iso2, flagcdn, qid}
TEAMS = {
    "Algeria":              {"slug": "algeria",                "iso2": "dz", "flagcdn": "dz",     "qid": "Q262"},
    "Argentina":            {"slug": "argentina",              "iso2": "ar", "flagcdn": "ar",     "qid": "Q414"},
    "Australia":            {"slug": "australia",              "iso2": "au", "flagcdn": "au",     "qid": "Q408"},
    "Austria":              {"slug": "austria",                "iso2": "at", "flagcdn": "at",     "qid": "Q40"},
    "Belgium":              {"slug": "belgium",                "iso2": "be", "flagcdn": "be",     "qid": "Q31"},
    "Bosnia & Herzegovina": {"slug": "bosnia-and-herzegovina", "iso2": "ba", "flagcdn": "ba",     "qid": "Q225"},
    "Brazil":               {"slug": "brazil",                 "iso2": "br", "flagcdn": "br",     "qid": "Q155"},
    "Cabo Verde":           {"slug": "cabo-verde",             "iso2": "cv", "flagcdn": "cv",     "qid": "Q1011"},
    "Canada":               {"slug": "canada",                 "iso2": "ca", "flagcdn": "ca",     "qid": "Q16"},
    "Colombia":             {"slug": "colombia",               "iso2": "co", "flagcdn": "co",     "qid": "Q739"},
    "Congo DR":             {"slug": "congo-dr",               "iso2": "cd", "flagcdn": "cd",     "qid": "Q974"},
    "Côte d'Ivoire":        {"slug": "cote-d-ivoire",          "iso2": "ci", "flagcdn": "ci",     "qid": "Q1008"},
    "Croatia":              {"slug": "croatia",                "iso2": "hr", "flagcdn": "hr",     "qid": "Q224"},
    "Curaçao":              {"slug": "curacao",                "iso2": "cw", "flagcdn": "cw",     "qid": "Q25279"},
    "Czechia":              {"slug": "czechia",                "iso2": "cz", "flagcdn": "cz",     "qid": "Q213"},
    "Ecuador":              {"slug": "ecuador",                "iso2": "ec", "flagcdn": "ec",     "qid": "Q736"},
    "Egypt":                {"slug": "egypt",                  "iso2": "eg", "flagcdn": "eg",     "qid": "Q79"},
    "England":              {"slug": "england",                "iso2": "gb", "flagcdn": "gb-eng", "qid": "Q145"},
    "France":               {"slug": "france",                 "iso2": "fr", "flagcdn": "fr",     "qid": "Q142"},
    "Germany":              {"slug": "germany",                "iso2": "de", "flagcdn": "de",     "qid": "Q183"},
    "Ghana":                {"slug": "ghana",                  "iso2": "gh", "flagcdn": "gh",     "qid": "Q117"},
    "Haiti":                {"slug": "haiti",                  "iso2": "ht", "flagcdn": "ht",     "qid": "Q790"},
    "IR Iran":              {"slug": "ir-iran",                "iso2": "ir", "flagcdn": "ir",     "qid": "Q794"},
    "Iraq":                 {"slug": "iraq",                   "iso2": "iq", "flagcdn": "iq",     "qid": "Q796"},
    "Japan":                {"slug": "japan",                  "iso2": "jp", "flagcdn": "jp",     "qid": "Q17"},
    "Jordan":               {"slug": "jordan",                 "iso2": "jo", "flagcdn": "jo",     "qid": "Q810"},
    "Korea Republic":       {"slug": "korea-republic",         "iso2": "kr", "flagcdn": "kr",     "qid": "Q884"},
    "Mexico":               {"slug": "mexico",                 "iso2": "mx", "flagcdn": "mx",     "qid": "Q96"},
    "Morocco":              {"slug": "morocco",                "iso2": "ma", "flagcdn": "ma",     "qid": "Q1028"},
    "Netherlands":          {"slug": "netherlands",            "iso2": "nl", "flagcdn": "nl",     "qid": "Q55"},
    "New Zealand":          {"slug": "new-zealand",            "iso2": "nz", "flagcdn": "nz",     "qid": "Q664"},
    "Norway":               {"slug": "norway",                 "iso2": "no", "flagcdn": "no",     "qid": "Q20"},
    "Panama":               {"slug": "panama",                 "iso2": "pa", "flagcdn": "pa",     "qid": "Q804"},
    "Paraguay":             {"slug": "paraguay",               "iso2": "py", "flagcdn": "py",     "qid": "Q733"},
    "Portugal":             {"slug": "portugal",               "iso2": "pt", "flagcdn": "pt",     "qid": "Q45"},
    "Qatar":                {"slug": "qatar",                  "iso2": "qa", "flagcdn": "qa",     "qid": "Q846"},
    "Saudi Arabia":         {"slug": "saudi-arabia",           "iso2": "sa", "flagcdn": "sa",     "qid": "Q851"},
    "Scotland":             {"slug": "scotland",               "iso2": "gb", "flagcdn": "gb-sct", "qid": "Q22"},
    "Senegal":              {"slug": "senegal",                "iso2": "sn", "flagcdn": "sn",     "qid": "Q1041"},
    "South Africa":         {"slug": "south-africa",           "iso2": "za", "flagcdn": "za",     "qid": "Q258"},
    "Spain":                {"slug": "spain",                  "iso2": "es", "flagcdn": "es",     "qid": "Q29"},
    "Sweden":               {"slug": "sweden",                 "iso2": "se", "flagcdn": "se",     "qid": "Q34"},
    "Switzerland":          {"slug": "switzerland",            "iso2": "ch", "flagcdn": "ch",     "qid": "Q39"},
    "Tunisia":              {"slug": "tunisia",                "iso2": "tn", "flagcdn": "tn",     "qid": "Q948"},
    "Türkiye":              {"slug": "turkiye",                "iso2": "tr", "flagcdn": "tr",     "qid": "Q43"},
    "Uruguay":              {"slug": "uruguay",                "iso2": "uy", "flagcdn": "uy",     "qid": "Q77"},
    "USA":                  {"slug": "usa",                    "iso2": "us", "flagcdn": "us",     "qid": "Q30"},
    "Uzbekistan":           {"slug": "uzbekistan",             "iso2": "uz", "flagcdn": "uz",     "qid": "Q265"},
}

TEAMS_BY_SLUG = {v["slug"]: k for k, v in TEAMS.items()}

# Wikipedia section names → our display names (where they differ)
WIKI_NAME_MAP = {
    "Czech Republic": "Czechia",
    "South Korea": "Korea Republic",
    "Bosnia and Herzegovina": "Bosnia & Herzegovina",
    "Turkey": "Türkiye",
    "United States": "USA",
    "Ivory Coast": "Côte d'Ivoire",
    "Iran": "IR Iran",
    "Cape Verde": "Cabo Verde",
    "DR Congo": "Congo DR",
}


def fetch_url(url, retries=3, delay=2):
    """Fetch URL with retries and User-Agent. Returns bytes."""
    req = urllib.request.Request(
        url, headers={"User-Agent": UA, "Accept": "application/json"}
    )
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return r.read()
        except Exception as e:
            if attempt < retries - 1:
                wait = delay * (2 ** attempt)
                print(f"  Retry {attempt+1}/{retries} after {wait}s: {e}")
                time.sleep(wait)
            else:
                raise


def strip_wiki(text):
    """Strip [[link|display]] → display, or [[link]] → link. Remove templates."""
    text = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"\{\{[^}]*\}\}", "", text)
    return text.strip()


def parse_player_template(line):
    """Parse a single {{nat fs g player|...}} template line into a player dict.

    Fields are extracted by name so order doesn't matter.
    Handles nested {{birth date and age2|...}} template inside age= field.
    """
    # Extract key=value pairs, handling nested {{ }} in age field
    def extract_field(text, field):
        pattern = re.compile(
            r"\|" + re.escape(field) + r"=(.*?)(?=\|(?:\w+=)|$)", re.DOTALL
        )
        m = pattern.search(text)
        return m.group(1).strip() if m else None

    # Flatten the template: remove outer {{ and }}
    # Handle nested braces by finding the full template span
    no = extract_field(line, "no")
    pos = extract_field(line, "pos")
    name_raw = extract_field(line, "name")
    other = extract_field(line, "other") or ""
    caps = extract_field(line, "caps")
    goals = extract_field(line, "goals")
    club_raw = extract_field(line, "club")
    clubnat = extract_field(line, "clubnat")

    if not all([no, pos, name_raw, caps is not None, goals is not None]):
        return None

    # Parse DOB from age={{birth date and age2|YYYY|M|D|YYYY|M|D}}
    dob_match = re.search(
        r"birth date and age2\|(\d{4})\|(\d+)\|(\d+)\|(\d{4})\|(\d+)\|(\d+)",
        line,
    )
    if not dob_match:
        return None

    # Tournament date params are groups 1-3, birth date is groups 4-6
    dob_year = int(dob_match.group(4))
    dob_month = int(dob_match.group(5))
    dob_day = int(dob_match.group(6))
    dob = f"{dob_year}-{dob_month:02d}-{dob_day:02d}"

    # Age at tournament start (2026-06-11)
    age = 2026 - dob_year
    if (dob_month, dob_day) > (6, 11):
        age -= 1

    is_captain = "captain" in other.lower()

    return {
        "number": int(no),
        "position": pos,
        "name": strip_wiki(name_raw),
        "dob": dob,
        "age": age,
        "caps": int(caps),
        "goals": int(goals),
        "club": strip_wiki(club_raw) if club_raw else "",
        "club_nation": clubnat.strip().rstrip("}") if clubnat else "",
        "captain": is_captain,
        "photo": None,
    }


def parse_wikipedia_squads():
    """Fetch and parse 2026 FIFA World Cup squads from Wikipedia."""
    url = (
        "https://en.wikipedia.org/w/api.php?action=parse"
        "&page=2026_FIFA_World_Cup_squads&prop=wikitext&format=json"
    )
    print("Fetching Wikipedia squad data...")
    data = json.loads(fetch_url(url))
    wikitext = data["parse"]["wikitext"]["*"]

    # Split on === TeamName === sections
    sections = re.split(r"\n===\s*(.+?)\s*===\n", wikitext)

    squads = {}
    for i in range(1, len(sections), 2):
        wiki_name = sections[i].strip()
        section_text = sections[i + 1] if i + 1 < len(sections) else ""

        # Map Wikipedia name to our display name
        display_name = WIKI_NAME_MAP.get(wiki_name, wiki_name)
        meta = TEAMS.get(display_name)

        if not meta:
            for dn, m in TEAMS.items():
                if dn.lower() == display_name.lower():
                    meta = m
                    display_name = dn
                    break

        if not meta:
            continue

        players = []
        for line in section_text.split("\n"):
            if "nat fs g player" not in line:
                continue
            player = parse_player_template(line)
            if player:
                players.append(player)

        if players:
            slug = meta["slug"]
            squads[slug] = {
                "team": display_name,
                "slug": slug,
                "players": players,
            }

    return squads


# GeoAPI returns wrong data for GB (Northern Ireland) — override for UK home nations
COUNTRY_OVERRIDES = {
    "england": {
        "name": "England", "capital": "London", "population": 56_000_000,
        "area": 130_279, "region": "Europe", "subregion": "Northern Europe",
        "languages": ["English"], "currency": "British pound (GBP)",
        "governmentType": "Constitutional monarchy (devolved)",
        "religion": "Christianity", "nationalDish": "Chicken tikka masala",
        "drivingSide": "left", "lifeExpectancy": 81.3,
    },
    "scotland": {
        "name": "Scotland", "capital": "Edinburgh", "population": 5_500_000,
        "area": 77_933, "region": "Europe", "subregion": "Northern Europe",
        "languages": ["English", "Scottish Gaelic"],
        "currency": "British pound (GBP)",
        "governmentType": "Devolved parliamentary democracy",
        "religion": "Christianity", "nationalDish": "Haggis",
        "drivingSide": "left", "lifeExpectancy": 79.1,
    },
}


def download_country_data(slug, iso2, dry_run=False, force=False):
    """Download country demographics from GeoAPI.info, save as country.json."""
    out_path = os.path.join(ASSETS_DIR, "teams", slug, "country.json")
    if not force and os.path.exists(out_path):
        print(f"  Skip country (exists)")
        return

    if slug in COUNTRY_OVERRIDES:
        data = COUNTRY_OVERRIDES[slug]
        print(f"  Country: hardcoded override for {slug}")
    else:
        url = f"https://geoapi.info/api/country?code={iso2.upper()}"
        try:
            raw = fetch_url(url)
            api_data = json.loads(raw)
            data = {
                "name": api_data.get("name", ""),
                "capital": api_data.get("capitalCity", ""),
                "population": api_data.get("population", 0),
                "area": api_data.get("surfaceArea", 0),
                "region": api_data.get("continent", ""),
                "languages": api_data.get("languages", []),
                "currency": api_data.get("currencyName", "") + f" ({api_data.get('currencyCode', '')})",
                "governmentType": api_data.get("governmentType", ""),
                "religion": api_data.get("religion", ""),
                "nationalDish": api_data.get("nationalDish", ""),
                "drivingSide": api_data.get("drivingSide", ""),
                "lifeExpectancy": api_data.get("lifeExpectancy", 0),
            }
            print(f"  Country: {data['name']}, capital: {data['capital']}")
        except Exception as e:
            print(f"  Country fetch failed: {e}")
            data = {"name": slug, "error": str(e)}

    if not dry_run:
        with open(out_path, "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    time.sleep(0.5)


def download_flag(slug, flagcdn_code, dry_run=False, force=False):
    """Download flag SVG from flagcdn.com."""
    out_path = os.path.join(ASSETS_DIR, "teams", slug, "flag.svg")
    if not force and os.path.exists(out_path):
        print(f"  Skip flag (exists)")
        return
    url = f"https://flagcdn.com/{flagcdn_code.lower()}.svg"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=10) as r:
            content = r.read()
        if not dry_run:
            with open(out_path, "wb") as f:
                f.write(content)
        print(f"  Flag: {flagcdn_code}.svg ({len(content)} bytes)")
    except Exception as e:
        print(f"  Flag failed for {flagcdn_code}: {e}")


def search_invidious_anthem(display_name):
    """Search Invidious for a national anthem video. Returns best videoId or None."""
    query = f"{display_name} national anthem"
    url = (f"{INVIDIOUS_BASE}/api/v1/search"
           f"?q={urllib.parse.quote(query)}"
           f"&type=video"
           f"&fields=videoId,title,hasCaptions,lengthSeconds,viewCount"
           f"&sort_by=relevance")
    try:
        raw = fetch_url(url)
        results = json.loads(raw)
        if not isinstance(results, list):
            return None

        # Filter: reasonable anthem duration (45s-300s), not a concert/match recording
        candidates = []
        for v in results:
            dur = v.get("lengthSeconds", 0)
            title = v.get("title", "").lower()
            if dur < 45 or dur > 300:
                continue
            score = 0
            if "anthem" in title or "hymn" in title or "himno" in title or "hymne" in title:
                score += 10
            if v.get("hasCaptions"):
                score += 5
            if "official" in title or "world cup" in title:
                score += 3
            score += min(v.get("viewCount", 0) // 100000, 10)
            candidates.append((score, v))

        if not candidates:
            for v in results:
                if 45 <= v.get("lengthSeconds", 0) <= 300:
                    return v["videoId"]
            return None

        best = max(candidates, key=lambda x: x[0])
        return best[1]["videoId"]
    except Exception as e:
        print(f"  Invidious search failed: {e}")
        return None


def download_anthem_invidious(slug, anthem_name, display_name, dry_run=False, force=False):
    """Download national anthem audio + captions from Invidious/YouTube."""
    json_path = os.path.join(ASSETS_DIR, "teams", slug, "anthem.json")
    audio_path = os.path.join(ASSETS_DIR, "teams", slug, "anthem.m4a")

    if not force and os.path.exists(json_path) and os.path.exists(audio_path):
        print(f"  Skip anthem (exists)")
        return

    anthem_data = {
        "name": anthem_name,
        "video_id": None,
        "video_title": None,
        "audio_file": None,
        "has_audio": False,
        "captions": [],
    }

    # Step 1: Find the best video
    video_id = search_invidious_anthem(display_name)
    if not video_id:
        print(f"  Anthem: no suitable video found for {display_name}")
        if not dry_run:
            with open(json_path, "w") as f:
                json.dump(anthem_data, f, indent=2)
        return

    # Step 2: Get video metadata (audio formats + captions)
    try:
        meta_url = f"{INVIDIOUS_BASE}/api/v1/videos/{video_id}?fields=title,adaptiveFormats,captions"
        meta_raw = fetch_url(meta_url)
        meta = json.loads(meta_raw)
    except Exception as e:
        print(f"  Anthem metadata fetch failed: {e}")
        if not dry_run:
            with open(json_path, "w") as f:
                json.dump(anthem_data, f, indent=2)
        return

    anthem_data["video_id"] = video_id
    anthem_data["video_title"] = meta.get("title", "")
    print(f"  Anthem: {anthem_data['video_title']} [{video_id}]")

    # Step 3: Download audio (prefer mp4a for broadest browser compatibility)
    if not dry_run:
        audio_url = None
        best_bitrate = 0
        for fmt in meta.get("adaptiveFormats", []):
            if "audio/mp4" in fmt.get("type", ""):
                br = int(fmt.get("bitrate", 0) or 0)
                if br > best_bitrate:
                    best_bitrate = br
                    audio_url = fmt.get("url")

        if audio_url:
            try:
                req = urllib.request.Request(audio_url, headers={"User-Agent": UA})
                with urllib.request.urlopen(req, timeout=60) as r:
                    audio_bytes = r.read()
                if len(audio_bytes) > 10000:
                    with open(audio_path, "wb") as f:
                        f.write(audio_bytes)
                    anthem_data["audio_file"] = "anthem.m4a"
                    anthem_data["has_audio"] = True
                    print(f"  Audio: {len(audio_bytes)//1024}KB downloaded")
                else:
                    print(f"  Audio: too small ({len(audio_bytes)} bytes), skipping")
            except Exception as e:
                print(f"  Audio download failed: {e}")
    else:
        anthem_data["audio_file"] = "anthem.m4a"
        anthem_data["has_audio"] = True

    # Step 4: Download captions (English preferred, then native language)
    captions_list = meta.get("captions", [])
    downloaded_captions = []

    cap_order = sorted(captions_list, key=lambda c: (
        0 if c.get("language_code") == "en" else
        1 if "(auto-generated)" not in c.get("label", "") else 2
    ))

    for cap in cap_order[:2]:
        cap_url_path = cap.get("url", "")
        if not cap_url_path:
            continue
        cap_url = INVIDIOUS_BASE + cap_url_path
        lang_code = cap.get("language_code") or "en"
        label = cap.get("label", lang_code)
        safe_label = re.sub(r'[^a-zA-Z0-9_-]', '_', lang_code)[:10]
        cap_filename = f"anthem.{safe_label}.vtt"
        cap_path = os.path.join(ASSETS_DIR, "teams", slug, cap_filename)

        if not dry_run:
            try:
                cap_req = urllib.request.Request(cap_url, headers={"User-Agent": UA})
                with urllib.request.urlopen(cap_req, timeout=15) as r:
                    vtt_bytes = r.read()
                if len(vtt_bytes) > 50:
                    with open(cap_path, "wb") as f:
                        f.write(vtt_bytes)
                    downloaded_captions.append({
                        "lang": lang_code,
                        "label": label,
                        "file": cap_filename,
                    })
                    print(f"  Captions: {label} ({len(vtt_bytes)} bytes)")
                else:
                    print(f"  Captions: {label} empty, skipping")
            except Exception as e:
                print(f"  Caption download failed ({label}): {e}")
        else:
            downloaded_captions.append({"lang": lang_code, "label": label, "file": cap_filename})

        time.sleep(0.5)

    anthem_data["captions"] = downloaded_captions

    if not dry_run:
        with open(json_path, "w") as f:
            json.dump(anthem_data, f, ensure_ascii=False, indent=2)

    time.sleep(1)


def ensure_dirs(slug, dry_run=False):
    """Create assets/teams/{slug}/players/ directory."""
    path = os.path.join(ASSETS_DIR, "teams", slug, "players")
    if not dry_run:
        os.makedirs(path, exist_ok=True)
    return path


def save_roster(slug, squad_data, dry_run=False, force=False):
    """Save roster.json for a team."""
    path = os.path.join(ASSETS_DIR, "teams", slug, "roster.json")
    if not force and os.path.exists(path):
        print(f"  Skip (exists): {path}")
        return False
    if dry_run:
        print(f"  Would write: {path} ({len(squad_data['players'])} players)")
        return True
    with open(path, "w") as f:
        json.dump(squad_data, f, ensure_ascii=False, indent=2)
    print(f"  Saved: {path} ({len(squad_data['players'])} players)")
    return True


def download_player_photos(slug, squad_data, dry_run=False, force=False):
    """
    Download player photos from TheSportsDB (per-name search) with Wikipedia fallback.
    Updates roster.json with photo paths.
    """
    players_dir = os.path.join(ASSETS_DIR, "teams", slug, "players")
    os.makedirs(players_dir, exist_ok=True)

    roster_path = os.path.join(ASSETS_DIR, "teams", slug, "roster.json")
    if not os.path.exists(roster_path):
        print(f"  No roster.json for {slug}, skipping photos")
        return

    with open(roster_path) as f:
        roster_data = json.load(f)

    players = roster_data["players"]
    # Determine team nationality string for TheSportsDB filtering
    team_display = roster_data.get("team", slug)
    nationality_map = {
        "england": "English", "scotland": "Scottish", "usa": "American",
        "korea-republic": "South Korean", "ir-iran": "Iranian",
        "cote-d-ivoire": "Ivorian", "congo-dr": "Congolese",
        "cabo-verde": "Cape Verdean", "czechia": "Czech",
        "bosnia-and-herzegovina": "Bosnian", "curacao": "Curaçaoan",
        "turkiye": "Turkish", "new-zealand": "New Zealand",
        "saudi-arabia": "Saudi Arabian", "south-africa": "South African",
        "algeria": "Algerian", "argentina": "Argentine",
        "australia": "Australian", "austria": "Austrian",
        "belgium": "Belgian", "brazil": "Brazilian",
        "canada": "Canadian", "colombia": "Colombian",
        "croatia": "Croatian", "ecuador": "Ecuadorian",
        "egypt": "Egyptian", "france": "French",
        "germany": "German", "ghana": "Ghanaian",
        "haiti": "Haitian", "iraq": "Iraqi",
        "japan": "Japanese", "jordan": "Jordanian",
        "mexico": "Mexican", "morocco": "Moroccan",
        "netherlands": "Dutch", "norway": "Norwegian",
        "panama": "Panamanian", "paraguay": "Paraguayan",
        "portugal": "Portuguese", "qatar": "Qatari",
        "senegal": "Senegalese", "spain": "Spanish",
        "sweden": "Swedish", "switzerland": "Swiss",
        "tunisia": "Tunisian", "uruguay": "Uruguayan",
        "uzbekistan": "Uzbekistani",
    }
    expected_nationality = nationality_map.get(slug, team_display)

    found_photos = 0
    needs_wiki_lookup = []  # players without TSDB photos

    for player in players:
        num = player["number"]
        name = player["name"]
        pos = player["position"].lower()

        photo_path = os.path.join(players_dir, f"{num}.png")

        # Skip if already downloaded
        if not force and os.path.exists(photo_path):
            player["photo"] = f"players/{num}.png"
            found_photos += 1
            continue

        if dry_run:
            player["photo"] = f"players/{num}.png"  # assume success in dry run
            found_photos += 1
            continue

        # Step 1: TheSportsDB per-name search
        tsdb_url = f"https://www.thesportsdb.com/api/v1/json/3/searchplayers.php?p={urllib.parse.quote(name)}"
        photo_downloaded = False
        try:
            raw = fetch_url(tsdb_url, retries=2, delay=2)
            data = json.loads(raw)
            tsdb_players = data.get("player") or []

            # Filter by sport and try to match nationality
            soccer_players = [p for p in tsdb_players if p.get("strSport") == "Soccer"]

            # Try nationality match first
            matched = None
            for p in soccer_players:
                nat = p.get("strNationality", "")
                if expected_nationality.lower() in nat.lower() or nat.lower() in expected_nationality.lower():
                    matched = p
                    break
            if not matched and soccer_players:
                matched = soccer_players[0]  # take first soccer player

            if matched:
                # Prefer cutout over thumb
                img_url = matched.get("strCutout") or matched.get("strThumb") or ""
                if img_url and img_url.startswith("http"):
                    img_req = urllib.request.Request(img_url, headers={"User-Agent": UA})
                    with urllib.request.urlopen(img_req, timeout=15) as r:
                        img_data = r.read()
                    if len(img_data) > 1000:
                        with open(photo_path, "wb") as f:
                            f.write(img_data)
                        player["photo"] = f"players/{num}.png"
                        found_photos += 1
                        photo_downloaded = True
        except Exception as e:
            pass  # fall through to Wikipedia

        if not photo_downloaded:
            needs_wiki_lookup.append(player)

        time.sleep(2)  # Rate limit: 30 req/min max

    # Step 2: Wikipedia fallback (batch 50 players per request)
    if needs_wiki_lookup:
        print(f"  Wikipedia fallback for {len(needs_wiki_lookup)} players...")
        batch_size = 50
        for i in range(0, len(needs_wiki_lookup), batch_size):
            batch = needs_wiki_lookup[i:i+batch_size]
            titles = "|".join(urllib.parse.quote(p["name"].replace(" ", "_")) for p in batch)
            wiki_url = (f"https://en.wikipedia.org/w/api.php?action=query"
                       f"&titles={titles}&prop=pageimages&format=json"
                       f"&pithumbsize=300&origin=*")
            try:
                raw = fetch_url(wiki_url)
                pages = json.loads(raw).get("query", {}).get("pages", {})
                # Build name→thumb map
                thumb_map = {}
                for page in pages.values():
                    title = page.get("title", "").replace("_", " ")
                    thumb = page.get("thumbnail", {}).get("source", "")
                    if thumb:
                        thumb_map[title.lower()] = thumb

                for player in batch:
                    name_lower = player["name"].lower()
                    thumb_url = thumb_map.get(name_lower)
                    if thumb_url:
                        try:
                            num = player["number"]
                            photo_path = os.path.join(players_dir, f"{num}.png")
                            img_req = urllib.request.Request(thumb_url, headers={"User-Agent": UA})
                            with urllib.request.urlopen(img_req, timeout=15) as r:
                                img_data = r.read()
                            if len(img_data) > 1000:
                                with open(photo_path, "wb") as f:
                                    f.write(img_data)
                                player["photo"] = f"players/{num}.png"
                                found_photos += 1
                        except Exception:
                            pass
            except Exception as e:
                print(f"  Wikipedia batch failed: {e}")
            time.sleep(1)

    # Step 3: Silhouette fallback for remaining
    silhouette_count = 0
    for player in players:
        if not player.get("photo"):
            pos_key = player["position"].lower()
            pos_key = pos_key if pos_key in ("gk", "df", "mf", "fw") else "mf"
            player["photo"] = f"silhouettes/{pos_key}.svg"
            silhouette_count += 1

    # Save updated roster.json
    with open(roster_path, "w") as f:
        json.dump(roster_data, f, ensure_ascii=False, indent=2)

    print(f"  {slug}: {found_photos}/26 photos, {silhouette_count} silhouettes")
    return found_photos, silhouette_count


def enrich_player_bios(slug, dry_run=False, force=False):
    """Enrich roster.json players with TheSportsDB bio data (search + lookup)."""
    roster_path = os.path.join(ASSETS_DIR, "teams", slug, "roster.json")
    if not os.path.exists(roster_path):
        print(f"  No roster.json for {slug}, skipping enrichment")
        return 0

    with open(roster_path) as f:
        roster_data = json.load(f)

    players = roster_data["players"]
    team_display = roster_data.get("team", slug)

    nationality_map = {
        "england": "English", "scotland": "Scottish", "usa": "American",
        "korea-republic": "South Korean", "ir-iran": "Iranian",
        "cote-d-ivoire": "Ivorian", "congo-dr": "Congolese",
        "cabo-verde": "Cape Verdean", "czechia": "Czech",
        "bosnia-and-herzegovina": "Bosnian", "curacao": "Curaçaoan",
        "turkiye": "Turkish", "new-zealand": "New Zealand",
        "saudi-arabia": "Saudi Arabian", "south-africa": "South African",
        "algeria": "Algerian", "argentina": "Argentine",
        "australia": "Australian", "austria": "Austrian",
        "belgium": "Belgian", "brazil": "Brazilian",
        "canada": "Canadian", "colombia": "Colombian",
        "croatia": "Croatian", "ecuador": "Ecuadorian",
        "egypt": "Egyptian", "france": "French",
        "germany": "German", "ghana": "Ghanaian",
        "haiti": "Haitian", "iraq": "Iraqi",
        "japan": "Japanese", "jordan": "Jordanian",
        "mexico": "Mexican", "morocco": "Moroccan",
        "netherlands": "Dutch", "norway": "Norwegian",
        "panama": "Panamanian", "paraguay": "Paraguayan",
        "portugal": "Portuguese", "qatar": "Qatari",
        "senegal": "Senegalese", "spain": "Spanish",
        "sweden": "Swedish", "switzerland": "Swiss",
        "tunisia": "Tunisian", "uruguay": "Uruguayan",
        "uzbekistan": "Uzbekistani",
    }
    expected_nationality = nationality_map.get(slug, team_display)

    enriched_count = 0
    for player in players:
        name = player["name"]

        if not force and player.get("tsdb_id"):
            enriched_count += 1
            continue

        search_url = "https://www.thesportsdb.com/api/v1/json/3/searchplayers.php?p=" + urllib.parse.quote(name)
        try:
            raw = fetch_url(search_url, retries=3, delay=5)
            data = json.loads(raw)
            tsdb_players = data.get("player") or []
        except Exception as e:
            print(f"    Search failed for {name}: {e}")
            time.sleep(6)
            continue

        soccer_players = [p for p in tsdb_players if p.get("strSport") == "Soccer"]
        matched = None
        for p in soccer_players:
            nat = p.get("strNationality", "")
            if expected_nationality.lower() in nat.lower() or nat.lower() in expected_nationality.lower():
                matched = p
                break
        if not matched and soccer_players:
            matched = soccer_players[0]

        if not matched:
            print(f"    No TSDB match for {name}")
            time.sleep(4)
            continue

        id_player = matched.get("idPlayer")
        if not id_player:
            time.sleep(4)
            continue

        time.sleep(4)

        lookup_url = f"https://www.thesportsdb.com/api/v1/json/3/lookupplayer.php?id={id_player}"
        try:
            raw = fetch_url(lookup_url, retries=3, delay=5)
            ldata = json.loads(raw)
            plist = ldata.get("players") or []
            p = plist[0] if plist else None
        except Exception as e:
            print(f"    Lookup failed for {name} (id={id_player}): {e}")
            time.sleep(6)
            continue

        if not p:
            time.sleep(4)
            continue

        social = {
            "instagram": p.get("strInstagram"),
            "facebook": p.get("strFacebook"),
            "twitter": p.get("strTwitter"),
            "youtube": p.get("strYoutube"),
            "website": p.get("strWebsite"),
        }
        social = {k: v for k, v in social.items() if v}

        last_name = p.get("strLastName")
        player_name_full = p.get("strPlayer", "")
        first_name = (player_name_full.replace(last_name, "").strip() if last_name else None)

        bio_raw = p.get("strDescriptionEN") or ""
        bio = bio_raw[:500]

        player["tsdb_id"] = p.get("idPlayer")
        player["full_name"] = p.get("strPlayerAlternate") or p.get("strPlayer")
        player["last_name"] = last_name
        player["first_name"] = first_name if first_name else None
        player["bio"] = bio
        player["birth_location"] = p.get("strBirthLocation")
        player["height"] = p.get("strHeight")
        player["weight"] = p.get("strWeight")
        player["position_detail"] = p.get("strPosition")
        player["preferred_foot"] = p.get("strSide")
        player["kit"] = p.get("strKit")
        player["social"] = social
        player["wikidata_id"] = p.get("idWikidata")

        for key in ["full_name", "last_name", "first_name", "bio", "birth_location",
                     "height", "weight", "position_detail", "preferred_foot", "kit", "wikidata_id"]:
            if player.get(key) is None:
                player.pop(key, None)

        enriched_count += 1
        print(f"    ✓ {name} → {player.get('full_name', name)} ({player.get('position_detail', '')})")
        time.sleep(4)

    if not dry_run:
        with open(roster_path, "w") as f:
            json.dump(roster_data, f, ensure_ascii=False, indent=2)

    print(f"  {slug}: {enriched_count}/{len(players)} players enriched")
    return enriched_count


def main():
    parser = argparse.ArgumentParser(description="Download WC2026 team assets")
    parser.add_argument("--team", help="Single team slug (e.g. mexico)")
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview without writing"
    )
    parser.add_argument(
        "--force", action="store_true", help="Overwrite existing files"
    )
    parser.add_argument(
        "--photos-only", action="store_true", help="Only download player photos"
    )
    parser.add_argument(
        "--skip-photos", action="store_true", help="Download everything except player photos"
    )
    parser.add_argument(
        "--anthems-only", action="store_true", help="Only download anthems"
    )
    parser.add_argument(
        "--enrich", action="store_true", help="Enrich player bios from TheSportsDB"
    )
    args = parser.parse_args()

    if args.team and args.team not in TEAMS_BY_SLUG:
        print(f"Unknown team slug: '{args.team}'")
        print(f"Valid slugs: {', '.join(sorted(TEAMS_BY_SLUG.keys()))}")
        sys.exit(1)

    if args.team:
        teams_to_process = [(TEAMS_BY_SLUG[args.team],
                             TEAMS[TEAMS_BY_SLUG[args.team]])]
    else:
        teams_to_process = list(TEAMS.items())

    if args.enrich:
        total = len(teams_to_process)
        print(f"Enriching player bios for {total} teams...")
        for i, (name, meta) in enumerate(teams_to_process, 1):
            slug = meta["slug"]
            print(f"\n[{i}/{total}] {name} ({slug})")
            enrich_player_bios(slug, dry_run=args.dry_run, force=args.force)
        if args.dry_run:
            print(f"\nDry run complete. Would enrich {total} teams.")
        else:
            print(f"\nDone. Enriched {total} teams.")
        return

    if not args.anthems_only:
        squads = parse_wikipedia_squads()
        print(f"Parsed {sum(len(s['players']) for s in squads.values())} players "
              f"across {len(squads)} teams\n")
    else:
        squads = {}

    total = len(teams_to_process)
    for i, (name, meta) in enumerate(teams_to_process, 1):
        slug = meta["slug"]
        print(f"\n[{i}/{total}] {name} ({slug})")
        ensure_dirs(slug, dry_run=args.dry_run)

        if args.anthems_only:
            anthem_name = ANTHEM_NAMES.get(slug, name)
            download_anthem_invidious(slug, anthem_name, name, dry_run=args.dry_run, force=args.force)
            if i < total:
                time.sleep(1)
            continue

        squad_data = squads.get(slug)
        if squad_data:
            save_roster(slug, squad_data, dry_run=args.dry_run, force=args.force)
        else:
            print(f"  Roster: no Wikipedia data for {name}")

        if not args.photos_only:
            download_country_data(slug, meta["iso2"], dry_run=args.dry_run, force=args.force)
            download_flag(slug, meta["flagcdn"], dry_run=args.dry_run, force=args.force)
            anthem_name = ANTHEM_NAMES.get(slug, name)
            download_anthem_invidious(slug, anthem_name, name, dry_run=args.dry_run, force=args.force)

        if squad_data and not args.skip_photos:
            download_player_photos(slug, squad_data, dry_run=args.dry_run, force=args.force)

        if i < total:
            time.sleep(1)

    if args.dry_run:
        print(f"\nDry run complete. Would process {total} teams.")
    else:
        print(f"\nDone. Processed {total} teams.")


if __name__ == "__main__":
    main()
