// verse 1, bar 8 (0:57.47-1:11.37): KALEIDOSCOPES. The app footage folded into 6, 8 or 12
// mirrored segments (a new count every 2 bars), turning, zooming in on the kicks, with the
// segment seams lit by the highs.
uniform sampler2D t_kaleido;
uniform float n_kaleido;
uniform float segs, zoom, cap_r;

void main() {
    vec2 p = P();
    float r = length(p) / zoom;
    float a = atan(p.y, p.x) + time * 0.18;
    float seg = TAU / segs;
    float am = mod(a, seg);
    float af = abs(am - seg * 0.5);                               // mirrored fold
    vec2 k = r * vec2(cos(af), sin(af));
    vec2 st = k * 0.55 + vec2(0.5 + 0.12 * sin(time * 0.21), 0.5 + 0.1 * cos(time * 0.17));
    vec3 c = foot(st) * 1.1;
    // seams: thin bright spokes on the fold lines
    float seam = smoothstep(0.012, 0.0, abs(af - seg * 0.5) * r) + smoothstep(0.012, 0.0, af * r);
    c += seam * hsv(time * 0.1 + r, 0.5, 1.0) * (0.15 + 0.6 * high);
    c *= smoothstep(2.4, 0.6, r);
    c += vec3(1.0) * smoothstep(0.05, 0.0, r) * (0.5 + kick);   // hot centre on the kick

    // caption, and the placeholder tag while no clip is in
    float by = -0.76;
    float bandm = smoothstep(0.11, 0.09, abs(p.y - by)) * step(0.0, cap_r);
    c = mix(c, vec3(0.0, 0.0, 0.02), 0.8 * bandm);
    c += typed(t_kaleido, p, vec2(0.0, by), 0.13, 1.6, cap_r, n_kaleido, step(0.5, fract(time * 2.3)))
         * vec3(0.4, 1.0, 0.95) * 1.3;
    c = ph_label(c, p, vec2(0.0, 0.86));
    frag = vec4(c, 1.0);
}
