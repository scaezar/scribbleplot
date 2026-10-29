"""
placeholder sound design for the bank job, synthesised from scratch with numpy.

no samples, no network: every sound is built from sines and filtered noise, then
placed on the cue sheet below. the cue times are measured from the diorama
repo's bank-job capture (media/bank-job.mp4, 48.1 s loop), so this track can be
laid straight onto that video to test the sound before the real scene exists.

usage: python3 synth.py out.wav
"""
import sys
import wave

import numpy as np

SR = 48000
T = 48.1
N = int(SR * T)
rng = np.random.default_rng(7)

mixL = np.zeros(N)
mixR = np.zeros(N)


# ---------------------------------------------------------------- helpers

def tt(n):
    return np.arange(n) / SR


def noise(n):
    return rng.standard_normal(n)


def norm(x):
    p = np.abs(x).max()
    return x / p if p > 0 else x


def filt(x, lo=None, hi=None, order=2):
    """zero-phase butterworth-magnitude band filter in the frequency domain."""
    n = len(x)
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1 / SR)
    H = np.ones_like(f)
    if lo:
        H *= 1 / np.sqrt(1 + (lo / np.maximum(f, 1e-3)) ** (2 * order))
    if hi:
        H *= 1 / np.sqrt(1 + (f / hi) ** (2 * order))
    return np.fft.irfft(X * H, n)


def conv(a, b):
    n = len(a) + len(b) - 1
    nfft = 1 << (n - 1).bit_length()
    return np.fft.irfft(np.fft.rfft(a, nfft) * np.fft.rfft(b, nfft), nfft)[:n]


def env(n, a, d):
    """linear attack of a seconds, exponential decay with time constant d."""
    t = tt(n)
    e = np.minimum(t / a, 1) if a > 0 else np.ones(n)
    return e * np.exp(-np.maximum(t - a, 0) / d)


def fade(n, fin, fout):
    e = np.ones(n)
    i, o = int(fin * SR), int(fout * SR)
    if i:
        e[:i] *= np.linspace(0, 1, i)
    if o:
        e[-o:] *= np.linspace(1, 0, o)
    return e


def curve(t, points):
    """piecewise-linear automation: points = [(time, value), ...]."""
    xs, ys = zip(*points)
    return np.interp(t, xs, ys)


def smooth_noise(n, rate):
    """band-limited random wobble in [-1, 1] at roughly `rate` Hz."""
    k = int(n * rate / SR) + 3
    ctrl = rng.uniform(-1, 1, k)
    return np.interp(np.arange(n) * rate / SR, np.arange(k), ctrl)


def add(sig, t0, db=0.0, pan=0.0):
    """place a mono sound at t0 (seconds), wrapping past the loop seam.

    pan is -1 (left) .. 1 (right), a number or an array as long as sig.
    """
    g = 10 ** (db / 20)
    a = (np.asarray(pan) + 1) * np.pi / 4
    gl, gr = np.cos(a) * np.sqrt(2), np.sin(a) * np.sqrt(2)
    idx = (int(round(t0 * SR)) + np.arange(len(sig))) % N
    mixL[idx] += sig * g * gl
    mixR[idx] += sig * g * gr


# ---------------------------------------------------------------- sounds

def engine(dur, rpm_fn, rough=0.25, bright=1800):
    n = int(dur * SR)
    t = tt(n)
    rpm = rpm_fn(t)
    f = rpm / 60 * 2  # four-cylinder four-stroke firing rate
    ph = 2 * np.pi * np.cumsum(f) / SR
    sig = np.zeros(n)
    for k in range(1, 13):
        sig += np.sin(k * ph + rng.uniform(0, 2 * np.pi)) / k ** 0.9
    cyc = ph / (2 * np.pi)
    jit = 1 + rough * rng.standard_normal(int(cyc.max()) + 3)
    sig *= np.interp(cyc, np.arange(len(jit)), jit)
    combustion = filt(noise(n), 100, 1500) * (0.5 + 0.5 * np.sin(ph)) ** 4
    sig = norm(sig) + 0.5 * norm(combustion)
    load = 0.55 + 0.45 * np.clip((rpm - 800) / 4000, 0, 1)
    return norm(filt(sig, 25, bright)) * load


