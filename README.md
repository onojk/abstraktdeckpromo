# abstraktdeckpromo — demoscene promo video for Abstrakt Deck

A 45–75 s demoscene-style promo for **Abstrakt Deck**, an audio-reactive art app (Rust/wgpu),
now on the [Microsoft Store](https://apps.microsoft.com/detail/9NR8XFDVFN48), and on Linux
through the Snap Store and a PPA.

Rendered offline and deterministically from GLSL shaders, synced to an analysis of the track.
The pipeline (moderngl/EGL renderer, `analyze.py`, `sync.py`, ffmpeg rgb24 pipe + audio mux)
is adapted from the author's earlier videos: lightholesdemo, tentimesdemo, laser-beam-demo.

## Structure

| # | beat | effect |
|---|---|---|
| 1 | cracktro intro: "ONOJK123 ART PRESENTS" | starfield, raster bars, glitchy cracktro type |
| 2 | title hit: "ABSTRAKT DECK" | logo slam, chromatic glitch, flash |
| 3a | AUDIO-REACTIVE: visuals that dance to your music | spectrum bars / plasma pumping on the kick |
| 3b | KALEIDOSCOPES / BLACK-HOLE FEEDBACK / MULTI-PANEL GRIDS | rotozoom kaleidoscope, feedback tunnel, grid split, in stand-in visuals (no app footage) |
| 3c | RECORD STRAIGHT TO VIDEO | REC overlay, CRT frame |
| 3d | BUILT IN RUST + WGPU | copper bars, vector type |
| 4 | NOW ON THE MICROSOFT STORE / Also on Linux: Snap Store & PPA / Store URL | held long enough to read |
| 5 | greetz scroller | sine scroller |

## Layout

- `fx/` GLSL scenes · `analyze.py` track → `cache/features.json` · `sync.py` music-driven uniforms
- `audio/` the track and `footage/` app recordings (both git-ignored; bring your own)
- `renders/` outputs (git-ignored)

## Deliverables

- 1920×1080 MP4, H.264, yuv420p, `-preset veryfast` (YouTube / LinkedIn)
- 1080×1080 square cut (social)
- 3–5 s GIF loop of the title hit

## License

MIT for the code (see [LICENSE](LICENSE)). The music and app footage are not included.

## Rebuild

```sh
# lightholesdemo's venv works (numpy + moderngl); or: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
python analyze.py audio/abstrakt_deck.wav        # -> cache/features.json
python sections.py                               # -> data/beats.json, data/sections.json
python render.py renders/preview.mp4 --full --res 480        # 848x480 preview
python render.py renders/abstrakt_deck_promo_1080p.mp4 --full  # 1920x1080 master
python make_cut.py cut                           # ~60 s 1080x1080 square cut
python make_cut.py loop                          # title-hit loop, MP4 + GIF
```

The four "app" scenes (kaleidoscope, black-hole feedback, multi-panel grid, record) use
stand-in visuals in the app's look, not screen captures; they carry the note
"DEMOSCENE TRIBUTE - NOT ACTUAL APP FOOTAGE", as does the outro.

## Finals (Nov 11, 2026; `renders/`, not committed)

- `abstrakt_deck_promo_1080p.mp4`: 1920x1080, 30 fps, H.264 High, yuv420p, `-preset veryfast`
  CRF 20, AAC 320k; 195.533 s; 170,066,882 bytes.
