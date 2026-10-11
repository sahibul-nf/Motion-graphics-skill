#!/usr/bin/env python3
"""Build an ASS caption track + preview/final ffmpeg scripts from beats.json + words.json.

Usage: python3 build_clip.py beats.json words.json <workdir>
Writes: captions.ass, preview.sh, final.sh in <workdir>.
"""
import json, os, subprocess, sys

def main():
    beats_p, words_p, wd = sys.argv[1], sys.argv[2], sys.argv[3]
    os.chdir(wd)
    b  = json.load(open(beats_p))
    ww = json.load(open(words_p))

    CLIP0, DUR = b["clip_start"], b["clip_dur"]
    PAD        = b.get("endcard_pad", 2.6)
    TOTAL      = DUR + PAD
    KW    = set(b.get("keywords", []))
    SKIP  = set(b.get("skip_words", []))
    REPL  = b.get("replace", {})
    ACC   = b["colors"]["accent"]; RED = b["colors"]["red"]
    AH = "&H00{:02X}{:02X}{:02X}&".format(int(ACC[4:6],16), int(ACC[2:4],16), int(ACC[0:2],16))
    RH = "&H00{:02X}{:02X}{:02X}&".format(int(RED[4:6],16), int(RED[2:4],16), int(RED[0:2],16))
    WH = "&HFFFFFF&"
    B, E = "{", "}"

    words = []
    for x in ww:
        if not x.get("word"): continue
        s, e, t = x["start"]-CLIP0, x["end"]-CLIP0, REPL.get(x["word"], x["word"])
        if e <= 0 or s >= DUR or t in SKIP or t == "": continue
        words.append((max(s,0.0), min(e,DUR), t))

    groups, cur = [], [words[0]]
    for p, n in zip(words, words[1:]):
        if n[0]-p[1] > 0.55 or len(cur) >= 5:
            groups.append(cur); cur = [n]
        else:
            cur.append(n)
    groups.append(cur)

    box = b.get("box")
    if box:
        groups = [g for g in groups if not (g[0][0] > box["start"]-0.05 and g[-1][1] < box["end"]+0.05)]

    def pop(o, big=False):
        p1, p2 = ("55","118") if big else ("58","112")
        return "\\alpha&HFF&\\fscx%s\\fscy%s\\t(%d,%d,\\alpha&H00&)\\t(%d,%d,\\fscx%s\\fscy%s)\\t(%d,%d,\\fscx100\\fscy100)" % (
            p1,p1,o,o+1,o+1,o+150,p2,p2,o+150,o+270)

    def kara(ws, we, o):
        a, bt = int(o), int(o+(we-ws)*1000)
        return "\\t(%d,%d,\\c%s)\\t(%d,%d,\\c%s)" % (a,a+80,AH,bt,bt+140,WH)

    def fmt(t):
        m, s = int(t//60), t % 60
        return "0:%02d:%05.2f" % (m, s)

    ev = []
    hk = b["hook"]
    h1 = [(w, o, c, fs) for (w,o,c,fs) in zip(hk["line1"].split(), [0.0,0.42,0.9], [AH,WH,AH], [112,76,120])]
    tags = "".join(B + pop(int(o), True) + "\\fnAnton\\fs%d\\c%s\\bord5\\shad3" % (fs,c) + E + t for t,o,c,fs in h1)
    px, py = hk["pos"]
    ev.append("Dialogue: 0,%s,%s,Hook,%d,%d,0,,,%s%s" % (
        fmt(0.15), fmt(hk["slam_at"]-0.01), 0, 0, B+"\\an5\\pos(%d,%d)" % (px,py)+E, tags))
    ev.append("Dialogue: 0,%s,%s,Hook,%d,%d,0,,,%s%s" % (
        fmt(hk["slam_at"]), fmt(hk["end"]), 0, 0,
        B+"\\an5\\pos(%d,%d)\\t(0,80,\\fscx145\\fscy145\\alpha&HFF&)\\t(80,81,\\alpha&H00&)"
        "\\t(81,220,\\fscx103\\fscy103)\\t(220,320,\\fscx100\\fscy100)"
        "\\fnAnton\\fs118\\c%s\\bord5\\shad3" % (px,py,WH) + E, hk["line2"].upper()))

    yf = b.get("caption_y_first", 1400); yc = b.get("caption_y", 1240)
    for g in groups:
        ls, le = g[0][0]-0.05, g[-1][1]+0.15
        y = yf if ls < hk["end"]+0.05 else yc
        parts = []
        for ws,we,t in g:
            o = max(int((ws-ls)*1000), 0)
            key = t.strip(",.?!") in KW or t in KW
            st = B+"\\fnAnton\\fs84\\c"+AH+"\\bord3\\shad2"+pop(o, True)+E if key else \
                 B+"\\fnCarlito\\fs66\\b1\\c"+WH+"\\bord3\\shad2"+pop(o)+kara(ws,we,o)+E
            parts.append(st+t+" ")
        ev.append("Dialogue: 0,%s,%s,Cap,540,%d,0,,,%s%s" % (fmt(ls), fmt(le), y,
                  (B+"\\an5\\pos(540,%d)"+E) % y, "".join(parts)))

    if box:
        bx, by = box["pos"]
        txt = "\\N".join(box["lines"])
        ev.append("Dialogue: 1,%s,%s,Box,%d,%d,0,,,%s%s" % (
            fmt(box["start"]), fmt(box["end"]), 0, 0,
            B+"\\an5\\pos(%d,%d)\\fad(100,180)\\t(0,140,\\fscx25\\fscy25)\\t(140,260,\\fscx106\\fscy106)"
            "\\t(260,340,\\fscx100\\fscy100)\\fnAnton\\fs74\\c%s" % (bx,by,WH) + E, txt))

    for s in b.get("stamps", []):
        sx, sy = s["pos"]; c = RH if s.get("color","red")=="red" else AH
        ev.append("Dialogue: 2,%s,%s,Stamp,%d,%d,0,,,%s%s" % (
            fmt(s["start"]), fmt(s["end"]), 0, 0,
            B+"\\an5\\pos(%d,%d)\\frz%d\\fad(80,150)\\t(0,120,\\fscx30\\fscy30)\\t(120,240,\\fscx112\\fscy112)"
            "\\t(240,320,\\fscx100\\fscy100)\\fnPermanent Marker\\fs%d\\c%s\\bord3\\shad2" % (sx,sy,s["rot"],s["size"],c) + E, s["text"]))

    ev.append("Dialogue: 3,%s,%s,Bar,0,0,0,,,%s%s" % (fmt(0), fmt(TOTAL), B +
        "\\an7\\pos(0,1504)\\c%s\\alpha&H30&\\fscx0.01\\t(0,%d,\\fscx100)\\p1" % (AH, int(DUR*1000)) + E,
        "m 0 0 l 1080 9"+B+"\\p"+E))

    ev.append("Dialogue: 4,%s,%s,Dim,540,960,0,,,%s%s" % (
        fmt(DUR-0.5), fmt(TOTAL), B+"\\an5\\pos(540,960)\\fad(320,0)\\p1"+E, "m 0 0 l 1080 1920"+B+"\\p"+E))
    for txt, sty, yy in b.get("credit", []):
        ev.append("Dialogue: 5,%s,%s,%s,540,%d,0,,,%s%s" % (
            fmt(DUR-0.25), fmt(TOTAL), sty, yy, B+"\\an5\\pos(540,%d)\\fad(260,0)" % yy + E, txt))

    styles = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "styles_head.ass")).read()
    open("captions.ass","w").write(styles + "\n".join(ev) + "\n")

    # ---- zoom/shake expressions ----
    T = "(in/30)"
    def ss(x): return "pow(min(max(%s,0),1),2)*(3-2*min(max(%s,0),1))" % (x,x)
    z = "1+0.03*min(%s,%s)/%s" % (T, DUR, DUR)
    for pb, pe, amp in b.get("punches", []):
        z += "+%s*(%s-%s)" % (amp, ss("(%s-%.2f)/0.28" % (T,pb)), ss("(%s-%.2f)/0.40" % (T,pe)))
    sx = "".join("+%d*sin((%s-%.2f)*90)*exp(-9*(%s-%.2f))*if(gt(%s-%.2f,0),1,0)" % (a,T,ts,T,ts,T,ts) for ts,a in b.get("shakes", []))
    sy = "".join("+%d*sin((%s-%.2f)*77)*exp(-9*(%s-%.2f))*if(gt(%s-%.2f,0),1,0)" % (int(a*0.5),T,ts,T,ts,T,ts) for ts,a in b.get("shakes", []))
    vx = "iw/2-(iw/zoom/2)"+sx
    vy = "ih/2-(ih/zoom/2)-ih*0.05*(zoom-1)/0.12"+sy

    # ---- synth SFX chains ----
    def boom(f, dur, vol):
        return "sine=frequency=%d:duration=%.2f,volume=%.2f,afade=t=in:d=0.006,afade=t=out:st=%.2f:d=%.2f" % (f,dur,vol,dur*0.2,dur*0.8)
    PRE = {"pop":  "sine=frequency=950:duration=0.05,afade=t=out:st=0.015:d=0.035,volume=0.5",
           "tick": "sine=frequency=1250:duration=0.04,afade=t=out:st=0.01:d=0.03,volume=0.42",
           "boom": boom(60, 0.55, 0.85),
           "whoosh":"anoisesrc=d=0.5:color=white:amplitude=0.35,lowpass=f=1400,highpass=f=300,afade=t=in:d=0.3,afade=t=out:st=0.32:d=0.18,volume=0.55"}
    fx = []
    for i,(name, ms) in enumerate(b.get("sfx", [])):
        fx.append("%s,adelay=%d:all=1[fx%d]" % (PRE[name], ms, i))
    nfx = len(fx)

    fc = ("[0:v]eq=contrast=1.05:saturation=1.12,crop=405:720:437:0,scale=1080:1920:flags=lanczos,fps=30,"
          "zoompan=z='%s':x='%s':y='%s':d=1:s=1080x1920:fps=30,vignette=angle=PI/4.6,noise=alls=5:allf=t,"
          "tpad=stop_mode=clone:stop_duration=%s[vb]" % (z, vx, vy, PAD))
    fc += ";[vb]subtitles=captions.ass:fontsdir=fonts[vout]"
    fc += ";[0:a]aformat=sample_rates=44100:channel_layouts=mono[vo]"
    if nfx: fc += ";" + ";".join(fx)
    if nfx: fc += ";" + "".join("[fx%d]"%i for i in range(nfx)) + "amix=inputs=%d:normalize=0[fxall]" % nfx
    mix = "[vo][fxall]amix=inputs=2:normalize=0," if nfx else "[vo],"
    fc += ";" + mix + "loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000,afade=t=out:st=%.2f:d=1.1[aout]" % (TOTAL-1.2)

    COMMON = "-y -ss %.2f -t %.2f -i %s -filter_complex \"%s\" -map \"[vout]\" -map \"[aout]\"" % (CLIP0, DUR, b.get("source","source.mp4"), fc)
    open("preview.sh","w").write("#!/bin/bash\ncd %s\nFFM=${FFM:-ffmpeg}\n$FFM %s -c:v libx264 -preset veryfast -crf 30 -pix_fmt yuv420p -s 378:672 -c:a aac -b:a 96k -movflags +faststart preview.mp4 2>&1 | tail -4\n" % (wd, COMMON))
    open("final.sh","w").write("#!/bin/bash\ncd %s\nFFM=${FFM:-ffmpeg}\n$FFM %s -c:v libx264 -preset veryfast -crf 21 -pix_fmt yuv420p -c:a aac -b:a 160k -movflags +faststart clip_final.mp4 2>&1 | tail -4\n" % (wd, COMMON))
    os.chmod("preview.sh", 0o755); os.chmod("final.sh", 0o755)
    print("captions.ass + preview.sh + final.sh written | events:", len(ev), "| groups:", len(groups))

if __name__ == "__main__":
    main()
