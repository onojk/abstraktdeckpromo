#!/usr/bin/env python3
"""make_cut.py — the ~60 s cut (square for social) and the title-hit loop.

    python make_cut.py cut  [--res 1080]           # renders/abstrakt_deck_promo_60s_square.mp4
    python make_cut.py loop [--res 1080]           # renders/abstrakt_deck_title_loop.{mp4,gif}

The cut is three pieces of the full film, each rendered from its own source times (so every
scene is exactly as in the full video) and spliced on bar lines, with the music cut at the
same frame-exact points:

    A  2 bars before the title hit -> 8 bars after it      (cracktro tail, the slam, the subtitle)
    B  chorus 1, its first 20 bars                         (headline, then the Store URL ~14 s)
    C  the outro, to the end                               (platforms, greetz, fade)

Why these points (data/beats.json, kick energy per beat phase): the title section is 8.5 bars,
because verse 1 enters half a bar late, and chorus 1 is 20.5 bars. Splicing at the section
ends would put the beat two beats out; ending A at title + 8 bars and B at chorus 1 + 20 bars
joins downbeat to downbeat. Each audio piece gets a 10 ms fade at its edges (no clicks, no
change in length), so picture and sound stay frame-locked.

The loop is the 2 bars from the title hit: slam, subtitle typing, the beat bounce; its last
frame runs into the next slam, so it repeats on the beat.
"""
import argparse, json, os, subprocess, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIO = os.path.join(HERE, "audio", "abstrakt_deck.wav")
RENDERS = os.path.join(HERE, "renders")
FPS = 30
PY = sys.executable

def beats():
    return np.array(json.load(open(os.path.join(HERE, "data", "beats.json")))["beats"])

def sections():
    return {s["name"]: s for s in json.load(open(os.path.join(HERE, "data", "sections.json")))["sections"]}

def beat_frame(b, t, offset_beats=0):
    """The frame nearest the beat nearest t, moved by offset_beats."""
    k = int(np.argmin(np.abs(b - t))) + offset_beats
    return int(round(b[k] * FPS))

def pieces():
    b, S = beats(), sections()
    hit = S["title"]["start"]
    A = (beat_frame(b, hit, -8), beat_frame(b, hit, 32))                  # -2 bars .. +8 bars
    B = (beat_frame(b, S["chorus1"]["start"]), beat_frame(b, S["chorus1"]["start"], 80))   # 20 bars
    C = (beat_frame(b, S["outro"]["start"]), int(round(json.load(open(os.path.join(HERE, "cache", "features.json")))["duration"] * FPS)))
    return [("A", *A), ("B", *B), ("C", *C)]

def render_piece(tag, f0, f1, res, square, out):
    cmd = [PY, os.path.join(HERE, "render.py"), out, "--audio", "", "--res", str(res),
           "--start", f"{f0 / FPS:.6f}", "--dur", f"{(f1 - f0) / FPS:.6f}", "--crf", "18"]
    if square:
        cmd.append("--square")
    subprocess.run(cmd, check=True)

def cut(res):
    tmp = os.path.join(RENDERS, "cut"); os.makedirs(tmp, exist_ok=True)
    ps = pieces()
    pos = 0.0
    print("splice map (cut time <- source time):")
    for tag, f0, f1 in ps:
        print(f"  {tag}: {pos:7.3f}-{pos + (f1 - f0) / FPS:7.3f} s  <-  {f0 / FPS:7.3f}-{f1 / FPS:7.3f} s")
        pos += (f1 - f0) / FPS
    print(f"  total {pos:.3f} s")
    vids = []
    for tag, f0, f1 in ps:
        v = os.path.join(tmp, f"{tag}.mp4")
        render_piece(tag, f0, f1, res, True, v)
        vids.append(v)
    # audio: the same frame-exact spans, 10 ms fades at each edge, concatenated
    parts, labels = [], []
    for i, (tag, f0, f1) in enumerate(ps):
        a, d = f0 / FPS, (f1 - f0) / FPS
        parts.append(f"[1:a]atrim=start={a:.6f}:duration={d:.6f},asetpts=PTS-STARTPTS,"
                     f"afade=t=in:d=0.01,afade=t=out:st={d - 0.01:.6f}:d=0.01[a{i}]")
        labels.append(f"[a{i}]")
    fc = ";".join(parts) + ";" + "".join(labels) + f"concat=n={len(ps)}:v=0:a=1[aout]"
    lst = os.path.join(tmp, "list.txt")
    open(lst, "w").write("".join(f"file '{v}'\n" for v in vids))
    out = os.path.join(RENDERS, "abstrakt_deck_promo_60s_square.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-i", AUDIO,
                    "-filter_complex", fc, "-map", "0:v", "-map", "[aout]",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
                    "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
                    "-c:a", "aac", "-b:a", "320k", "-movflags", "+faststart", out], check=True)
    print("wrote", out)

def loop(res):
    b, S = beats(), sections()
    f0 = beat_frame(b, S["title"]["start"]); f1 = beat_frame(b, S["title"]["start"], 8)   # 2 bars
    mp4 = os.path.join(RENDERS, "abstrakt_deck_title_loop.mp4")
    render_piece("loop", f0, f1, res, True, mp4)
    gif = os.path.join(RENDERS, "abstrakt_deck_title_loop.gif")
    vf = "fps=15,scale=600:600:flags=lanczos,split[a][b];[a]palettegen=max_colors=192:stats_mode=diff[p];[b][p]paletteuse=dither=sierra2_4a"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", mp4, "-filter_complex", vf, "-loop", "0", gif], check=True)
    print(f"loop {f0 / FPS:.3f}-{f1 / FPS:.3f} s ({(f1 - f0) / FPS:.3f} s); wrote {mp4} and {gif}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=("cut", "loop", "map"))
    ap.add_argument("--res", type=int, default=1080)
    a = ap.parse_args()
    if a.what == "cut":
        cut(a.res)
    elif a.what == "loop":
        loop(a.res)
    else:
        for tag, f0, f1 in pieces():
            print(tag, f0, f1, f"{f0 / FPS:.3f}-{f1 / FPS:.3f}")
