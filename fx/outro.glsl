// outro (3:05.00-3:15.52): SNAP STORE * PPA * WINDOWS, the pixel logo, and the greetz: a
// classic sine scroller crossing the screen once, each character riding the wave, coloured by
// position, over the starfield and slow copper bars. Fades to black at the end.
uniform sampler2D t_platforms, t_crack, t_greetz;
uniform float n_platforms, n_greetz;
uniform float plat_r, scroll, logo_on;

void main() {
    vec2 p = P();
    float asp = res.x / res.y;
    vec3 c = stars(p, 0.12, 0.0) * 0.8;
    for (int i = 0; i < 4; i++) {
        float fi = float(i);
        c += copper(p.y, -0.45 + 0.35 * sin(time * 0.9 + fi * 0.9), 0.04, fi * 0.22 + time * 0.03) * 0.3;
    }
    // the platforms, then the logo under them
    c += typed(t_platforms, p, vec2(0.0, 0.70), 0.10, 1.8, plat_r, n_platforms, 0.0) * vec3(1.0, 0.95, 0.55) * 1.3;
    c += text(t_crack, p, vec2(0.0, 0.40), 0.20, 1.7) * logo_on * vec3(0.35, 1.0, 0.95) * 1.2;

    // the sine scroller
    vec2 ts = vec2(textureSize(t_greetz, 0));
    float h = 0.14, w = h * ts.x / ts.y;
    float cx = mix(asp + w * 0.5, -asp - w * 0.5, scroll);
    float lx = (p.x - cx) / w + 0.5;                               // 0..1 along the string
    float slot = floor(lx * n_greetz);
    float yo = 0.07 * sin(time * 3.0 + slot * 0.28);
    float a = text(t_greetz, p, vec2(cx, -0.25 + yo), h, 100.0);
    c += a * hsv(slot / 24.0 + time * 0.15, 0.55, 1.0) * 1.35;
    frag = vec4(c, 1.0);
}
