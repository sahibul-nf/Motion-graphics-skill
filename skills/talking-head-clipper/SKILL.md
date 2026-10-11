---
name: talking-head-clipper
description: Turn one moment from a long talking-head / lecture / kajian recording into a branded 9:16 social clip with word-synced kinetic captions, punch zooms, marker stamps, synthesized SFX and a credit end card. Renders locally with ffmpeg only (libass), no After Effects. Companion to motion-video-director; use it when the input is existing footage and the deliverable is one short clip.
---

# Talking-head clipper

Cut one moment out of long footage and produce a finished 9:16 clip at the motion-video-director quality bar: kinetic word-by-word captions locked to word timestamps, punch zooms on key words, marker stamps on jokes, SFX hits, a hook in the first 3 seconds and an end card that credits the source channel.

Follow the parent skill (motion-video-director) for gates, project structure, QA contact sheets and the render log. This skill only adds the clip pipeline.

## Workflow

1. **Pick the moment.** Transcribe the full source with word timestamps (faster-whisper, word_timestamps=True). Read the transcript in windows, choose the single best beat (hook + payoff), note the source channel to credit. → **Approve the moment and length.**
2. **Beat sheet.** Fill `beats.json` (schema below): clip_start/clip_dur, keywords, stamps, punch/shake times, SFX hits, end-card credit lines. Words inside the hook/punchline-box windows are excluded from the caption track automatically when you list their window in `box`.
3. **Build.** `python3 scripts/build_clip.py beats.json words.json .` writes `captions.ass`, `preview.sh` (small QA render) and `final.sh` (delivery render).
4. **Preview loop.** Run `preview.sh`, extract stills at every effect moment, tile them into a contact sheet and LOOK at it. Fix, re-render, repeat. Only then run `final.sh`.
5. **Deliver.** 1080x1920 H.264 yuv420p, AAC 48 kHz, `+faststart`, loudness -14 LUFS / -1.5 dBTP. Credit the source channel in the end card and in the post text.

## beats.json schema (all times seconds, clip-relative)

```
{
  "clip_start": 1983.3,        // absolute seconds in the source file
  "clip_dur": 49.3,
  "endcard_pad": 2.6,          // freeze-frame tail for the end card
  "keywords": ["duit","tenang"],            // rendered big + accent colour
  "skip_words": ["ee","gelisa,"],           // removed from captions
  "replace": {"kemascit": "ke masjid"},     // obvious transcription fixes
  "colors": {"accent": "FFD84A", "red": "FF5555"},   // RGB hex
  "hook": {"line1": "duit itu senang,", "line2": "bukan tenang",
           "slam_at": 1.55, "end": 2.55, "pos": [540, 970]},
  "box": {"lines": ["duit itu senang,", "bukan tenang"],
          "start": 14.9, "end": 18.5, "pos": [540, 1150]},   // optional highlight box; captions inside this window are skipped
  "stamps": [{"text": "tenang gak?", "start": 26.78, "end": 28.4,
              "pos": [740, 300], "rot": -7, "color": "FF5555", "size": 70}],
  "punches": [[14.94, 17.0, 0.12], [26.74, 28.2, 0.10]],     // [start, hold_end, zoom_amp]
  "shakes":  [[1.55, 14], [15.88, 10]],                       // [at, amp_px]
  "sfx":     [["pop", 500], ["boom", 1550], ["whoosh", 14550]], // presets: pop/boom/whoosh/tick
  "credit":  [["kajian: <speaker>", "Cred", 880],
              ["sumber: <channel>", "Cred2", 975],
              ["<watermark>", "CredM", 1065]],
  "caption_y": 1240, "caption_y_first": 1400
}
```

`words.json` is a flat list of `{"word", "start", "end"}` in absolute seconds (faster-whisper output).

## Branding

Brand tokens live in `brands/<brand>.json` (name, channel URLs, end-card watermark, palette). `brands/nourbit.json` ships as an example. Never invent brand colours: read them from the brand's own assets, and leave a slot empty rather than guessing. Every clip made from someone else's footage credits their channel in the end card.

## Render gotchas (each of these cost a debugging loop once)

- `-t <dur>` must be an INPUT option (`-ss X -t D -i src.mp4`). As an output option it caps the stream at `clip_dur` and silently eats the `tpad` end card.
- One brace group per word. Nested `{{...{...}...}}` renders the override tags as literal on-screen text.
- `zoompan` has no `t`; key all zoom/shake expressions to `(in/30)` and force `fps=30` before it.
- Word gaps need a literal space AFTER the closing brace (`}word `), or caption words run together.
- Word pop-in: static `\alpha&HFF&\fscxNN` before a `\t(o,o+1,\alpha&H00&)` snap, then overshoot. `\t(0,o,\alpha&HFF&)` alone fades the word OUT first, which reads as a glitch.
- Animated drawing widths start from the style value: prefix `\fscx0.01` before `\t(0,T,\fscx100)`.
- Synth SFX: mix mono sources with `amix=normalize=0` at low volume under the VO, `adelay=<ms>:all=1`, then one `loudnorm`.

## Quality bar

Intensity 4-5 for social clips: every emphasis gets motion (pop, zoom, stamp or hit), dead air over 1.5 s is cut, captions sit in the 60-70 % height band inside the 9:16 safe zones (top ~220 px, bottom ~420 px, right ~140 px), and the hook lands inside 3 s. Contact sheets over the full duration before delivery.