def car_door(slam=True):
    n = int(0.45 * SR)
    t = tt(n)
    latch = filt(noise(n), 2500, 7000) * env(n, 0.0005, 0.006)
    if not slam:
        return norm(latch + 0.3 * filt(noise(n), 300, 1500) * env(n, 0.001, 0.02))
    f = 48 + 45 * np.exp(-t / 0.04)
    thump = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.001, 0.09)
    body = filt(noise(n), 200, 1800) * env(n, 0.001, 0.035)
    rattle = sum(np.sin(2 * np.pi * fr * t) for fr in (410, 655, 880)) * env(n, 0.002, 0.08)
    return norm(thump + 0.7 * body + 0.15 * rattle + 0.4 * np.roll(latch, int(0.004 * SR)))


def trunk_slam():
    return norm(np.concatenate([car_door(True), np.zeros(SR // 10)]) * 1.0
                + 0.6 * np.concatenate([np.zeros(SR // 10), car_door(True)]))


def glass_door(burst=False):
    n = int((0.9 if burst else 0.6) * SR)
    t = tt(n)
    clack = filt(noise(n), 1000, 5000) * env(n, 0.0005, 0.01) + np.sin(2 * np.pi * 1250 * t) * env(n, 0.0005, 0.03)
    rattle = np.zeros(n)
    for fr in (2350, 3120, 4410, 5230, 2790):
        d = rng.uniform(0.12, 0.3) * (1.6 if burst else 1)
        rattle += rng.uniform(0.4, 1) * np.sin(2 * np.pi * fr * t + rng.uniform(0, 6)) * env(n, 0.001, d)
    thump = np.sin(2 * np.pi * 85 * t) * env(n, 0.001, 0.12 if burst else 0.06)
    return norm(0.7 * clack + 0.35 * rattle + (1.0 if burst else 0.5) * thump)


def step(run=False, stone=False):
    n = int(0.12 * SR)
    t = tt(n)
    hi = rng.uniform(1400, 2600) * (1.3 if stone else 1)
    s = filt(noise(n), 120, hi, 1) * env(n, 0.002, 0.03 if run else 0.035)
    s += 0.5 * np.sin(2 * np.pi * rng.uniform(80, 110) * t) * env(n, 0.001, 0.03)
    if run:
        scuff = filt(noise(n), 1500, 5000) * env(n, 0.002, 0.015)
        s += 0.35 * np.roll(scuff, int(0.03 * SR))
    return norm(s) * 10 ** (rng.uniform(-3, 0) / 20)


def footsteps(t0, t1, people, interval, db, pan0, pan1, run=False, stone=False):
    for _ in range(people):
        t = t0 + rng.uniform(0, interval)
        while t < t1:
            frac = (t - t0) / max(t1 - t0, 1e-6)
            add(step(run, stone), t + rng.normal(0, 0.012), db, pan0 + (pan1 - pan0) * frac)
            t += interval * rng.uniform(0.92, 1.08)


def bell(dur, rate=17.0, f0=1150):
    n = int(dur * SR)
    k = int(0.35 * SR)
    kt = tt(k)
    kernel = sum(a * np.sin(2 * np.pi * f0 * r * kt) * np.exp(-kt / d)
                 for r, a, d in ((1.0, 1.0, 0.25), (2.76, 0.6, 0.15), (5.40, 0.35, 0.08), (8.93, 0.2, 0.05)))
    imp = np.zeros(n)
    for ti in np.arange(0, dur, 1 / rate):
        imp[int(ti * SR)] = 1 + 0.15 * rng.standard_normal()
    ring = conv(imp, kernel)
    buzz = conv(imp, filt(noise(int(0.004 * SR)), 2000, 9000))
    buzz = np.pad(buzz, (0, len(ring) - len(buzz)))
    return norm(norm(ring) + 0.25 * norm(buzz))


def siren(dur, mode="wail"):
    n = int(dur * SR)
    t = tt(n)
    if mode == "wail":
        x = (np.sin(2 * np.pi * t / 2.6 - np.pi / 2) + 1) / 2
        f = 650 + 800 * x
    else:  # yelp
        x = (t / 0.34) % 1
        f = 700 + 750 * x ** 0.6
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.sin(ph) + 0.35 * np.sin(3 * ph) + 0.15 * np.sin(5 * ph)
    return norm(filt(s, 300, 5000))


def wind_down(sig, start, length=0.6):
    """drop the last part of a siren in pitch and level, like the motor spinning down."""
    i, m = int(start * SR), int(length * SR)
    seg = sig[i:i + m]
    warp = np.cumsum(np.exp(-tt(len(seg)) / 0.35))
    out = np.interp(warp, np.arange(len(seg)), seg) * np.linspace(1, 0, len(seg)) ** 2
    return np.concatenate([sig[:i], out])


def chirp(f0, f1, dur, shape=1.0):
    n = int(dur * SR)
    t = tt(n) / dur
    f = f0 + (f1 - f0) * t ** shape
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t) ** 2


def screech(dur, f=2300):
    n = int(dur * SR)
    fv = f + 140 * smooth_noise(n, 9) + 40 * smooth_noise(n, 60)
    ph = 2 * np.pi * np.cumsum(fv) / SR
    tone = np.sin(ph) + 0.5 * np.sin(1.37 * ph + 1) + 0.25 * np.sin(2.1 * ph)
    hiss = filt(noise(n), 1200, 5000)
    flutter = 0.75 + 0.25 * smooth_noise(n, 35)
    return norm((norm(tone) + 0.5 * norm(hiss)) * flutter * fade(n, 0.03, min(0.3, dur / 3)))


def coins(dur=0.5, count=14):
    n = int(dur * SR)
    out = np.zeros(n)
    for _ in range(count):
        m = int(0.12 * SR)
        p = sum(np.sin(2 * np.pi * rng.uniform(3000, 8000) * tt(m)) for _ in range(2)) * env(m, 0.0005, 0.03)
        i = int(rng.uniform(0, dur - 0.13) * SR)
        out[i:i + m] += p * rng.uniform(0.3, 1)
    return norm(out)


def bag_thud():
    n = int(0.3 * SR)
    t = tt(n)
    return norm(filt(noise(n), 60, 600) * env(n, 0.002, 0.05) + 0.6 * np.sin(2 * np.pi * 70 * t) * env(n, 0.001, 0.06))


def wings(dur=0.7):
    n = int(dur * SR)
    t = tt(n)
    flap = (0.5 + 0.5 * np.sin(2 * np.pi * 13 * t)) ** 6
    return norm(filt(noise(n), 400, 3000) * flap * fade(n, 0.02, 0.3))


# ---------------------------------------------------------------- cue sheet
# times are loop seconds measured off the capture (see analysis in PLAN.md).

# street bed: two decorrelated noise beds plus slow traffic swells.
t = tt(N)
swell = 0.65 + 0.35 * np.sin(2 * np.pi * t / (T / 4)) * np.sin(2 * np.pi * t / (T / 3) + 1)
for side, pan in ((0, -0.7), (1, 0.7)):
    bed = norm(filt(noise(N), 70, 700, 1)) + 0.25 * norm(filt(noise(N), 300, 3500, 1))
    add(norm(bed) * swell, 0, -26, pan)

# birds until the alarm, then they scatter, and come back once it is quiet.
for t0 in list(np.arange(0.6, 12.0, 1.7)) + list(np.arange(39.5, 47.5, 1.9)):
    t0 += rng.uniform(-0.4, 0.4)
    base = rng.uniform(3200, 4800)
    for j in range(rng.integers(2, 5)):
        add(chirp(base, base * rng.uniform(1.15, 1.4), rng.uniform(0.05, 0.1), 0.6),
            t0 + j * rng.uniform(0.09, 0.14), -29, rng.uniform(-0.8, 0.8))
add(wings(), 12.55, -24, 0.4)
add(wings(), 12.7, -27, -0.3)

# the sedan: one continuous engine from its entrance at 47.4 (wrapping into the
# loop start) through idle, the peel-out at 25.2 and its exit past 28.
u0 = 47.4 - T  # entrance, expressed before 0 so it wraps
sedan_rpm = [(-0.8, 2600), (0.8, 2300), (2.4, 1400), (3.3, 820), (24.9, 840), (25.05, 3200),
             (25.6, 4600), (26.4, 4900), (26.55, 3300), (27.4, 4700), (29.5, 4800)]
sedan_db = [(-0.8, -16), (0.6, -13), (3.0, -16), (3.6, -27), (24.8, -27), (25.1, -9),
            (27.3, -9), (28.4, -20), (29.5, -60)]
sedan_pan = [(-0.8, -0.8), (3.3, -0.45), (25.2, -0.45), (28.2, 0.85)]
dur = 29.5 - u0
eng = engine(dur, lambda x: curve(x + u0, sedan_rpm))
ut = tt(len(eng)) + u0
add(eng * 10 ** (curve(ut, sedan_db) / 20), u0, 0, curve(ut, sedan_pan))
add(chirp(3100, 2900, 0.28) * 0.6, 2.85, -28, -0.45)  # soft brake squeak

# robbers get out: door latches, then slams.
for d in (4.1, 4.22, 4.4):
    add(car_door(False), d, -20, -0.45)
for d in (4.9, 5.05, 5.22):
    add(car_door(True), d, -12, -0.45)

# walk to the bank, then up the stone steps; door opens and swings shut.
footsteps(5.3, 7.6, 3, 0.42, -20, -0.45, -0.1)
footsteps(7.6, 9.2, 3, 0.46, -20, -0.1, 0.0, stone=True)
add(glass_door(), 9.2, -12, 0.0)
add(glass_door(), 9.75, -21, 0.0)

# alarm: hard hit at 12.45, sits under the action, ducks for the getaway.
alarm_len = 37.25 - 12.45
al = bell(alarm_len)
at = tt(len(al))
al_db = curve(at + 12.45, [(12.45, -5), (14.3, -5), (15.0, -15), (25.0, -15), (25.3, -19),
                           (29.2, -19), (29.8, -16), (37.25, -16), (40, -16)])
add(al * 10 ** (al_db / 20), 12.45, 0, 0.1)

# robbers burst out, run for the car, load the bags into the trunk.
add(glass_door(burst=True), 16.85, -9, 0.0)
footsteps(17.0, 20.3, 3, 0.28, -16, 0.0, -0.45, run=True)
add(car_door(False), 20.45, -19, -0.45)  # trunk unlatched
for i, b in enumerate((21.0, 21.45, 21.9, 22.3)):
    add(bag_thud(), b, -15, -0.45)
    add(coins(0.4, 9), b + 0.02, -24, -0.45)
add(trunk_slam(), 22.55, -13, -0.45)
for d in (22.9, 23.1, 23.35):
    add(car_door(True), d, -12, -0.45)

# peel-out: tyres scream as it launches.
add(screech(1.15), 25.25, -10, curve(25.25 + tt(int(1.15 * SR)), [(25.25, -0.45), (26.4, 0.1)]))

# sirens: wail from far off, a yelp joins, both arrive at 28.6 and spin down.
sir_end = 29.4
for mode, start, pan in (("wail", 23.6, -0.55), ("yelp", 25.0, -0.35)):
    s = siren(sir_end - start, mode)
    s = wind_down(s, 28.85 - start)
    st = tt(len(s)) + start
    near = np.clip((st - 24.0) / 2.6, 0, 1)
    s = near * s + (1 - near) * filt(s, None, 900)
    gain = curve(st, [(start, -44), (25.2, -30), (26.4, -17), (27.6, -10), (29.4, -10)])
    add(s * 10 ** (gain / 20), start, -1 if mode == "wail" else -4, pan)

# cruisers: engines in, brakes, idle with doors, then away with one chirp.
cr_rpm = [(26.3, 3200), (28.2, 2600), (28.8, 1100), (29.3, 850), (42.1, 860), (42.3, 2600),
          (44.0, 3800), (46.0, 4200)]
cr_db = [(26.3, -30), (27.3, -15), (28.8, -18), (29.4, -29), (42.0, -29), (42.4, -13),
         (44.6, -14), (45.8, -40), (46.0, -60)]
cr_pan = [(26.3, -0.85), (28.8, -0.45), (42.2, -0.45), (45.6, 0.9)]
for k, off in enumerate((0.0, 0.35)):
    e = engine(46.0 - 26.3, lambda x: curve(x + 26.3 - off, cr_rpm), rough=0.18, bright=1500)
    et = tt(len(e)) + 26.3
    add(e * 10 ** (curve(et - off, cr_db) / 20), 26.3, -2 * k, curve(et - off, cr_pan))
add(screech(0.45, 3300), 28.3, -19, -0.5)
add(screech(0.4, 3500), 28.6, -21, -0.4)
for d in (29.3, 29.42, 29.58, 29.7):
    add(car_door(False), d, -21, -0.5)
for d in (29.9, 30.05, 30.22, 30.35):
    add(car_door(True), d, -13, -0.5)

# officers rush the door, go in, come back out, walk back.
footsteps(30.2, 33.8, 4, 0.28, -16, -0.5, 0.0, run=True)
add(glass_door(burst=True), 33.8, -11, 0.0)
add(glass_door(), 36.3, -12, 0.0)
footsteps(36.4, 37.4, 4, 0.48, -20, 0.0, -0.1, stone=True)
footsteps(37.4, 40.6, 4, 0.5, -20, -0.1, -0.5)
for d in (40.6, 40.75, 40.9, 41.0):
    add(car_door(False), d, -21, -0.5)
for d in (41.3, 41.5, 41.75, 42.0):
    add(car_door(True), d, -13, -0.5)
add(chirp(520, 1400, 0.28, 0.7) + 0.0, 42.25, -12, -0.4)  # whoop
add(chirp(1400, 600, 0.25, 1.3), 42.53, -12, -0.35)


# ---------------------------------------------------------------- master

# outdoor reverb: a few building slaps plus a short diffuse tail.
ir_n = int(0.9 * SR)
ir = filt(noise(ir_n), 200, 5000) * env(ir_n, 0.01, 0.22)
for d, g in ((0.017, 0.5), (0.031, 0.35), (0.047, 0.25)):
    ir[int(d * SR)] += g * np.sqrt(ir_n) * 0.02
ir = norm(ir)
wet = 0.12
outL = mixL + wet * conv(mixL, ir)[:N] / 30
outR = mixR + wet * conv(mixR, ir)[:N] / 30

peak = max(np.abs(outL).max(), np.abs(outR).max())
outL, outR = np.tanh(outL / peak * 1.1) * 0.89, np.tanh(outR / peak * 1.1) * 0.89
pcm = (np.stack([outL, outR], axis=1) * 32767).astype("<i2")

with wave.open(sys.argv[1] if len(sys.argv) > 1 else "bank-job-sfx.wav", "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
