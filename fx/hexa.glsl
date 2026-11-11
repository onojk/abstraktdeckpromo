// verse 1 opening (from 0:43.57): audio-reactive hexagons. A hex grid where each cell's
// ring around the centre reads one of 16 spectrum bands (bass in the middle, highs outside):
// cells swell and brighten with their band, coloured in the app's rainbow rings, the grid
// turning slowly and kicking in on the bass, with feedback trails. Caption: AUDIO-REACTIVE /
// VISUALS THAT DANCE TO YOUR MUSIC.
uniform sampler2D t_reactive, t_dance;
uniform float n_reactive, n_dance;
uniform float cap_r, cap2_r, zoom;

float band(float k) {
    int i = int(clamp(k, 0.0, 15.0));
    int j = min(i + 1, 15);
    return mix(spec[i], spec[j], fract(k));
}

// hex cell: returns (local offset from cell centre, cell id)
vec4 hexcell(vec2 p) {
    const vec2 s = vec2(1.0, 1.7320508);
    vec2 a = mod(p, s) - s * 0.5;
    vec2 b = mod(p - s * 0.5, s) - s * 0.5;
    vec2 g = dot(a, a) < dot(b, b) ? a : b;
    return vec4(g, p - g);
}
float hexdist(vec2 g) { g = abs(g); return max(dot(g, normalize(vec2(1.0, 1.7320508))), g.x); }

void main() {
    vec2 p = P();
    // feedback: last frame, pulled slightly inward and faded, as trails
    vec2 fu = (uv - 0.5) * 0.985 + 0.5;
    vec3 c = texture(prev, fu).rgb * 0.62;

    vec2 q = rot(time * 0.08) * p / zoom * 5.0;
    vec4 h = hexcell(q);
    vec2 cid = h.zw;
    float ring = length(cid) / 1.7320508;                        // in cells from the centre
    float lv = band(ring * 1.6);
    float ang = atan(cid.y, cid.x) / TAU;
    float hd = hexdist(h.xy);
    float rad = 0.12 + 0.36 * lv;
    float fill = smoothstep(rad + 0.02, rad - 0.02, hd);
    float rim = smoothstep(0.03, 0.0, abs(hd - rad)) ;
    vec3 col = hsv(ang + time * 0.07 + ring * 0.06 - 0.12 * kick, 0.9, 1.0);
    vec3 cell = col * (fill * (0.12 + 0.85 * lv * lv) + rim * (0.4 + 0.8 * lv));
    c = max(c, cell);
    // a faint lattice so the empty grid still reads
    c += vec3(0.02, 0.05, 0.08) * smoothstep(0.02, 0.0, abs(hd - 0.5));

    // caption
    float by = -0.70;
    float bandm = smoothstep(0.17, 0.15, abs(p.y - by)) * step(0.0, cap_r);
    c = mix(c, vec3(0.0, 0.0, 0.02), 0.8 * bandm);
    float a1 = typed(t_reactive, p, vec2(0.0, by + 0.06), 0.13, 1.6, cap_r, n_reactive, step(0.5, fract(time * 2.3)));
    float a2 = typed(t_dance, p, vec2(0.0, by - 0.08), 0.065, 1.75, cap2_r, n_dance, step(0.5, fract(time * 2.3)));
    c += a1 * vec3(0.4, 1.0, 0.95) * 1.3 + a2 * vec3(1.0) * 1.0;
    frag = vec4(c, 1.0);
}
