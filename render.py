#!/usr/bin/env python3
"""Abstrakt Deck promo — rendered offline.

    python render.py renders/preview.mp4 --start 0 --dur 53 --res 480 [--preset veryfast]
    python render.py renders/title.mp4 --section title --res 480
    python render.py renders/abstrakt_deck_1080p.mp4 --full
    python render.py renders/square.mp4 --full --square
    python render.py - --still 3.2 --still 30.0            # PNGs into renders/

Adapted from lightholesdemo's render.py (itself from tentimesdemo / laser-beam-demo): the
EGL standalone context, quarter-size two-pass bloom, ffmpeg rgb24 pipe and audio mux.
Deterministic: time = frame / 30, never the wall clock; grain and glitch are hashes of the
pixel and frame number.

Changed for this film: a feedback buffer (the previous frame's scene, for trails and the
black-hole feedback), a CRT post pass (scanlines, chromatic aberration, slice glitch, white
flash), text as textures from ffmpeg drawtext (pixel-chunky cracktro type sampled NEAREST,
the logo LINEAR), and scenes chosen by section. Layouts keep text within |x| < 0.95 so the
1080x1080 square cut frames the same scenes without re-layout.
"""
import argparse, os, subprocess, sys, tempfile
import numpy as np
import moderngl
from sync import Sync, FPS

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIO = os.path.join(HERE, "audio", "abstrakt_deck.wav")
FONT_PIXEL = "/usr/share/fonts/fonts-go/Go-Mono-Bold.ttf"          # drawn small, sampled NEAREST
FONT_LOGO = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
SEED = 0xAD5C
WARMUP = 45                      # frames rendered before --start so feedback trails settle

FONT_URL = "/usr/share/fonts/fonts-go/Go-Mono-Bold.ttf"            # drawn large, sampled LINEAR

# The timeline: (section, bars after its start, scene, footage slot). Bars count on the beat
# grid from the section's first beat (4 beats a bar), so every cut lands on a beat. A section
# with no entry shows the labelled fallback.
TIMELINE = [
    ("intro",     0,  "intro",     None),
    ("title",     0,  "title",     None),
    ("verse1",    0,  "hexa",      None),
    ("verse1",    8,  "kaleido",   "kaleido"),
    ("verse1",    16, "blackhole", "blackhole"),
    ("breakdown", 0,  "scanline",  None),
    ("chorus1",   0,  "chorus",    None),
    ("break",     0,  "crack",     None),
    ("verse2",    0,  "rust",      None),
    ("verse2",    6,  "grid",      "grid"),
    ("verse2",    12, "record",    "record"),
    ("chorus2",   0,  "chorus",    None),
    ("outro",     0,  "outro",     None),
]
NOTE_SCENES = {"kaleido", "blackhole", "grid", "record", "outro"}   # show the tribute note
URL_BARS_CHORUS1 = 12            # chorus 1 adds the Store URL for its last ~8 bars (the 60 s cut ends there)
FOOT_EXT = (".mp4", ".mov", ".mkv", ".webm")
GREETZ = "GREETZ: ALL SCENERS * RUST & WGPU CREWS * VJS & NOISEMAKERS * AND YOU!"

TEXTS = {   # name: (text, font, size px, pixel)
    "onojk":     ("ONOJK123", FONT_PIXEL, 18, True),
    "presents":  ("ART PRESENTS", FONT_PIXEL, 18, True),
    "abstrakt":  ("ABSTRAKT", FONT_LOGO, 220, False),
    "deck":      ("DECK", FONT_LOGO, 220, False),
    "store":     ("NOW ON THE MICROSOFT STORE", FONT_PIXEL, 18, True),
    "reactive":  ("AUDIO-REACTIVE", FONT_PIXEL, 18, True),
    "dance":     ("VISUALS THAT DANCE TO YOUR MUSIC", FONT_PIXEL, 18, True),
    "todo":      ("SCENE TO COME", FONT_PIXEL, 18, True),
    "tribute":   ("DEMOSCENE TRIBUTE - NOT ACTUAL APP FOOTAGE", FONT_PIXEL, 18, True),
    "kaleido":   ("KALEIDOSCOPES", FONT_PIXEL, 18, True),
    "blackhole": ("BLACK-HOLE FEEDBACK", FONT_PIXEL, 18, True),
    "grid":      ("MULTI-PANEL GRIDS", FONT_PIXEL, 18, True),
    "builtin":   ("BUILT IN", FONT_PIXEL, 18, True),
    "rustwgpu":  ("RUST + WGPU", FONT_LOGO, 220, False),
    "record":    ("RECORD STRAIGHT TO VIDEO", FONT_PIXEL, 18, True),
    "f12":       ("PRESS F12", FONT_PIXEL, 18, True),
    "rec":       ("REC", FONT_PIXEL, 18, True),
    "nowonthe":  ("NOW ON THE", FONT_PIXEL, 18, True),
    "msstore":   ("MICROSOFT STORE", FONT_LOGO, 220, False),
    "url":       ("apps.microsoft.com/detail/9NR8XFDVFN48", FONT_URL, 120, False),
    "linux":     ("ALSO ON LINUX: SNAP STORE & PPA", FONT_PIXEL, 18, True),
    "platforms": ("SNAP STORE * PPA * WINDOWS", FONT_PIXEL, 18, True),
    "crack":     ("ABSTRAKT DECK", FONT_PIXEL, 18, True),
    "greetz":    (GREETZ, FONT_PIXEL, 18, True),
}

