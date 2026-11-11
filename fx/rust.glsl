// verse 2 opening (2:19.70-2:30.17): BUILT IN RUST + WGPU. A dot tunnel (rings of glowing
// points rushing at the viewer, the tunnel's path bending on a sine) behind; "BUILT IN" typed,
// then RUST + WGPU slams in two beats later, its letters filled with copper raster bars that
// scroll through them, the classic masked-copper look.
uniform sampler2D t_builtin, t_rustwgpu;
uniform float n_builtin;
uniform float r1, slam, shown;

vec3 dot_tunnel(vec2 p) {
    vec3 c = vec3(0.0);
    for (int i = 0; i < 18; i++) {
        float fi = float(i);
        float z = fract(fi / 18.0 - time * 0.35);                 // 1 far .. 0 near
        float depth = mix(0.25, 6.0, z);
        float tz = time * 1.2 + fi * 0.33;
        vec2 cen = vec2(0.5 * sin(tz * 0.7), 0.35 * cos(tz * 0.5)) * (1.0 - 1.0 / depth);
        vec2 q = (p - cen) * depth;
        float a = atan(q.y, q.x);
        float n = 16.0;
        float sa = (floor(a / TAU * n) + 0.5) / n * TAU;
        vec2 dotp = vec2(cos(sa), sin(sa));
        float d = length(q - dotp) / depth;
        float size = 0.012 + 0.03 / depth;
        float b = smoothstep(size, 0.0, d) * smoothstep(1.0, 0.75, z) * smoothstep(0.0, 0.08, z);
        c += b * hsv(0.05 + fi * 0.04 + time * 0.05, 0.7, 1.0) * (0.6 + 0.8 * pulse);
    }
    return c;
}

void main() {
    vec2 p = P();
    vec3 c = dot_tunnel(p) * 0.8;

    c += typed(t_builtin, p, vec2(0.0, 0.42), 0.12, 1.2, r1, n_builtin, step(0.5, fract(time * 2.3)))
         * vec3(1.0, 0.95, 0.6) * 1.3;

    float s = 1.0 + 2.0 * slam - 0.03 * pulse;
    vec2 q = p / s;
    vec2 sh = vec2(0.02, -0.025);
    float shadow = text(t_rustwgpu, q - sh, vec2(0.0, 0.0), 0.36, 1.86) * shown;
    c *= 1.0 - 0.85 * shadow;
    vec3 a = textq(t_rustwgpu, q, vec2(0.0, 0.0), 0.36, 1.86);
    // copper fill: 7 bars scrolling down through the letters, warm rust-orange to hot white
    vec3 fill = vec3(0.0);
    for (int i = 0; i < 7; i++) {
        float fi = float(i);
        float yc = 1.2 - fract(time * 0.45 + fi / 7.0) * 2.4;
        fill = max(fill, copper(a.z * 2.0 - 1.0, yc, 0.2, 0.03 + 0.05 * sin(fi * 2.1)) * vec3(1.0, 0.75, 0.55));
    }
    fill = max(fill, vec3(0.55, 0.16, 0.03));
    c += fill * a.x * shown * 1.15;
    frag = vec4(c, 1.0);
}
