// breakdown / pre-chorus (1:32.57-1:38.67): the CRT powers down. A mirrored 16-band
// spectrum squeezes vertically into one glowing scanline over the first bar, rides the music
// as a line, then pulls in to a dot for the last two beats; chorus 1 explodes out of it.
uniform float squeeze, pinch;

void main() {
    vec2 p = P();
    float asp = res.x / res.y;
    float sy = mix(1.0, 0.012, squeeze);                         // vertical squeeze
    float sx = mix(1.0, 0.02, pinch * pinch);                        // horizontal pull to the dot
    vec2 q = vec2(p.x / sx, p.y / sy);
    vec3 c = vec3(0.0);
    if (abs(q.x) < asp) {
        float x = abs(q.x) / asp;                                 // 0 centre .. 1 edge, mirrored
        float k = x * 15.0;
        float lv = band(k);
        float bar = step(abs(q.y), 0.08 + 0.85 * lv) * step(0.12, fract(k));
        vec3 col = hsv(0.55 - x * 0.6 + time * 0.05, 0.8, 1.0);
        c = col * bar * (0.5 + 0.6 * lv);
        c += col * 0.25 * exp(-abs(q.y) * 6.0);                   // glow around the axis
    }
    // the line itself: white-hot, brighter as it thins
    float line = exp(-pow(p.y / (0.004 + 0.02 * (1.0 - squeeze)), 2.0)) * squeeze;
    line *= smoothstep(asp * sx + 0.02, asp * sx - 0.05, abs(p.x));
    c += vec3(0.85, 0.95, 1.0) * line * (1.2 + 1.5 * pulse);
    c += vec3(1.0) * exp(-dot(p, p) / (0.002 + 0.002 * pulse)) * pinch * 2.0;   // the dot
    frag = vec4(c, 1.0);
}
