"""Sync: the section map and the music-driven uniforms, at 30 fps video frames.

Rewritten for this film from lightholesdemo's sync.py (same idea: every per-frame value is a
function of t alone, smoothed so nothing jumps). Inputs: data/beats.json (the 138 bpm grid
and downbeats), data/sections.json (sections and hits), cache/features.json (analyze.py), and
a 16-band log spectrum computed here and cached as cache/spectrum.npy.

Per frame:
    beat, bar        beat index and phase (0..1) on the full grid; bar phase from downbeats
    pulse            1 on each beat, decaying (BEAT_DECAY)
    kick             1 on strong low-band onsets, decaying (KICK_DECAY)
    rms, low, mid, high   analyze.py's normalised levels
    spec[16]         log-spaced bands 40 Hz-12 kHz, each normalised to its 5th-98th
                     percentile over the song, fast attack / slow release
"""
import json, os, subprocess
import numpy as np

FPS = 30
HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "cache")
DATA = os.path.join(HERE, "data")
AUDIO = os.path.join(HERE, "audio", "abstrakt_deck.wav")
BEAT_DECAY = 0.11                # s
KICK_DECAY = 0.16                # s
KICK_MIN = 0.45                  # onset strength x low band that counts as a kick
N_BANDS = 16
SPEC_SR, SPEC_WIN = 22050, 2048  # hop 735 = one video frame
ATTACK, RELEASE = 0.7, 0.18      # per-frame smoothing toward a rise / a fall

def spectrum(path=AUDIO, cache=os.path.join(CACHE, "spectrum.npy")):
    if os.path.exists(cache) and os.path.getmtime(cache) > os.path.getmtime(path):
        return np.load(cache)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1",
                          "-ar", str(SPEC_SR), "-"], capture_output=True, check=True).stdout
    y = np.frombuffer(raw, "f4")
    hop = SPEC_SR // FPS
    n = int(np.ceil(len(y) / hop))
    y = np.pad(y, (SPEC_WIN // 2, SPEC_WIN))
    win = np.hanning(SPEC_WIN).astype("f4")
    idx = np.arange(n)[:, None] * hop + np.arange(SPEC_WIN)[None]
    mag = np.abs(np.fft.rfft(y[idx] * win, axis=1))
    freqs = np.fft.rfftfreq(SPEC_WIN, 1 / SPEC_SR)
    edges = np.geomspace(40, 12000, N_BANDS + 1)
    bands = np.stack([np.log1p((mag[:, (freqs >= a) & (freqs < b)] ** 2).sum(1))
                      for a, b in zip(edges[:-1], edges[1:])], 1)
    lo, hi = np.percentile(bands, 5, 0), np.percentile(bands, 98, 0)
    bands = np.clip((bands - lo) / (hi - lo + 1e-9), 0, 1)
    out = np.zeros_like(bands)
    for i in range(1, n):
        d = bands[i] - out[i - 1]
        out[i] = out[i - 1] + np.where(d > 0, ATTACK, RELEASE) * d
    os.makedirs(CACHE, exist_ok=True)
    np.save(cache, out.astype("f4"))
    return out.astype("f4")

class Sync:
    def __init__(self):
        f = json.load(open(os.path.join(CACHE, "features.json")))
        b = json.load(open(os.path.join(DATA, "beats.json")))
        s = json.load(open(os.path.join(DATA, "sections.json")))
        self.ffps = f["fps"]
        self.duration = f["duration"]
        self.n_frames = int(round(self.duration * FPS))
        self.period = b["period"]
        self.beats = np.array(b["beats"])
        self.downbeats = np.array(b["downbeats"])
        for k in ("rms", "low", "mid", "high", "onset_strength"):
            setattr(self, k, np.array(f[k], "f4"))
        # kicks: the beats with bass under them (the low band's peak within 50 ms of the beat);
        # spectral-flux onsets alone find only 37 in the whole song, none in the title hit
        w = int(0.05 * self.ffps)
        lowpk = np.array([self.low[max(0, int(t * self.ffps) - w):int(t * self.ffps) + w + 1].max()
                          for t in self.beats])
        self.kick_t = self.beats[lowpk >= KICK_MIN]
        self.sections = s["sections"]
        self.by_name = {x["name"]: x for x in self.sections}
        self.hits = {h["name"]: h["t"] for h in s["hits"]}
        self.hits_raw = {h["name"]: h["raw"] for h in s["hits"]}
        self.spec = spectrum()

    def section(self, t):
        for x in self.sections:
            if x["start"] <= t < x["end"]:
                return x
        return self.sections[-1]

    def feat(self, arr, t):
        x = t * self.ffps
        i = int(np.clip(np.floor(x), 0, len(arr) - 2)); a = x - i
        return float(arr[i] * (1 - a) + arr[i + 1] * a)

    def grid(self, t, grid):
        """(index, phase) on a grid of times, extrapolated beyond both ends."""
        if t < grid[0]:
            p = (t - grid[0]) / (grid[1] - grid[0])
            return int(np.floor(p)), p - np.floor(p)
        k = int(np.searchsorted(grid, t, side="right")) - 1
        if k >= len(grid) - 1:
            p = (t - grid[-1]) / (grid[-1] - grid[-2])
            return k + int(np.floor(p)), p - np.floor(p)
        return k, (t - grid[k]) / (grid[k + 1] - grid[k])

    @staticmethod
    def since(t, times):
        k = np.searchsorted(times, t, side="right") - 1
        return t - times[k] if k >= 0 else 1e9

    def uniforms(self, t):
        bi, bp = self.grid(t, self.beats)
        di, dp = self.grid(t, self.downbeats)
        fi = int(np.clip(round(t * FPS), 0, len(self.spec) - 1))
        return {"time": t, "beat": float(bi), "beat_ph": float(bp), "bar": float(di), "bar_ph": float(dp),
                "pulse": float(np.exp(-self.since(t, self.beats) / BEAT_DECAY)),
                "kick": float(np.exp(-self.since(t, self.kick_t) / KICK_DECAY)),
                "rms": self.feat(self.rms, t), "low": self.feat(self.low, t),
                "mid": self.feat(self.mid, t), "high": self.feat(self.high, t),
                "spec": self.spec[fi]}
