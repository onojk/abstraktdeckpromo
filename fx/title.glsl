// title (0:28.77-0:43.57): the ABSTRAKT DECK slam. A dim rainbow plasma pumping on the
// kicks, raster bars that jump on every beat, the logo in chrome slamming in from 3x with a
// specular sweep each bar, and "NOW ON THE MICROSOFT STORE" typed under it on a dark banner.
uniform sampler2D t_abstrakt, t_deck, t_store;
uniform float n_store;
uniform float slam, sub_r, sweep;

vec3 plasma(vec2 p) {
    float t = time * 0.6;
    float v = sin(p.x * 3.1 + t) + sin(p.y * 3.7 - t * 1.3)
            + sin((p.x + p.y) * 2.6 + t * 0.7) + sin(length(p * 1.4 + vec2(sin(t * 0.5), cos(t * 0.4))) * 5.0 - t * 2.0);
    return hsv(v * 0.12 + time * 0.04, 0.85, 1.0);
}

vec3 logo_ink(sampler2D T, vec2 p, vec2 c, float h) {
    vec3 a = textq(T, p, c, h, 1.86);
    if (a.x <= 0.0) return vec3(0.0);
    // chrome: sky above the horizon line, hot sunset below, a rainbow tint drifting across
    float y = a.z;
    vec3 sky = mix(vec3(0.15, 0.55, 1.0), vec3(1.0), smoothstep(0.52, 0.95, y));
    vec3 sun = mix(vec3(1.0, 0.85, 0.2), vec3(1.0, 0.15, 0.6), smoothstep(0.48, 0.05, y));
    vec3 col = y > 0.5 ? sky : sun;
    col = mix(col, hsv(a.y * 0.6 + time * 0.15, 0.7, 1.0), 0.25);
    col *= 0.75 + 0.25 * smoothstep(0.47, 0.53, abs(y - 0.5) + 0.47);    // dark horizon seam
    float sw = exp(-pow((a.y - (sweep * 1.6 - 0.3)) * 7.0 + (y - 0.5) * 2.0, 2.0));
    col += vec3(1.0) * sw * 0.9;                                          // specular sweep
    return col * a.x;
}

void main() {
    vec2 p = P();
    float zoomk = 1.0 + 0.05 * kick;
    vec3 c = plasma(p / zoomk) * (0.10 + 0.14 * kick + 0.08 * low);

    // raster bars: their positions jump to a new set every beat
    for (int i = 0; i < 4; i++) {
        float fi = float(i);
        float yc = 0.85 * sin(beat * 1.37 + fi * 1.9 + beat_ph * 0.8);
        c += copper(p.y, yc, 0.05, fi * 0.25 + beat * 0.05) * (0.25 + 0.5 * pulse);
    }

    // the logo: scale from 3x at the hit, bounce on beats
    float s = 1.0 + 2.2 * slam - 0.035 * pulse;
    vec2 q = p / s;
    vec2 sh = vec2(0.025, -0.03);
    float shadow = max(text(t_abstrakt, q - sh, vec2(0.0, 0.33), 0.44, 1.86),
                       text(t_deck, q - sh, vec2(0.0, -0.12), 0.44, 1.86));
    c *= 1.0 - 0.85 * shadow;
    c += logo_ink(t_abstrakt, q, vec2(0.0, 0.33), 0.44);
    c += logo_ink(t_deck, q, vec2(0.0, -0.12), 0.44) * 1.05;

    // the banner and subtitle
    float by = -0.58;
    float bandm = smoothstep(0.14, 0.12, abs(p.y - by)) * step(0.0, sub_r);
    c = mix(c, vec3(0.0, 0.0, 0.02), 0.85 * bandm);
    c += bandm * 0.5 * copper(p.y, by + 0.135, 0.012, time * 0.1) + bandm * 0.5 * copper(p.y, by - 0.135, 0.012, time * 0.1 + 0.5);
    float sa = typed(t_store, p, vec2(0.0, by), 0.12, 1.8, sub_r, n_store, step(0.5, fract(time * 2.3)));
    c += sa * mix(vec3(1.0, 0.95, 0.5), vec3(1.0), 0.4 * pulse) * 1.3;

    frag = vec4(c, 1.0);
}
