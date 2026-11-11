#!/usr/bin/env python3
"""sections.py — cache/features.json -> data/beats.json + data/sections.json, and print the map.

    python sections.py

analyze.py tracks this song at half time (69 bpm; its autocorrelation's top lag is 138.5, and
onsets fall as often on the half-beats as on the tracked beats), so the full beat grid here is
the tracked beats plus their midpoints: 138.1 bpm, 0.4345 s a beat. Downbeats: the phase of 4
with the most kick (onset strength x low band), which is phase 0, i.e. the first tracked beat.

Section starts (RAW) come from the features: novelty peaks over the beat-synchronous
self-similarity, band-energy steps, the mid/side voice-band profile, and which blocks repeat
each other's chroma. Each is snapped to the nearest beat (every cut and hit lands on a beat);
"why" keeps the reason. No transcript was available (faster-whisper not installed), so the
boundaries are signal-only until the author confirms them (CONFIRMED below).
"""
import json, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
FEATURES = os.path.join(HERE, "cache", "features.json")
DATA = os.path.join(HERE, "data")
DOWNBEAT_PHASE = 0
CONFIRMED = "vocal start 0:43.57 and chorus 2 at 2:50.20 confirmed by the author by ear, 2026-11-11"

# (name, role, start s, why)
RAW = [
    ("intro",     "intro",   0.0,    "pads + voice, no drums: 'ONOJK123 Art presents / Abstrakt... Deck!'"),
    ("title",     "title",   28.77,  "novelty peak 0.44; drums and bass enter (low 0.2 -> 0.41, high -> 0.48): instrumental title hit"),
    ("verse1",    "verse",   43.57,  "novelty 0.51; highs drop (0.48 -> 0.17) and the centred voice band jumps (M-S 4.8 -> 10.8): vocals start (confirmed by ear)"),
    ("breakdown", "verse",   92.57,  "novelty 0.37; bass drops out (low 0.14), centred voice-band peak: pre-chorus"),
    ("chorus1",   "chorus",  98.67,  "novelty 0.36; biggest lift so far (rms 0.34 -> 0.59, high 0.72)"),
    ("break",     "verse",   134.03, "novelty 0.41; side channel collapses (near-mono at 136 s); chroma matches the intro (0.85)"),
    ("verse2",    "verse",   139.70, "novelty 0.59; full band back"),
    ("chorus2",   "chorus",  170.20, "novelty 0.25; loudest block (rms 0.71-0.79); chroma matches 28.8 block (0.62) and verse 2 (0.54)"),
    ("outro",     "outro",   185.00, "novelty 1.00 (strongest): highs drop out (0.75 -> 0.19), bass rides to the end"),
]
# sub-boundaries inside sections: hits, not cuts
HITS = [
    ("type1",       1.07,  "first downbeat: type ONOJK123"),
    ("type2",       7.50,  "centred voice-band phrase 7.5-13.5 s: type ART PRESENTS"),
    ("gap",         13.75, "hard silence (-inf in the voice band for one quarter-second): cut to black"),
    ("tease",       17.50, "centred phrase 17.5-18.75 s: ABSTRAKT flickers in"),
    ("build",       23.50, "mid band steps up (40 -> 48 dB): starfield warps toward the hit"),
    ("title_hit",   28.77, "drums enter: the ABSTRAKT DECK slam"),
    ("shout",       35.00, "near-mono burst 35.0-36.25 s (M-S 16 dB): extra flash"),
    ("verse1_build", 71.53, "novelty 0.25: mids and highs climb toward the chorus"),
    ("music_end",   191.6, "level falls under -26 dBFS (192-194 s): the tail"),
]

def build():
    f = json.load(open(FEATURES))
    hb = np.array(f["beats"])
    beats = np.sort(np.concatenate([hb, (hb[:-1] + hb[1:]) / 2]))
    period = float(np.diff(beats).mean())
    down = beats[DOWNBEAT_PHASE::4]

    def snap(t):
        if t <= 0:
            return 0.0
        return round(float(beats[np.argmin(np.abs(beats - t))]), 3)

    def bar_of(t):
        return round(float((t - down[0]) / (4 * period)) + 1, 2)

    secs = []
    for name, role, t, why in RAW:
        s = snap(t)
        secs.append({"name": name, "role": role, "start": s, "raw": t, "bar": bar_of(s), "why": why})
    for i, s in enumerate(secs):
        s["end"] = secs[i + 1]["start"] if i + 1 < len(secs) else round(f["duration"], 3)
    hits = [{"name": n, "t": snap(t), "raw": t, "why": w} for n, t, w in HITS]

    os.makedirs(DATA, exist_ok=True)
    json.dump({"source": "audio/abstrakt_deck.wav (195.520 s, 48 kHz, stereo)",
               "tempo": round(60 / period, 2), "period": round(period, 4),
               "tracked_tempo": f["tempo"], "note": "full grid = tracked half-time beats + midpoints",
               "downbeat_phase": DOWNBEAT_PHASE,
               "beats": beats.round(3).tolist(), "downbeats": down.round(3).tolist()},
              open(os.path.join(DATA, "beats.json"), "w"), indent=1)
    json.dump({"duration": round(f["duration"], 3), "confirmed": CONFIRMED,
               "sections": secs, "hits": hits},
              open(os.path.join(DATA, "sections.json"), "w"), indent=1)
    return secs, hits, period

def mmss(t):
    return f"{int(t // 60)}:{t % 60:05.2f}"

if __name__ == "__main__":
    secs, hits, period = build()
    print(f"tempo {60 / period:.2f} bpm, beat {period:.4f} s, bar {4 * period:.3f} s\n")
    for s in secs:
        L = s["end"] - s["start"]
        print(f"{s['name']:10s} {mmss(s['start']):>8s} - {mmss(s['end']):>8s}  {L:6.2f}s "
              f"{L / (4 * period):5.1f} bars  (bar {s['bar']:.2f})  {s['why']}")
    for h in hits:
        print(f"  hit {h['name']:13s} {mmss(h['t'])}  {h['why']}")
