// verse 1, from the build (1:11.53-1:32.57): BLACK-HOLE FEEDBACK. Each frame the last one is
// sampled swirled and from further out, so everything spirals inward; fresh app footage is
// fed in on an outer ring; the centre is a black disc with a glowing event horizon that
// pulses on the kicks. The pull tightens toward the breakdown.
uniform sampler2D t_blackhole;
uniform float n_blackhole;
uniform float cap_r, pull;

void main() {
    vec2 p = P();
    float asp = res.x / res.y;
    float r = length(p);
    // feedback: sample the previous frame swirled and zoomed out (content moves inward)
    float swirl = (0.035 + 0.05 * pull + 0.03 * low) / (0.35 + r);
    vec2 q = rot(swirl) * p * (1.025 + 0.02 * pull + 0.015 * kick);
    vec2 fu = q / vec2(asp, 1.0) * 0.5 + 0.5;
    vec3 c = texture(prev, fu).rgb * (0.93 - 0.04 * pull);
    // the caption band and placeholder tag are overlays: never feed them back into the swirl
    float overlay = step(abs(q.y + 0.76), 0.12) + step(0.78, q.y) * step(abs(q.x), 0.8);
    c *= 1.0 - clamp(overlay, 0.0, 1.0);
    c = mix(c, c.gbr, 0.015);                                    // slow hue drift in the trails

    // fresh footage on an outer ring, rotating
    float a = atan(p.y, p.x);
    float ring = smoothstep(0.75, 0.95, r) * smoothstep(1.6, 1.25, r);
    vec2 st = vec2(a / TAU + 0.5 + time * 0.03, (r - 0.75) / 0.85);
    c = max(c, foot(st) * ring * (0.55 + 0.6 * rms));

    // the hole and its horizon
    float rh = 0.16 + 0.05 * pull + 0.025 * kick;
    float horizon = exp(-pow((r - rh) / (0.012 + 0.02 * kick), 2.0));
    c *= smoothstep(rh * 0.92, rh * 1.15, r);
    c += horizon * hsv(a / TAU + time * 0.2, 0.6, 1.0) * (0.8 + 1.5 * kick);

    float by = -0.76;
    float bandm = smoothstep(0.11, 0.09, abs(p.y - by)) * step(0.0, cap_r);
    vec3 outc = mix(c, vec3(0.0, 0.0, 0.02), 0.8 * bandm);
    outc += typed(t_blackhole, p, vec2(0.0, by), 0.13, 1.75, cap_r, n_blackhole, step(0.5, fract(time * 2.3)))
         * vec3(1.0, 0.6, 0.95) * 1.3;
    outc = ph_label(outc, p, vec2(0.0, 0.86));
    frag = vec4(outc, 1.0);
}
