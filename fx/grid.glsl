// verse 2, bar 6 (2:30.17-2:40.60): MULTI-PANEL GRIDS. The app footage in a grid of panels,
// 2x2, then 3x3 after two bars, then 4x4; each panel its own variant (turned, zoomed,
// mirrored, colour-rotated, some kaleidoscope-folded), one panel lighting up per beat in turn.
uniform sampler2D t_grid;
uniform float n_grid;
uniform float tiles, cap_r;

vec3 variant(vec2 l, float v, float idx) {
    vec2 q = l - 0.5;
    q = rot(floor(v * 4.0) * PI * 0.5 + time * 0.1 * (v - 0.5)) * q;
    q *= 0.8 + 0.6 * fract(v * 7.3) - 0.08 * kick;
    if (fract(v * 3.7) > 0.6) {                                   // a few panels fold
        float segs = 6.0 + 2.0 * floor(fract(v * 11.0) * 3.0);
        float a = atan(q.y, q.x), r = length(q), seg = TAU / segs;
        a = abs(mod(a, seg) - seg * 0.5);
        q = r * vec2(cos(a), sin(a));
    }
    vec3 c = foot(q + 0.5 + vec2(0.05 * sin(time * 0.3 + idx), 0.0));
    float k = fract(v * 5.1);
    if (k > 0.66) c = c.gbr; else if (k > 0.33) c = c.brg;
    return c;
}

void main() {
    vec2 p = P();
    float asp = res.x / res.y;
    vec2 g = uv * tiles;
    vec2 id = floor(g), l = fract(g);
    float idx = id.y * tiles + id.x;
    float v = hash21(id + tiles * 13.0);
    float gap = 0.035;
    float inside = step(gap, l.x) * step(l.x, 1.0 - gap) * step(gap, l.y) * step(l.y, 1.0 - gap);
    vec2 ll = (l - gap) / (1.0 - 2.0 * gap);
    vec3 c = variant(ll, v, idx) * inside;
    float lit = step(abs(mod(beat, tiles * tiles) - (tiles * tiles - 1.0 - idx)), 0.5);
    c *= 0.7 + 0.8 * lit * pulse + 0.3 * lit;
    // panel frames
    float frame = inside * (1.0 - step(gap + 0.012, l.x) * step(l.x, 1.0 - gap - 0.012)
                                * step(gap + 0.012, l.y) * step(l.y, 1.0 - gap - 0.012));
    c += frame * hsv(idx / (tiles * tiles) + time * 0.1, 0.5, 1.0) * (0.3 + 0.9 * lit * pulse);

    float by = -0.76;
    float bandm = smoothstep(0.11, 0.09, abs(p.y - by)) * step(0.0, cap_r);
    c = mix(c, vec3(0.0, 0.0, 0.02), 0.85 * bandm);
    c += typed(t_grid, p, vec2(0.0, by), 0.13, 1.7, cap_r, n_grid, step(0.5, fract(time * 2.3)))
         * vec3(0.4, 1.0, 0.95) * 1.3;
    c = ph_label(c, p, vec2(0.0, 0.86));
    frag = vec4(c, 1.0);
}
