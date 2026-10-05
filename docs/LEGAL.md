# Legal notes: an original metroidvania

> This document is a practical summary, **not legal advice**. If you plan to
> sell or heavily promote a game, consult a lawyer in your jurisdiction.

VESPER is inspired by the *gameplay* of classic exploration-platformers such as
Super Metroid, but it shares **nothing protected** with them: no names, no
characters, no artwork, no music, no logos, no code.  This page explains how
that is possible and how to keep it that way.

## Ideas are not copyrighted — expression is

Copyright protects the *expression* of an idea, not the idea itself:

- **Not protected:** game mechanics and rules — exploration, ability-gated
  progression, a minimap, health tanks, wall jumps, a charge beam.  These are
  functional ideas.  That is why an entire genre of "metroidvania" games
  exists from many studios.
- **Protected:** the specific characters, names, story text, sprites, music,
  sound effects, level data, logos and trade dress of another game.

So you may build a game that *feels* like Super Metroid.  You may not copy its
characters, art, audio or branding.

## Trademarks

Trademark protects names and branding that identify a source of goods:

- Do **not** use "*Metroid*", "*Samus*", "*Super Metroid*", the stylised "S"
  logo, or any confusingly similar mark.
- Do not name your project "Metroid-something" or mimic Nintendo's box art /
  logo style.
- The word "**metroidvania**" is a genre term and is generally fine to
  *describe* your game (e.g. in the README or a store tag).  Avoid it in the
  game's title/brand in a way that suggests endorsement or affiliation.

## Assets: generate or create your own

The safest path — the one this project takes — is to create every asset
yourself:

- **Art:** VESPER draws all sprites procedurally in `vesper/game/art/`
  (geometric pixel art).  No sprite is ripped, traced or sampled from another
  game.
- **Audio:** all sounds and the music loop are synthesised from oscillators in
  `vesper/engine/audio.py`.  No sample from another game is used.
- **Fonts:** only pygame's bundled default font is used.
- **Code:** written from scratch; no proprietary SDKs or leaked source.

If you add third-party assets, check their licences — they must be compatible
with the GPL (e.g. CC0, CC-BY, GPL).

## Story, characters and names

Invent your own:

| Risk if copied            | VESPER's original choice        |
|---------------------------|---------------------------------|
| "Samus Aran"              | **Vesper**, bounty hunter       |
| "Zebes / SR388"           | **Nara system / the Depths**    |
| "Metroid", "Mother Brain" | **Warden**, the Nara Core       |
| Nintendo suits/voices     | original crimson-and-cyan suit  |

Characters, names, dialogue and world-building are creative expression — make
them yours.

## Fan projects are risky

Even a free, non-commercial fan game that reuses Nintendo's characters or
assets can be taken down, because it infringes copyright/trademark.  A fully
original game avoids that entirely.  "Inspired by" is fine; "uses their stuff"
is not.

## Checklist before publishing

- [ ] Original title, with no protected words or lookalike logos.
- [ ] Original protagonist, world and story.
- [ ] All sprites, sounds and music created by you or properly licensed.
- [ ] No data ripped from a commercial ROM (levels, text, sprites, audio).
- [ ] Mechanics re-implemented from scratch (you may take inspiration freely).
- [ ] A clear licence for your own work (this project: **GPL-3.0-or-later**).
- [ ] Reasonable effort made to avoid consumer confusion with any existing IP.

## About this project's licence

VESPER's source is licensed **GPL-3.0-or-later** (see `LICENSE`).  The
procedurally generated graphics and audio are produced by that same GPL code,
so they are distributed under the same terms.  You may study, modify and
redistribute the game as long as derivative works remain free under the GPL.

## Do not

- Do not rename this project to anything containing another company's
  trademark.
- Do not add ripped assets to a fork and redistribute it; that would infringe
  others' rights regardless of the GPL.
- Do not imply that this project is endorsed by or affiliated with any existing
  game or company.
