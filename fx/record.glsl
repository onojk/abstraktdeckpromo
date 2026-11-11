// verse 2, bar 12 (2:40.60-2:50.20): RECORD STRAIGHT TO VIDEO. The app footage in a camera
// viewfinder: corner brackets, a red REC dot blinking on the beat, a recording bar filling
// across the bottom; a "PRESS F12" key that dips when it is pressed at the cut.
uniform sampler2D t_record, t_f12, t_rec;
uniform float n_record, n_f12;
uniform float cap_r, f12_r, rec_on, press;

void main() {
    vec2 p = P();
    float asp = res.x / res.y;
    // the viewfinder: footage inset with a margin
    vec2 m = vec2(asp - 0.12, 0.70);
    float sc = max(m.x / foot_aspect, m.y);                       // cover-crop, never stretch
    vec2 st = p / (sc * vec2(foot_aspect, 1.0)) * 0.5 + 0.5;
    vec2 sd = abs(p) - m;
    float inside = step(max(sd.x, sd.y), 0.0);
    vec3 c = foot(st) * inside * 0.95;
    c += vec3(0.01, 0.01, 0.02) * (1.0 - inside);
    // corner brackets
    vec2 cp = abs(p) - (m - 0.02);
    float br = step(cp.x, 0.0) * step(cp.y, 0.0) * step(-0.12, cp.x) * step(-0.12, cp.y)
             * (1.0 - step(cp.x, -0.012) * step(cp.y, -0.012));
    c += br * vec3(0.9);
    // REC
    vec2 rp = vec2(-m.x + 0.12, m.y - 0.1);
    float dotm = smoothstep(0.035, 0.03, length(p - rp));
    c = mix(c, vec3(1.0, 0.08, 0.05) * 1.4, dotm * rec_on);
    c += text(t_rec, p, rp + vec2(0.16, 0.0), 0.07, 0.5) * vec3(1.0) * 1.2;
    // recording bar
    float prog = fract(lt / 20.0);
    float bar = step(abs(p.y + m.y - 0.06), 0.008) * step(-m.x + 0.08, p.x) * step(p.x, -m.x + 0.08 + prog * (2.0 * m.x - 0.16));
    c += bar * vec3(1.0, 0.2, 0.15);
    c = ph_label(c, p, vec2(0.0, 0.40));

    // caption under the viewfinder; the F12 key on the right of the caption
    float by = -0.84;
    c += typed(t_record, p, vec2(0.0, by), 0.10, 1.8, cap_r, n_record, step(0.5, fract(time * 2.3)))
         * vec3(0.4, 1.0, 0.95) * 1.3;
    vec2 kp = vec2(m.x - 0.3, m.y - 0.12 - 0.01 * press);   // top-right of the viewfinder
    vec2 kd = abs(p - kp) - vec2(0.2, 0.065);
    float key = step(max(kd.x, kd.y), 0.0) * step(0.0, f12_r);
    float keyedge = key * (1.0 - step(max(kd.x, kd.y), -0.01));
    c = mix(c, vec3(0.12, 0.12, 0.16), key * 0.9);
    c += keyedge * vec3(0.8) + typed(t_f12, p, kp, 0.06, 0.36, f12_r, n_f12, 0.0) * vec3(1.0, 0.95, 0.6) * 1.3;
    frag = vec4(c, 1.0);
}
