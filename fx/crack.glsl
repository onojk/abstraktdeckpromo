// break (2:14.03-2:19.70): a cracktro callback to the intro. The near-mono break shares the
// intro's harmony, so it gets the intro's look back: starfield, copper bars and the pixel
// logo, typed fast, each character bobbing on a sine.
uniform sampler2D t_crack;
uniform float n_crack, r1;

void main() {
    vec2 p = P();
    vec3 c = stars(p, 0.25, 0.0);
    for (int i = 0; i < 5; i++) {
        float fi = float(i);
        c += copper(p.y, 0.8 * sin(time * 1.4 + fi * 0.75), 0.05, fi * 0.2 + time * 0.03) * 0.35;
    }
    // per-character sine bob: the char slot under this pixel picks the phase
    vec2 ts = vec2(textureSize(t_crack, 0));
    float h = 0.26, mw = 1.85;
    float w = min(h * ts.x / ts.y, mw); h = w * ts.y / ts.x;
    float slot = floor(((p.x + w * 0.5) / w) * n_crack);
    float yo = 0.06 * sin(time * 5.0 + slot * 0.7);
    float a = typed(t_crack, p, vec2(0.0, yo), h, mw, r1, n_crack, step(0.5, fract(time * 2.3)));
    float band = smoothstep(0.24, 0.2, abs(p.y));
    c *= 1.0 - 0.55 * band;
    c += a * mix(vec3(0.35, 1.0, 0.95), hsv(slot / n_crack + time * 0.2, 0.6, 1.0), 0.5) * 1.3;
    frag = vec4(c, 1.0);
}