VERT = """
#version 330
in vec2 pos;
out vec2 uv;
void main() { uv = pos * 0.5 + 0.5; gl_Position = vec4(pos, 0.0, 1.0); }
"""

HEAD = """
#version 330
in vec2 uv;
out vec4 frag;
uniform vec2 res;
uniform int frame, seed;
uniform float time, lt, beat, beat_ph, bar, bar_ph, pulse, kick, rms, low, mid, high;
uniform float spec[16];
uniform sampler2D prev;
const float PI = 3.14159265, TAU = 6.2831853;
vec2 P() { vec2 p = (uv - 0.5) * 2.0; p.x *= res.x / res.y; return p; }
float hash11(float x) { return fract(sin(x * 127.1 + float(seed) * 0.013) * 43758.5453); }
float hash21(vec2 v) { return fract(sin(dot(v, vec2(127.1, 311.7)) + float(seed) * 0.017) * 43758.5453); }
vec2 hash22(vec2 v) { return vec2(hash21(v), hash21(v + 19.19)); }
vec3 hsv(float h, float s, float v) {
    vec3 k = clamp(abs(mod(h * 6.0 + vec3(0, 4, 2), 6.0) - 3.0) - 1.0, 0.0, 1.0);
    return v * mix(vec3(1.0), k, s);
}
mat2 rot(float a) { float c = cos(a), s = sin(a); return mat2(c, -s, s, c); }
// a text texture placed with its centre at c, height h (shrunk so the width stays <= mw);
// returns (coverage, local x 0..1, local y 0..1)
vec3 textq(sampler2D T, vec2 p, vec2 c, float h, float mw) {
    vec2 ts = vec2(textureSize(T, 0));
    float w = h * ts.x / ts.y;
    if (w > mw) { h *= mw / w; w = mw; }
    vec2 q = (p - c) / vec2(w, h) + 0.5;
    if (q.x < 0.0 || q.y < 0.0 || q.x > 1.0 || q.y > 1.0) return vec3(0.0, q);
    return vec3(texture(T, q).r, q);
}
float text(sampler2D T, vec2 p, vec2 c, float h, float mw) { return textq(T, p, c, h, mw).x; }
// typed reveal: the first `r` (0..1) of a monospace string, with a block cursor after it
float typed(sampler2D T, vec2 p, vec2 c, float h, float mw, float r, float n_chars, float cursor) {
    vec3 a = textq(T, p, c, h, mw);
    float shown = a.x * step(a.y, r);
    float cur = step(r, a.y) * step(a.y, r + 1.0 / n_chars) * step(0.08, a.z) * step(a.z, 0.92);
    return max(shown, cursor * cur * step(0.0, r) * step(r, 1.0));
}
// classic copper raster bar: hue-coloured with a white-hot core
vec3 copper(float y, float yc, float half_h, float hue) {
    float d = abs(y - yc) / half_h;
    if (d > 1.0) return vec3(0.0);
    float pr = 1.0 - d * d;
    return mix(hsv(hue, 0.85, 1.0) * pr, vec3(1.0), pow(pr, 8.0));
}
float band(float k) {
    int i = int(clamp(k, 0.0, 15.0));
    int j = min(i + 1, 15);
    return mix(spec[i], spec[j], fract(clamp(k, 0.0, 15.0)));
}
// 3D starfield; warp stretches the stars along their direction from the centre
vec3 stars(vec2 p, float spd, float warp) {
    vec3 c = vec3(0.0);
    for (int l = 0; l < 7; l++) {
        float fl = float(l);
        float z = fract(fl / 7.0 - time * spd);
        float scale = mix(0.4, 9.0, z);
        vec2 q = p * scale + fl * 17.3;
        vec2 id = floor(q), f = fract(q) - 0.5;
        vec2 o = hash22(id + fl * 3.1) - 0.5;
        if (hash21(id + fl) > 0.55) continue;
        vec2 d = f - o * 0.8;
        vec2 dir = normalize((id + 0.5 + o * 0.8 - fl * 17.3) / scale + 1e-4);
        float along = dot(d, dir), across = dot(d, vec2(-dir.y, dir.x));
        along /= 1.0 + warp * 22.0 * (1.0 - z);
        float r = length(vec2(along, across));
        float size = 0.03 + 0.05 * (1.0 - z);
        float b = smoothstep(size, 0.0, r) * smoothstep(1.0, 0.6, z) * (1.0 - z * 0.7);
        c += b * mix(vec3(0.7, 0.85, 1.0), hsv(hash21(id), 0.5, 1.0), 0.35);
    }
    return c;
}
// App footage: st in 0..1 (mirrored outside). With no clip in footage/ yet, a stand-in in
// the app's own look (rainbow rings inside a turning polygon, reacting to the spectrum).
uniform sampler2D t_foot;
uniform float has_foot, foot_aspect;
vec3 foot(vec2 st) {
    st = 1.0 - abs(1.0 - mod(st, 2.0));
    if (has_foot > 0.5) return texture(t_foot, st).rgb;
    vec2 p = (st - 0.5) * 2.0 * vec2(foot_aspect, 1.0);
    float n = 6.0, a = atan(p.y, p.x) + time * 0.25;
    float r = length(p) * cos(PI / n) / cos(mod(a, TAU / n) - PI / n);
    float b = band(r * 9.0);
    float ring = r * 9.0 / (0.85 + 0.25 * low);
    vec3 c = hsv(floor(ring) / 9.0 * 1.3 - time * 0.35, 0.9, 1.0);
    c *= 0.75 + 0.25 * smoothstep(0.0, 0.15, fract(ring));      // a dark seam between rings
    return c * (0.4 + 0.7 * b);
}
// the honest note: the stand-ins are a tribute, not screen captures. Small pixel type in the
// bottom-right corner, steady and dim, on a faint shade so it reads over any colour; it sits
// below every caption band (lowest caption edge -0.89) and never shares a scene with the URL.
uniform sampler2D t_tribute;
vec3 tribute(vec3 col, vec2 p, float on) {
    vec2 ts = vec2(textureSize(t_tribute, 0));
    float h = 0.05;
    float w = h * ts.x / ts.y;
    vec2 c = vec2(res.x / res.y - 0.04 - w * 0.5, -0.94);
    vec2 d = abs(p - c) - vec2(w * 0.5 + 0.015, h * 0.5 + 0.012);
    float shade = step(max(d.x, d.y), 0.0);
    float a = text(t_tribute, p, c, h, 2.0);
    return mix(col, vec3(0.0), 0.6 * shade * on) + vec3(0.78) * a * on;
}
"""

