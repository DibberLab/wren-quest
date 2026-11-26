# Wren Quest

An 8-bit top-down action-adventure in the spirit of classic NES games, with an original hero, world and chiptune soundtrack. Live at **https://quest.dibberlab.me**.

- 864-screen overworld (36x24), 27 disc golf holes that are also 27 dungeons, the Obsidian Throne, 9 secret puzzle dungeons
- Disc golf: sink one of the 27 baskets and the ground opens into its dungeon. Beat the boss, then sink a ghostly hole in par or better for one of 27 crown pieces. Place a target marker, pick a shot shape, lock power and release; within 30 ft a putting mini-game takes over (lock left/right and up/down inside the chains). Miss par and you replay the hole; every third miss costs a heart container, but never more than one per hole, and you can walk away and come back. All holes are par 3 or 4. Every 9 holes brings a scorecard with a progress report
- Sword levels 1-30 earned through kills (enemies toughen with you, but more slowly); heart pieces (4 make a heart container) from duels, aces, birdies, moats, bounties and sword milestones
- 17 underground caverns (15-35 screens each, some connecting regions) with cave-only enemies, dim lighting, ore to mine, and a unique reward deep in each; a Pick-Shovel to break boulders and dig up hidden entrances and buried treasure
- 30 kinds of monster (15 added in this update), from the common Marebear, who oozes sticky white goo and sometimes gets smitten and starts a charm duel (fill her love meter and she walks off with a heart container; beat a Marebear in the next duel to win it back), to gem-stealing ravens, rolling thornbacks and sleeping boulderkin
- Stamina: tap B to roll, hold it to sprint; jumping, rolling, sprinting, spin attacks and heavy swings use stamina, which refills quickly; run dry and you're winded for a moment
- Jump places: hurdles to leap, rune stones to land on (they sink stone pillars), and treasure islands in moats (wide moats need a sprinting jump)
- People of the land wander the overworld: talkers, sages, traders, gift-givers, thieves you can chase across screens, bandits, and challengers who start duels
- 34-slot inventory: discs, weapons, potions, scrolls, and only the rare high-powered mushrooms (most mushrooms take effect when you pick them up); relics and secrets to find
- Champion duels, side quests, NPCs, bounty boards, dojos
- Keyboard, gamepad and touch controls; Web Audio chiptune music (epic, doomy minor-key themes with drones, galloping bass and toms) and sound effects
- Progress saves in the player's browser (localStorage key `wrenquest-save-v3`)

## Admin

Open the site once with `?admin` (for example https://quest.dibberlab.me/?admin) to turn on admin on that device; `?admin=off` turns it off. Press the backtick key (`` ` ``) or the Admin button to fast travel to any hole's dungeon, straight into any hole's golf challenge, or into the Obsidian Throne.

## Tests

```bash
pip install playwright && playwright install chromium   # once
python3 tests/run.py                                    # all suites, about a minute
```

Suites: `world` (map, dungeons and caverns connect), `golf` (every hole makeable in par), `flows` (the hole loop and other key paths), `layout` (no overlapping or off-screen text on about 30 screens drawn with worst-case values) and `stress` (random input, no console errors). Balance numbers are in `TUNE` at the top of `site/index.html`.

## How it runs

A static site: everything is in `site/index.html` (HTML, CSS and JS in one file, no build step, no dependencies beyond Google Fonts). nginx serves `site/` on the DibberLab droplet.

Run it locally by opening `site/index.html`, or `python3 -m http.server -d site 8080`.

## Deploys

Merging into `main` deploys. `.github/workflows/deploy.yml` is the shared DibberLab template from `amcmorrow/dibberlab-infra`; the site config is `server/sites/wren-quest.conf` there.
