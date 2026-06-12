# Asset Licenses and Provenance

<!-- SPDX-License-Identifier: CC0-1.0 AND CC-BY-SA-4.0 -->

This directory contains pre-cached data and media for the FIFA World Cup 2026
wallchart. Assets are sourced from public APIs and freely-available resources.
No registration or API keys are required to regenerate them via `download_assets.py`.

## Roster Data (`teams/*/roster.json`)

- **Source**: [Wikipedia](https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_squads)
  (MediaWiki API, wikitext parsing)
- **License**: [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)
- **SPDX**: `CC-BY-SA-4.0`
- **Fields**: Squad number, position, name, DOB, caps, goals, club
- **Enrichment**: Player bios and social media links from
  [TheSportsDB](https://www.thesportsdb.com/) (free API, CC BY-SA 4.0)

## Country Data (`teams/*/country.json`)

- **Source**: [GeoAPI.info](https://geoapi.info/) (REST API)
- **License**: [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)
  (ISO country data)
- **SPDX**: `CC-BY-SA-4.0`
- **Note**: England and Scotland use hardcoded overrides (GeoAPI returns UK-level
  data for `GB`)

## Flag Images (`teams/*/flag.svg`)

- **Source**: [flagcdn.com](https://flagcdn.com/) /
  [Flagpedia.net](https://flagpedia.net/)
- **License**: Public domain (sourced from Wikimedia Commons SVGs)
- **SPDX**: `CC0-1.0`

## Player Photos (`teams/*/players/*.png`)

- **Source**: [TheSportsDB](https://www.thesportsdb.com/) (`strCutout` / `strThumb`
  fields) with [Wikipedia](https://en.wikipedia.org/) `pageimages` API fallback
- **License**: [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)
  (TheSportsDB community-contributed); Wikipedia images vary per file
- **SPDX**: `CC-BY-SA-4.0`
- **Fallback**: Position silhouettes in `silhouettes/` are original work,
  released as CC0

## Silhouette SVGs (`silhouettes/*.svg`)

- **Source**: Original work (generated for this project)
- **License**: Public domain
- **SPDX**: `CC0-1.0`

## National Anthem Audio (`teams/*/anthem.m4a`)

- **Source**: YouTube via [Invidious](https://invidious.io/) API (audio stream
  extraction)
- **License**: Audio content is subject to the original uploader's rights and
  YouTube's Terms of Service. Included here as short educational excerpts under
  fair use / fair dealing provisions. These files are provided for personal,
  non-commercial use as part of this wallchart application.
- **Note**: Set `INVIDIOUS_URL` environment variable to point to your Invidious
  instance when regenerating

## National Anthem MIDI (`teams/*/anthem.mid`)

- **Source**: [Pauline's MIDI Collection](https://midi.polyna.eu/anthems/encarta/)
  (ex-Microsoft Encarta orchestral arrangements)
- **License**: Public domain (original Encarta MIDI arrangements are not
  copyrighted; national anthems themselves are public domain in most
  jurisdictions)
- **SPDX**: `CC0-1.0`
- **Coverage**: 46/48 teams (Curaçao and Scotland not available as MIDI)

## Anthem Metadata (`teams/*/anthem.json`)

- **Source**: Anthem names from
  [Wikidata](https://www.wikidata.org/) (SPARQL, CC0);
  video metadata from Invidious search results
- **License**: [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/)
  (Wikidata) / factual data (not copyrightable)
- **SPDX**: `CC0-1.0`

## Regeneration

All assets can be regenerated from public sources:

```bash
python3 download_assets.py              # all data
python3 download_assets.py --team brazil # single team
python3 download_assets.py --photos-only # player photos only
python3 download_assets.py --enrich      # TheSportsDB bio enrichment
```

No API keys or authentication required. Set `INVIDIOUS_URL` for anthem audio.
