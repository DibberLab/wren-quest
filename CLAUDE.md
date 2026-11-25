# Wren Quest

An 8-bit top-down action-adventure game (original IP: hero Wren, the Ember Crown, the Obsidian King). Static site.

- Hostname: https://quest.dibberlab.me
- dibberlab-infra site name: `wren-quest` (`server/sites/wren-quest.conf`, TYPE=static, standard static nginx template)
- Served from: `site/` (the whole game is `site/index.html`)

## Working on this

- One file on purpose: HTML, CSS and JS inline in `site/index.html`. No build step, no npm. Fonts come from Google Fonts (Press Start 2P, Silkscreen).
- The game is a 256x232 canvas: 56px HUD on top, 256x176 playfield (16x11 tiles of 16px). Fixed 60 fps tick in `tick()`, rendering in `draw()`.
- World generation is seeded (`SEED`), so the map is the same for every player. Changing `SEED`, `WW`/`WH`, `CEN`, or the cave pattern reshuffles the world and old saves will point at different places: bump `SKEY` when you do that.
- Saves live in the player's localStorage under `SKEY` (currently `wrenquest-save-v3`). `loadSave()` also reads the pre-rename key `emberwake-save-v3`, so keep that fallback. New state fields go in `newState()`; loading does `Object.assign(newState(), save)`, so new fields get defaults on old saves.
- Music and sound effects are synthesized with Web Audio (`SONGS`, `sfx()`). Keep the music original; do not reproduce melodies from existing games.
- Disc golf: `HOLES`/`HOLEOF`/`BASKETS` define the 27-hole course (seeded, one per region in `CEN` plus 3, numbered by distance from `START`). Strokes are counted per screen visit in `G.strokes`; first-time results are saved in `S.bk`. In `basketMade()`, par or better refills hearts and a bogey or worse takes one heart (2 hp), never below 1 hp. Every 9 holes `openCard()` shows the scorecard (`drawCard()`, stats from `progress()`). Cards are by hole number: card 1 is holes 1-9, card 2 is 10-18, card 3 is 19-27; unplayed holes show `-`. On the pause map page, sunk baskets are green and found-but-unsunk ones white; A opens the card with the next unplayed hole (`nextHole()`).
- Sprites are pixel strings in `SPR`; palettes are swapped per enemy tier. The hero's floppy cap is drawn procedurally in `drawCap()`.
- Test in a browser before shipping: start a new game, walk a few screens, open the inventory (Enter), enter a dungeon, and check the console is clean.

## How changes ship

Branch + PR against `main`; merging deploys via the shared `Deploy` workflow (dibberlab-deploy on the droplet). Never push straight to `main`.
