"""Assemble the Invergroup 30s vertical commercial from the chosen clips.

Timeline (brief): scene 1 at 0s, scenes 2-6 every 4s, scene 7 at 24s for 6s.
Crossfades of 0.4s are centred on each cut, so every scene still starts on its mark.

Usage (from the repo root):
  python3 src/invergroup/assemble.py --voice Claudia \
      --clip 2=invergroup/runway/cena02_take1.mp4 ... \
      [--logo invergroup/assets/logo.png] [--music invergroup/assets/trilha.mp3]
"""

import argparse
import subprocess
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FF = imageio_ffmpeg.get_ffmpeg_exe()
ROOT = Path("invergroup")
XF = 0.4  # crossfade length
HALF = XF / 2
STARTS = [0, 4, 8, 12, 16, 20, 24]
DURS = [4, 4, 4, 4, 4, 4, 6]
TOTAL = 30
TAGLINE_AT = 26
VOICE_LEAD = 0.3  # each line starts this long after its scene


def run(*args):
    subprocess.run([FF, "-v", "error", "-y", *map(str, args)], check=True)


def tagline_png(path: Path, with_logo_space: bool):
    """Transparent 1080x1920 overlay with "Donde empieza todo." in the lower third."""
    img = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # dark gradient over the lower third so logo and text read over the pool and gardens
    for yy in range(1150, 1920):
        draw.line([(0, yy), (1080, yy)], fill=(0, 0, 0, int(170 * ((yy - 1150) / 770) ** 1.3)))
    font = ImageFont.truetype(str(ROOT / "assets/CormorantGaramond.ttf"), 92)
    font.set_variation_by_name("Medium")
    text = "Donde empieza todo."
    w = draw.textlength(text, font=font)
    y = 1560 if with_logo_space else 1440
    # soft shadow for legibility over bright sky/pool areas
    shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).text(((1080 - w) / 2 + 3, y + 3), text, font=font, fill=(0, 0, 0, 150))

    img = Image.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(6)), img)
    ImageDraw.Draw(img).text(((1080 - w) / 2, y), text, font=font, fill=(255, 255, 255, 255))
    img.save(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", required=True, help="folder under invergroup/voice/")
    ap.add_argument("--clip", action="append", default=[], help="scene=path for scenes 2-6")
    ap.add_argument("--logo", type=Path)
    ap.add_argument("--music", type=Path)
    ap.add_argument("--out", type=Path, default=ROOT / "export/invergroup_comercial_30s_9x16.mp4")
    a = ap.parse_args()

    clips = {1: ROOT / "pack/cena01_aerea_pan.mp4", 7: ROOT / "pack/cena07_torres_pan.mp4"}
    for c in a.clip:
        k, v = c.split("=", 1)
        clips[int(k)] = Path(v)
    missing = [i for i in range(1, 8) if i not in clips]
    if missing:
        raise SystemExit(f"missing clips for scenes {missing}")

    work = ROOT / "build"
    work.mkdir(exist_ok=True)
    a.out.parent.mkdir(parents=True, exist_ok=True)

    # 1. Normalise every scene to 1080x1920/30fps with the extra length the crossfades eat.
    #    First scene needs +HALF at the end, middle scenes +HALF at both ends, last +HALF at the start.
    #    Clips are always taken from their first frame (the one identical to the render); where a clip
    #    is too short, its last frame is held.
    norm = []
    for i in range(1, 8):
        length = DURS[i - 1] + (HALF if i < 7 else 0) + (HALF if i > 1 else 0)
        out = work / f"s{i}.mp4"
        run(
            "-i", clips[i],
            "-vf",
            "scale=1080:1920:flags=lanczos,setsar=1,fps=30,"
            f"tpad=stop_mode=clone:stop_duration={length},trim=duration={length},setpts=PTS-STARTPTS,format=yuv420p",
            "-an", "-c:v", "libx264", "-crf", "15", "-preset", "medium", out,
        )
        norm.append(out)

    # 2. Crossfade chain. Transition k is centred on the cut at STARTS[k].
    inputs, chain, prev = [], [], "0:v"
    for p in norm:
        inputs += ["-i", p]
    for k in range(1, 7):
        label = f"v{k}"
        chain.append(f"[{prev}][{k}:v]xfade=transition=fade:duration={XF}:offset={STARTS[k] - HALF:.3f}[{label}]")
        prev = label
    video = prev

    # 3. Overlays: tagline (+ logo if provided) from 26s, fade to black in the last 0.5s.
    n = len(norm)
    tag = work / "tagline.png"
    tagline_png(tag, with_logo_space=a.logo is not None)
    inputs += ["-loop", "1", "-t", str(TOTAL), "-i", tag]
    chain.append(f"[{n}:v]format=rgba,fade=in:st={TAGLINE_AT}:d=0.8:alpha=1[tag]")
    chain.append(f"[{video}][tag]overlay=0:0[vt]")
    video = "vt"
    n += 1
    if a.logo:
        inputs += ["-loop", "1", "-t", str(TOTAL), "-i", a.logo]
        chain.append(f"[{n}:v]scale=560:-1,format=rgba,fade=in:st={TAGLINE_AT}:d=0.8:alpha=1[logo]")
        chain.append(f"[{video}][logo]overlay=(W-w)/2:1300[vl]")
        video = "vl"
        n += 1
    chain.append(f"[{video}]fade=out:st={TOTAL - 0.5}:d=0.5,trim=duration={TOTAL}[vout]")

    # 4. Voice lines placed on their scene marks.
    voice_labels = []
    for i in range(1, 8):
        inputs += ["-i", ROOT / f"voice/{a.voice}/linea{i}.mp3"]
        delay = int((STARTS[i - 1] + VOICE_LEAD) * 1000)
        chain.append(f"[{n}:a]aresample=48000,aformat=channel_layouts=stereo,adelay={delay}|{delay}[l{i}]")
        voice_labels.append(f"[l{i}]")
        n += 1
    chain.append(f"{''.join(voice_labels)}amix=inputs=7:normalize=0,apad=whole_dur={TOTAL}[voice]")

    if a.music:
        # Music ducked ~12 dB under the voice while it speaks, then one loudness pass on the mix.
        inputs += ["-i", a.music]
        chain.append(f"[{n}:a]aresample=48000,aformat=channel_layouts=stereo,atrim=duration={TOTAL},volume=-6dB[mus]")
        chain.append("[voice]asplit=2[vmix][vkey]")
        chain.append("[mus][vkey]sidechaincompress=threshold=0.02:ratio=8:attack=20:release=400:makeup=1[duck]")
        chain.append("[vmix][duck]amix=inputs=2:normalize=0[mix]")
        mix = "mix"
    else:
        mix = "voice"
    chain.append(
        f"[{mix}]loudnorm=I=-14:TP=-1.5:LRA=11,afade=out:st={TOTAL - 0.5}:d=0.5,atrim=duration={TOTAL}[aout]"
    )

    run(
        *inputs,
        "-filter_complex", ";".join(chain),
        "-map", "[vout]", "-map", "[aout]",
        "-c:v", "libx264", "-crf", "17", "-preset", "slow", "-pix_fmt", "yuv420p", "-r", "30",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-movflags", "+faststart", "-t", TOTAL,
        a.out,
    )
    print(f"exported {a.out}")


if __name__ == "__main__":
    main()
