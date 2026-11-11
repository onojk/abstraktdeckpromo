// intro (0:00-0:28.77): cracktro. A 3D starfield, copper raster bars, "ONOJK123" typed a
// character per beat and "ART PRESENTS" per half beat; a cut to black on the silence at
// 13.75 s; "ABSTRAKT" flickers in on the tease; from the build the stars stretch into warp
// streaks and the bars race until the white-out at the title hit.
uniform sampler2D t_onojk, t_presents, t_abstrakt;
uniform float n_onojk, n_presents;
uniform float r1, r2, fade_in, tease, build, bars_on, gap_after;

vec3 starfield(vec2 p, float warp) {
    vec3 c = vec3(0.0);
    float spd = 0.08 + 0.05 * tease + 0.9 * build * build;
    for (int l = 0; l < 7; l++) {
        float fl = float(l);
        float z = fract(fl / 7.0 - time * spd);                 // 1 far .. 0 near
        float scale = mix(0.4, 9.0, z);
        vec2 q = p * scale + fl * 17.3;
        vec2 id = floor(q), f = fract(q) - 0.5;
        vec2 o = hash22(id + fl * 3.1) - 0.5;
        if (hash21(id + fl) > 0.55) continue;
        vec2 d = f - o * 0.8;
        // warp: stretch along the star's own direction from the centre
        vec2 dir = normalize((id + 0.5 + o * 0.8 - fl * 17.3) / scale + 1e-4);
        float along = dot(d, dir), across = dot(d, vec2(-dir.y, dir.x));
        along /= 1.0 + warp * 22.0 * (1.0 - z);
        float r = length(vec2(along, across));
        float size = 0.03 + 0.05 * (1.0 - z);
        float b = smoothstep(size, 0.0, r) * smoothstep(1.0, 0.6, z) * (1.0 - z * 0.7);
        c += b * mix(vec3(0.7, 0.85, 1.0), hsv(hash21(id) , 0.5, 1.0), 0.35);
    }
    return c;
}

void main() {
    vec2 p = P();
    vec3 c = vec3(0.0);
    c += starfield(p, build) * fade_in;

    // copper bars: five, sine-swinging; race and brighten through the build
    float bt = time * (1.1 + 4.0 * build * build);
    vec3 bars = vec3(0.0);
    for (int i = 0; i < 5; i++) {
        float fi = float(i);
        float yc = 0.78 * sin(bt * 0.9 + fi * 0.75);
        bars = max(bars, copper(p.y, yc, 0.055 + 0.02 * build, fi * 0.2 + time * 0.03));
    }
    c += bars * bars_on * (0.22 + 0.6 * build) * (1.0 - 0.7 * tease * (1.0 - build));

    // the typed credits: big chunky pixels; a dark band behind keeps them readable on the bars
    float out_t = tease;                                          // slide away on the tease
    vec2 off = vec2(0.0, 1.4 * out_t * out_t);
    float a1 = typed(t_onojk, p - off, vec2(0.0, 0.22), 0.30, 1.85, r1, n_onojk, step(0.5, fract(time * 2.3)));
    float a2 = typed(t_presents, p - off, vec2(0.0, -0.16), 0.15, 1.6, r2, n_presents, step(0.5, fract(time * 2.3)));
    float band = smoothstep(0.42, 0.38, abs(p.y + 0.0 - off.y - 0.03)) * step(0.0, r1) * (1.0 - out_t);
    c *= 1.0 - 0.6 * band;
    vec3 ink1 = mix(vec3(0.35, 1.0, 0.95), vec3(1.0), 0.35) * (1.0 + 0.6 * gap_after);
    vec3 ink2 = vec3(1.0, 0.55, 0.95);
    c += a1 * ink1 * 1.2 + a2 * ink2 * 1.1;

    // the tease: ABSTRAKT flickers in, a frame-hashed on/off that settles toward on
    float on = step(hash11(floor(time * 15.0)), 0.25 + 0.6 * tease + 0.3 * build);
    vec3 at = textq(t_abstrakt, p, vec2(0.0, 0.0), 0.42 + 0.08 * build, 1.85);
    float edge = at.x * (1.0 - at.x) * 4.0;                       // outline-ish ink
    vec3 chrome = mix(vec3(0.2, 0.9, 1.0), vec3(1.0, 0.3, 0.8), at.z);
    c += tease * on * (edge * chrome * 1.4 + at.x * chrome * (0.15 + 0.6 * build));

    // white-out toward the hit
    c += vec3(0.6, 0.8, 1.0) * pow(build, 6.0) * 0.8;
    frag = vec4(c, 1.0);
}
