# Wren Quest

An 8-bit top-down action-adventure in the spirit of classic NES games, with an original hero, world and chiptune soundtrack. Live at **https://quest.dibberlab.me**.

- 864-screen overworld (36x24), 14 shard dungeons plus the Obsidian Throne, 9 secret puzzle dungeons
- Disc golf: throw discs, sink them in baskets across the world to refill your hearts
- 35-slot inventory: discs, weapons, potions, scrolls, mushrooms; relics and secrets to find
- Champion duels, side quests, NPCs, bounty boards, dojos
- Keyboard, gamepad and touch controls; Web Audio chiptune music and sound effects
- Progress saves in the player's browser (localStorage key `wrenquest-save-v3`)

## How it runs

A static site: everything is in `site/index.html` (HTML, CSS and JS in one file, no build step, no dependencies beyond Google Fonts). nginx serves `site/` on the DibberLab droplet.

Run it locally by opening `site/index.html`, or `python3 -m http.server -d site 8080`.

## Deploys

Merging into `main` deploys. `.github/workflows/deploy.yml` is the shared DibberLab template from `amcmorrow/dibberlab-infra`; the site config is `server/sites/wren-quest.conf` there.