FALLBACK = """
uniform sampler2D t_todo;
uniform float sec_id;
void main() {
    vec2 p = P();
    vec3 c = vec3(0.02, 0.02, 0.05) + 0.03 * hsv(sec_id * 0.13, 0.8, 1.0) * (0.5 + 0.5 * sin(p.y * 40.0));
    c += vec3(0.7) * text(t_todo, p, vec2(0.0), 0.12, 1.8);
    frag = vec4(c, 1.0);
}
"""

DOWN = """
#version 330
in vec2 uv;
out vec4 frag;
uniform sampler2D src;
void main() { frag = vec4(texture(src, uv).rgb, 1.0); }
"""

BLUR = """
#version 330
in vec2 uv;
out vec4 frag;
uniform sampler2D src;
uniform vec2 dir;
const float W[5] = float[5](0.227027, 0.1945946, 0.1216216, 0.054054, 0.016216);
void main() {
    vec3 c = texture(src, uv).rgb * W[0];
    for (int i = 1; i < 5; i++) {
        c += texture(src, uv + dir * float(i) * 1.5).rgb * W[i];
        c += texture(src, uv - dir * float(i) * 1.5).rgb * W[i];
    }
    frag = vec4(c, 1.0);
}
"""

POST = """
#version 330
in vec2 uv;
out vec4 frag;
uniform sampler2D scene, bloom;
uniform vec2 res;
uniform float bloom_gain, glitch, aberr, flash, fade, scan, shake_x, shake_y, note_on;
uniform vec4 note_box;
uniform int frame, seed;
uint hash(uint x) { x ^= x >> 16; x *= 0x7feb352du; x ^= x >> 15; x *= 0x846ca68bu; x ^= x >> 16; return x; }
float h01(uint x) { return float(hash(x + uint(seed))) / 4294967295.0; }
void main() {
    vec2 u = uv + vec2(shake_x, shake_y);
    // slice glitch: bands of rows jump sideways, re-rolled every 2 frames
    uint fr = uint(frame / 2);
    float band = floor(u.y * 36.0);
    float on = step(1.0 - 0.55 * glitch, h01(uint(band) * 7919u + fr * 104729u));
    vec2 ug = u + vec2(on * glitch * (h01(uint(band) * 31u + fr * 613u) - 0.5) * 0.18, 0.0);
    float ab = aberr + glitch * 0.012;
    // the tribute note is exempt from the glitch, like the Store URL: no slice shift inside its
    // box, and no shifted slice outside it may sample from inside it (that is what doubled it)
    vec4 nb = note_box;
    bool in_note = note_on > 0.5 && u.x > nb.x && u.x < nb.z && u.y > nb.y && u.y < nb.w;
    bool from_note = note_on > 0.5 && ug.x > nb.x && ug.x < nb.z && ug.y > nb.y && ug.y < nb.w;
    if (in_note || from_note) { ab = aberr; } else { u = ug; }
    vec3 c;
    c.r = texture(scene, u + vec2(ab, 0.0)).r;
    c.g = texture(scene, u).g;
    c.b = texture(scene, u - vec2(ab, 0.0)).b;
    c = max(c, 0.0) + bloom_gain * texture(bloom, u).rgb;
    c = 1.0 - exp(-c * 1.2);                                   // soft knee
    c *= 1.0 - scan * 0.22 * (0.5 + 0.5 * cos(uv.y * 270.0 * 6.2831853));   // 270 CRT lines
    vec2 v = uv - 0.5;
    c *= clamp(1.0 - dot(v, v) * 0.7, 0.0, 1.0);               // vignette
    uint px = uint(gl_FragCoord.x) + 7919u * uint(gl_FragCoord.y) + 104729u * uint(frame);
    c += (h01(px) - 0.5) * 0.035 * (0.15 + c);                 // grain
    c = mix(c, vec3(1.0), clamp(flash, 0.0, 1.0));
    frag = vec4(clamp(c * fade, 0.0, 1.0), 1.0);
}
"""

