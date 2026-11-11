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
| 3b | KALEIDOSCOPES / BLACK-HOLE FEEDBACK / MULTI-PANEL GRIDS | rotozoom kaleidoscope, feedback tunnel, grid split, with real app footage |
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
