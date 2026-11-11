// chorus 1 (1:38.67-2:14.03) and chorus 2 (2:50.20-3:05.00): NOW ON THE MICROSOFT STORE.
// A rotozoomed copper checkerboard, full-width raster bars that drop in on every beat, the
// headline slamming in and bouncing on the kicks. The Store URL comes up on a steady banner
// (chorus 1: its last ~8 bars; chorus 2: from its second beat to the end), with the Linux
// line under it in chorus 2. Nothing moves or glitches over the URL once it is up.
uniform sampler2D t_nowonthe, t_msstore, t_url, t_linux;
uniform float n_nowonthe, n_url, n_linux;
uniform float slam, now_r, url_on, url_r, linux_on, linux_r;

vec3 rotozoom(vec2 p) {
    float z = 1.6 + 0.7 * sin(time * 0.31);
    vec2 q = rot(time * 0.23) * p * z + vec2(time * 0.4, time * 0.13);
    vec2 cell = floor(q * 2.0);
    float chk = mod(cell.x + cell.y, 2.0);
    vec3 a = hsv(0.62 + 0.04 * sin(time), 0.8, 1.0), b = hsv(0.85 + beat * 0.02, 0.8, 1.0);
    return mix(a, b, chk);
}

void main() {
    vec2 p = P();
    vec3 c = rotozoom(p / (1.0 + 0.04 * kick)) * (0.10 + 0.10 * kick) * (1.0 - 0.5 * url_on);

    // raster bars: each beat a new set falls from the top and settles
    for (int i = 0; i < 6; i++) {
        float fi = float(i);
        float home = 0.9 - fi * 0.36;
        float yc = home + 0.5 * pow(1.0 - beat_ph, 6.0) * (1.0 + fi * 0.2);
        c += copper(p.y, yc, 0.045, fi * 0.15 + beat * 0.11) * (0.25 + 0.55 * pulse) * (1.0 - 0.6 * url_on);
    }

    float lift = 0.18 * (1.0 - url_on);                          // headline centred until the URL comes
    float s = 1.0 + 2.0 * slam - 0.03 * pulse * (1.0 - url_on);
    vec2 q = p / s;
    // NOW ON THE
    c += typed(t_nowonthe, q, vec2(0.0, 0.58 - lift), 0.13, 1.4, now_r, n_nowonthe, 0.0) * vec3(1.0, 0.95, 0.55) * 1.3;
    // MICROSOFT STORE in chrome, with a dark drop shadow
    vec2 sh = vec2(0.02, -0.025);
    float shadow = text(t_msstore, q - sh, vec2(0.0, 0.30 - lift), 0.27, 1.86);
    c *= 1.0 - 0.85 * shadow;
    vec3 a = textq(t_msstore, q, vec2(0.0, 0.30 - lift), 0.27, 1.86);
    vec3 sky = mix(vec3(0.15, 0.55, 1.0), vec3(1.0), smoothstep(0.5, 0.95, a.z));
    vec3 sun = mix(vec3(1.0, 0.85, 0.2), vec3(1.0, 0.15, 0.6), smoothstep(0.5, 0.05, a.z));
    vec3 chrome = a.z > 0.5 ? sky : sun;
    float sw = exp(-pow((a.y - (fract(bar / 2.0 + bar_ph / 2.0) * 1.6 - 0.3)) * 7.0, 2.0));
    c += (chrome + sw) * a.x * 1.05;

    // the URL banner: dark, steady, full contrast
    float uy = -0.30;
    float umw = min(res.x / res.y * 1.8, 3.1);                   // the URL uses the frame's width
    float uh = min(0.14, umw / 23.5);                             // (38 mono chars ~ 23.5 heights wide)
    float bandm = smoothstep(uh + 0.04, uh + 0.03, abs(p.y - uy)) * url_on;
    c = mix(c, vec3(0.0, 0.0, 0.03), 0.92 * bandm);
    c += bandm * 0.6 * (copper(p.y, uy + uh + 0.035, 0.01, 0.55) + copper(p.y, uy - uh - 0.035, 0.01, 0.9));
    c += typed(t_url, p, vec2(0.0, uy), uh, umw, url_r, n_url, 0.0) * url_on * vec3(1.0) * 1.4;

    // ALSO ON LINUX (chorus 2)
    float ly = -0.62;
    float lm = smoothstep(0.08, 0.07, abs(p.y - ly)) * linux_on;
    c = mix(c, vec3(0.0, 0.0, 0.03), 0.85 * lm);
    c += typed(t_linux, p, vec2(0.0, ly), 0.075, 1.6, linux_r, n_linux, 0.0) * linux_on * vec3(0.45, 1.0, 0.75) * 1.3;
    frag = vec4(c, 1.0);
}