def text_image(text, font, size, pad=0.06):
    """White text on black from ffmpeg drawtext, cropped to its ink plus a margin, 8-bit gray,
    top row first."""
    w, h = int(size * (len(text) * 0.9 + 2)), int(size * 2)
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as fh:
        fh.write(text)
    try:
        vf = (f"drawtext=fontfile={font}:textfile={fh.name}:fontsize={size}:fontcolor=white:"
              f"x=(w-text_w)/2:y=(h-text_h)/2:expansion=none")
        raw = subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", f"color=c=black:s={w}x{h}",
                              "-frames:v", "1", "-vf", vf, "-f", "rawvideo", "-pix_fmt", "gray", "-"],
                             capture_output=True, check=True).stdout
    finally:
        os.unlink(fh.name)
    img = np.frombuffer(raw, np.uint8).reshape(h, w)
    ys, xs = np.nonzero(img > 8)
    m = int(np.ceil(pad * (ys.max() - ys.min())))
    return np.ascontiguousarray(img[max(0, ys.min() - m):ys.max() + m + 1, max(0, xs.min() - m):xs.max() + m + 1])

class Renderer:
    def __init__(self, W, H):
        self.W, self.H = W, H
        self.ctx = moderngl.create_standalone_context(backend="egl")
        self.quad = self.ctx.buffer(np.array([-1, -1, 1, -1, -1, 1, 1, 1], "f4").tobytes())
        def target(w, h):
            tx = self.ctx.texture((w, h), 4, dtype="f2")
            tx.filter = (moderngl.LINEAR, moderngl.LINEAR)
            tx.repeat_x = tx.repeat_y = False
            return tx, self.ctx.framebuffer([tx])
        self.scene, self.scene_fbo = target(W, H)
        self.prev, self.prev_fbo = target(W, H)
        self.bw, self.bh = W // 4, H // 4
        self.b1, self.b1_fbo = target(self.bw, self.bh)
        self.b2, self.b2_fbo = target(self.bw, self.bh)
        self.out = self.ctx.renderbuffer((W, H), 3)
        self.out_fbo = self.ctx.framebuffer([self.out])
        self.down, self.blur, self.post = (self.program(s) for s in (DOWN, BLUR, POST))
        self.scenes, self.tex = {}, {}

    def add_texture(self, name, img, nearest=False):
        h, w = img.shape
        tx = self.ctx.texture((w, h), 1, np.ascontiguousarray(img[::-1]).tobytes())
        tx.filter = (moderngl.NEAREST, moderngl.NEAREST) if nearest else (moderngl.LINEAR, moderngl.LINEAR)
        tx.repeat_x = tx.repeat_y = False
        self.tex[name] = tx

    def set_foot(self, arr):
        """The current app-footage frame (h, w, 3) uint8, top row first."""
        h, w, _ = arr.shape
        tx = self.tex.get("foot")
        if tx is None or tx.size != (w, h):
            tx = self.ctx.texture((w, h), 3)
            tx.filter = (moderngl.LINEAR, moderngl.LINEAR)
            self.tex["foot"] = tx
        tx.write(np.ascontiguousarray(arr[::-1]).tobytes())

    def program(self, frag):
        prog = self.ctx.program(vertex_shader=VERT, fragment_shader=frag)
        return prog, self.ctx.vertex_array(prog, [(self.quad, "2f", "pos")])

    def scene_prog(self, name):
        if name not in self.scenes:
            path = os.path.join(HERE, "fx", name + ".glsl")
            src = open(path).read() if os.path.exists(path) else FALLBACK
            self.scenes[name] = self.program(HEAD + src)
        return self.scenes[name]

    @staticmethod
    def set(prog, uniforms):
        for k, v in uniforms.items():
            if k in prog:
                if isinstance(v, np.ndarray):
                    prog[k].write(np.ascontiguousarray(v, "f4").tobytes())
                else:
                    prog[k].value = v

    def frame(self, name, u, post, frame_no):
        prog, vao = self.scene_prog(name)
        self.set(prog, dict(u, res=(self.W, self.H), seed=SEED, frame=frame_no))
        self.prev.use(0)
        if "prev" in prog:
            prog["prev"].value = 0
        for unit, (k, tx) in enumerate(self.tex.items(), start=1):
            if "t_" + k in prog:
                tx.use(unit); prog["t_" + k].value = unit
        self.scene_fbo.use(); vao.render(moderngl.TRIANGLE_STRIP)
        self.ctx.copy_framebuffer(self.prev_fbo, self.scene_fbo)        # feedback for next frame
        p, v = self.down
        self.scene.use(0); p["src"].value = 0
        self.b1_fbo.use(); v.render(moderngl.TRIANGLE_STRIP)
        p, v = self.blur
        p["src"].value = 0
        for _ in range(2):
            self.b1.use(0); p["dir"].value = (1 / self.bw, 0)
            self.b2_fbo.use(); v.render(moderngl.TRIANGLE_STRIP)
            self.b2.use(0); p["dir"].value = (0, 1 / self.bh)
            self.b1_fbo.use(); v.render(moderngl.TRIANGLE_STRIP)
        p, v = self.post
        self.scene.use(0); self.b1.use(1)
        p["scene"].value, p["bloom"].value = 0, 1
        self.set(p, dict(post, res=(self.W, self.H), frame=frame_no, seed=SEED))
        self.out_fbo.use(); v.render(moderngl.TRIANGLE_STRIP)
        return self.out_fbo.read(components=3)                 # bottom row first

def ffmpeg_writer(path, W, H, start, dur, audio, crf, preset):
    cmd = ["ffmpeg", "-v", "error", "-y",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-"]
    if audio:
        cmd += ["-ss", f"{start:.6f}", "-t", f"{dur:.6f}", "-i", audio]
    cmd += ["-vf", "vflip,format=yuv420p", "-c:v", "libx264", "-preset", preset, "-crf", str(crf),
            "-pix_fmt", "yuv420p", "-colorspace", "bt709", "-color_primaries", "bt709",
            "-color_trc", "bt709", "-color_range", "tv"]
    if audio:
        cmd += ["-af", "apad", "-c:a", "aac", "-b:a", "320k", "-shortest"]
    cmd += ["-movflags", "+faststart", path]
    return subprocess.Popen(cmd, stdin=subprocess.PIPE)

def save_png(buf, W, H, path):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                    "-s", f"{W}x{H}", "-i", "-", "-vf", "vflip", path], input=buf, check=True)

def ramp(t, a, b):
    """0 before a, 1 after b, smooth between."""
    if b <= a:
        return float(t >= a)
    x = min(1.0, max(0.0, (t - a) / (b - a)))
    return x * x * (3 - 2 * x)

def decay(t, t0, tau):
    return float(np.exp(-(t - t0) / tau)) if t >= t0 else 0.0

class Footage:
    """App recordings in footage/<slot>.mp4 (git-ignored), decoded on demand to a fixed-size
    RGB frame (scaled to cover, centre-cropped) at 30 fps and looped. Frames are read
    sequentially from one ffmpeg process; a jump restarts it at the wanted frame."""
    def __init__(self, W, H):
        self.W, self.H = W, H
        self.proc = self.key = None
        self.next, self.last = 0, None
        self.n = {}

    def path(self, slot):
        for ext in FOOT_EXT:
            p = os.path.join(HERE, "footage", slot + ext)
            if os.path.exists(p):
                return p
        return None

    def frames(self, p):
        if p not in self.n:
            d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                      "-of", "csv=p=0", p], capture_output=True, text=True).stdout)
            self.n[p] = max(1, int(d * FPS) - 1)
        return self.n[p]

    def frame(self, slot, idx):
        p = self.path(slot)
        if p is None:
            return None
        idx %= self.frames(p)
        if self.key == p and idx == self.next - 1 and self.last is not None:
            return self.last
        if self.key != p or idx != self.next:
            if self.proc:
                self.proc.kill(); self.proc.wait()
            vf = (f"fps={FPS},scale={self.W}:{self.H}:force_original_aspect_ratio=increase,"
                  f"crop={self.W}:{self.H}")
            self.proc = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{idx / FPS:.4f}", "-i", p,
                                          "-an", "-vf", vf, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                                         stdout=subprocess.PIPE)
            self.key, self.next = p, idx
        n = self.W * self.H * 3
        raw = self.proc.stdout.read(n)
        if len(raw) < n:                                  # ran short of the probed length: loop
            self.key = None
            return self.frame(slot, 0)
        self.last = np.frombuffer(raw, np.uint8).reshape(self.H, self.W, 3)
        self.next = idx + 1
        return self.last

class Film:
    def __init__(self, W, H):
        self.sync = Sync()
        self.r = Renderer(W, H)
        for name, (text, font, size, pixel) in TEXTS.items():
            self.r.add_texture(name, text_image(text, font, size), nearest=pixel)
        self.n_chars = {k: float(len(v[0])) for k, v in TEXTS.items()}
        self.sec_index = {s["name"]: i for i, s in enumerate(self.sync.sections)}
        self.timeline(0.0)
        # the tribute note's box in uv (matches tribute() in HEAD: h 0.05, centre y -0.94,
        # right edge 0.04 in from the frame edge; plus the shade margin and a little more)
        th, tw = self.r.tex["tribute"].size[1], self.r.tex["tribute"].size[0]
        asp, h = W / H, 0.05
        w = h * tw / th
        x0, x1 = asp - 0.04 - w - 0.03, asp - 0.04 + 0.03
        y0, y1 = -0.94 - h / 2 - 0.03, -0.94 + h / 2 + 0.03
        self.note_box = (x0 / (2 * asp) + 0.5, y0 / 2 + 0.5, x1 / (2 * asp) + 0.5, y1 / 2 + 0.5)
        self.footage = Footage(*((640, 360) if H <= 480 else (1280, 720)))

    # --- per-scene uniforms: u is the shared sync dict, post the post-pass dict ---------
    def scene_intro(self, s, t, u, post):
        h, hr, bp = self.sync.hits, self.sync.hits_raw, self.sync.period
        u["r1"] = (t - h["type1"]) / (8 * bp)                        # ONOJK123: a char per beat
        u["r2"] = (t - h["type2"]) / (12 * bp / 2)                   # ART PRESENTS: per half beat
        u["fade_in"] = ramp(t, 0.0, h["type1"])
        u["tease"] = ramp(t, h["tease"], h["tease"] + 2 * bp)
        u["build"] = ramp(t, h["build"], h["title_hit"])
        u["bars_on"] = ramp(t, h["type1"], h["type1"] + 8 * bp)
        u["gap_after"] = decay(t, hr["gap"] + 0.25, 0.4)
        gap = hr["gap"] <= t < hr["gap"] + 0.25
        post["fade"] = 0.0 if gap else 1.0
        post["glitch"] = 0.6 * u["gap_after"] + 0.5 * u["tease"] * float(t < h["tease"] + 4 * bp) * \
            (0.4 + 0.6 * float(np.sin(t * 9) > 0.6)) + 0.6 * u["build"] ** 3
        post["flash"] = ramp(t, h["title_hit"] - bp, h["title_hit"]) ** 3 * 0.85
        post["aberr"] = 0.002 + 0.004 * u["build"]

    def scene_title(self, s, t, u, post):
        h, bp = self.sync.hits, self.sync.period
        lt = t - h["title_hit"]
        u["slam"] = decay(t, h["title_hit"], 0.09)
        u["sub_r"] = (lt - bp) / (26 * bp / 4)                        # a char per 16th
        u["sweep"] = (t - h["title_hit"]) / (4 * bp) % 1.0            # specular sweep every bar
        shake = decay(t, h["title_hit"], 0.25) + 0.6 * decay(t, h["shout"], 0.2)
        post["shake_x"] = 0.02 * shake * (np.sin(t * 91.0) )
        post["shake_y"] = 0.02 * shake * (np.cos(t * 77.0))
        post["flash"] = 0.9 * decay(t, h["title_hit"], 0.12) + 0.6 * decay(t, h["shout"], 0.1)
        down = (u["bar_ph"] < 0.06)                                   # glitch on downbeats
        post["glitch"] = 0.7 * decay(t, h["title_hit"], 0.3) + 0.5 * float(down) + \
            0.7 * decay(t, h["shout"], 0.35) + 0.6 * ramp(t, s["end"] - bp, s["end"])
        post["aberr"] = 0.0015 + 0.004 * u["kick"]

    def scene_hexa(self, s, t, u, post):
        bp = self.sync.period
        lt = t - s["start"]
        u["cap_r"] = (lt - 2 * bp) / (14 * bp / 4)
        u["cap2_r"] = (lt - 8 * bp) / (32 * bp / 4)
        u["zoom"] = 1.0 + 0.06 * u["kick"]
        post["flash"] = 0.7 * decay(t, s["start"], 0.1)
        post["glitch"] = 0.5 * decay(t, s["start"], 0.25) + 0.25 * float(u["bar_ph"] < 0.04)
        post["aberr"] = 0.0015 + 0.003 * u["kick"]

    # --- the scenes after the title -----------------------------------------------------
    def scene_kaleido(self, s, t, u, post):
        bp = self.sync.period
        lt = t - s["start"]
        u["segs"] = float((6, 8, 12, 8)[int(lt / (8 * bp)) % 4])      # new fold every 2 bars
        u["zoom"] = 1.0 + 0.10 * u["kick"]
        u["cap_r"] = (lt - bp) / (13 * bp / 4)
        post["flash"] = 0.6 * decay(t, s["start"], 0.1)
        post["glitch"] = 0.5 * decay(t, s["start"], 0.25) + 0.3 * float(lt % (8 * bp) < 0.07)
        post["aberr"] = 0.0015 + 0.003 * u["kick"]

    def scene_blackhole(self, s, t, u, post):
        bp = self.sync.period
        lt = t - s["start"]
        u["cap_r"] = (lt - bp) / (19 * bp / 4)
        u["pull"] = ramp(t, s["start"], s["end"])                     # tightens toward the breakdown
        post["flash"] = 0.6 * decay(t, s["start"], 0.1)
        post["glitch"] = 0.5 * decay(t, s["start"], 0.25) + 0.2 * float(u["bar_ph"] < 0.04)
        post["aberr"] = 0.002 + 0.004 * u["kick"]

    def scene_scanline(self, s, t, u, post):
        bp = self.sync.period
        u["squeeze"] = ramp(t, s["start"], s["start"] + 4 * bp)       # CRT collapses to a line in a bar
        u["pinch"] = ramp(t, s["end"] - 2 * bp, s["end"])              # then to a dot
        post["glitch"] = 0.25 * u["pulse"]
        post["flash"] = 0.4 * decay(t, s["start"], 0.1)

    def scene_chorus(self, s, t, u, post):
        bp = self.sync.period
        lt = t - s["start"]
        sec = s["section"]
        url_t = s["start"] + (URL_BARS_CHORUS1 * 4 * bp if sec == "chorus1" else 2 * bp)
        u["slam"] = decay(t, s["start"], 0.09)
        u["now_r"] = (lt - 0.5 * bp) / (10 * bp / 4)
        u["url_on"] = ramp(t, url_t, url_t + bp)
        u["url_r"] = (t - url_t) / (38 * bp / 8)                       # a char per 32nd
        u["linux_on"] = ramp(t, url_t + 4 * bp, url_t + 5 * bp) if sec == "chorus2" else 0.0
        u["linux_r"] = (t - url_t - 4 * bp) / (31 * bp / 8)
        post["flash"] = 0.9 * decay(t, s["start"], 0.12)
        post["shake_x"] = 0.015 * decay(t, s["start"], 0.25) * np.sin(t * 91.0)
        post["shake_y"] = 0.015 * decay(t, s["start"], 0.25) * np.cos(t * 77.0)
        # downbeat glitches, but never once the URL is up: it must stay readable
        post["glitch"] = 0.6 * decay(t, s["start"], 0.3) + 0.35 * float(u["bar_ph"] < 0.05) * (1 - u["url_on"])
        post["aberr"] = 0.0015 + 0.003 * u["kick"] * (1 - 0.7 * u["url_on"])

    def scene_crack(self, s, t, u, post):
        bp = self.sync.period
        lt = t - s["start"]
        u["r1"] = lt / (13 * bp / 4)
        post["flash"] = 0.5 * decay(t, s["start"], 0.1)
        post["glitch"] = 0.4 * decay(t, s["start"], 0.3) + 0.6 * ramp(t, s["end"] - bp, s["end"])

    def scene_rust(self, s, t, u, post):
        bp = self.sync.period
        lt = t - s["start"]
        u["r1"] = (lt - 0.5 * bp) / (8 * bp / 4)
        u["slam"] = decay(t, s["start"] + 2 * bp, 0.09) if lt >= 2 * bp else 0.0
        u["shown"] = float(lt >= 2 * bp)
        post["flash"] = 0.8 * decay(t, s["start"], 0.1) + 0.5 * (decay(t, s["start"] + 2 * bp, 0.1) if lt >= 2 * bp else 0)
        post["glitch"] = 0.5 * decay(t, s["start"], 0.25) + 0.3 * float(u["bar_ph"] < 0.04)

    def scene_grid(self, s, t, u, post):
        bp = self.sync.period
        lt = t - s["start"]
        u["tiles"] = float(min(4, 2 + int(lt / (8 * bp))))            # 2x2, 3x3 after 2 bars, 4x4
        u["cap_r"] = (lt - bp) / (17 * bp / 4)
        post["flash"] = 0.6 * decay(t, s["start"], 0.1)
        post["glitch"] = 0.5 * decay(t, s["start"], 0.25) + 0.4 * float(lt % (8 * bp) < 0.07 and lt > 1)

    def scene_record(self, s, t, u, post):
        bp = self.sync.period
        lt = t - s["start"]
        u["cap_r"] = (lt - bp) / (24 * bp / 4)
        u["f12_r"] = (lt - 6 * bp) / (9 * bp / 4)
        u["rec_on"] = float((lt / bp) % 2 < 1.0)                     # REC blinks a beat on, a beat off
        u["press"] = decay(t, s["start"], 0.15)
        post["flash"] = 0.6 * decay(t, s["start"], 0.1)
        post["glitch"] = 0.4 * decay(t, s["start"], 0.25) + 0.7 * ramp(t, s["end"] - bp, s["end"])

    def scene_outro(self, s, t, u, post):
        bp = self.sync.period
        lt = t - s["start"]
        end = self.sync.duration
        u["plat_r"] = (lt - 0.5 * bp) / (26 * bp / 8)
        # the greetz enter at the right edge a beat in and are off the left 0.3 s before the end
        u["scroll"] = (t - s["start"] - bp) / (end - 0.3 - s["start"] - bp)
        u["logo_on"] = ramp(t, s["start"], s["start"] + bp)
        post["flash"] = 0.5 * decay(t, s["start"], 0.1)
        post["fade"] = 1.0 - ramp(t, end - 1.6, end - 0.1)

    def timeline(self, t):
        """The scene segment at time t: dict(scene, slot, start, end, section)."""
        segs = []
        for sec, bars, scene, slot in TIMELINE:
            S = self.sync.by_name[sec]
            if bars == 0:
                start = S["start"]
            else:
                k = int(np.argmin(np.abs(self.sync.beats - S["start"]))) + 4 * bars
                start = float(self.sync.beats[k])
            segs.append({"scene": scene, "slot": slot, "start": start, "section": sec})
        for i, g in enumerate(segs):
            g["end"] = segs[i + 1]["start"] if i + 1 < len(segs) else self.sync.duration
        self.segs = segs
        return segs

    def segment(self, t):
        for g in self.segs:
            if g["start"] <= t < g["end"]:
                return g
        return self.segs[-1]

    def frame(self, fi):
        t = fi / FPS
        g = self.segment(t)
        sec = self.sync.by_name[g["section"]]
        name = g["scene"]
        u = dict(self.sync.uniforms(t), lt=t - g["start"], sec_id=float(self.sec_index[g["section"]]))
        post = {"bloom_gain": 0.9, "glitch": 0.0, "aberr": 0.0015, "flash": 0.0, "fade": 1.0,
                "scan": 1.0, "shake_x": 0.0, "shake_y": 0.0}
        u["has_foot"], u["foot_aspect"] = 0.0, 16 / 9
        post["note_on"] = float(name in NOTE_SCENES)
        post["note_box"] = self.note_box
        if g["slot"]:
            img = self.footage.frame(g["slot"], int(round((t - g["start"]) * FPS)))
            if img is not None:
                self.r.set_foot(img)
                u["has_foot"] = 1.0
        extra = getattr(self, "scene_" + name, None)
        if extra:
            extra(dict(g, end=g["end"], name=g["section"], sec_end=sec["end"]), t, u, post)
        for k, n in self.n_chars.items():
            u["n_" + k] = n
        return self.r.frame(name, u, post, fi)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out", help="'-' renders stills only")
    ap.add_argument("--audio", default=AUDIO, help="the track ('' for a silent clip)")
    ap.add_argument("--start", type=float, default=0.0)
    ap.add_argument("--dur", type=float, default=10.0)
    ap.add_argument("--section", default=None, help="render exactly this section (by name)")
    ap.add_argument("--full", action="store_true", help="the whole film")
    ap.add_argument("--res", type=int, default=1080, choices=(360, 480, 720, 1080))
    ap.add_argument("--square", action="store_true", help="1:1 frame (res x res)")
    ap.add_argument("--crf", type=int, default=20)
    ap.add_argument("--preset", default="veryfast")
    ap.add_argument("--still", action="append", type=float, default=[])
    a = ap.parse_args()

    H = a.res
    # 16:9 width rounded down to a multiple of 16: 480p -> 848x480 (854 crashes Parole), 1080p -> 1920
    W = H if a.square else int(H * 16 / 9) // 16 * 16
    film = Film(W, H)
    if a.full:
        f0, n = 0, film.sync.n_frames
    elif a.section:
        s = film.sync.by_name[a.section]
        f0 = int(np.ceil(s["start"] * FPS - 1e-9)); n = int(np.ceil(s["end"] * FPS - 1e-9)) - f0
    else:
        f0, n = round(a.start * FPS), round(a.dur * FPS)
    for fi in range(max(0, f0 - WARMUP), f0):
        film.frame(fi)
    stills = {round(t * FPS): t for t in a.still}
    stem = os.path.splitext(a.out)[0] if a.out != "-" else os.path.join(HERE, "renders", "still")
    os.makedirs(os.path.dirname(os.path.abspath(stem)), exist_ok=True)
    if a.out == "-":
        last = -10
        for fi, t in sorted(stills.items()):
            for k in range(max(last + 1, fi - WARMUP), fi):
                film.frame(k)
            save_png(film.frame(fi), W, H, f"{stem}_{t:06.2f}s.png"); last = fi
        return
    print(f"render {W}x{H} @ {FPS} fps: frames {f0}..{f0 + n - 1} ({f0 / FPS:.3f}-{(f0 + n) / FPS:.3f} s)",
          file=sys.stderr)
    proc = ffmpeg_writer(a.out, W, H, f0 / FPS, n / FPS, a.audio, a.crf, a.preset)
    for fi in range(f0, f0 + n):
        buf = film.frame(fi)
        proc.stdin.write(buf)
        if fi in stills:
            save_png(buf, W, H, f"{stem}_{stills[fi]:06.2f}s.png")
        if (fi - f0) % 300 == 0:
            print(f"frame {fi} / {f0 + n} ({fi / FPS:.1f} s)", file=sys.stderr, flush=True)
    proc.stdin.close()
    sys.exit(proc.wait())

if __name__ == "__main__":
    main()
