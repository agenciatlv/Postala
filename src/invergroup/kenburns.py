"""No-AI fallback for a scene: slow zoom over the original render (brief: after 2 failed generations).

Usage: python3 src/invergroup/kenburns.py <image> <out.mp4> [--zoom 1.06] [--cx 0.5] [--cy 0.5] [--seconds 5]
cx/cy are the zoom's focal point as a fraction of the frame (e.g. the couple, the balcony door).
"""

import argparse
import subprocess

import imageio_ffmpeg

ap = argparse.ArgumentParser()
ap.add_argument("image")
ap.add_argument("out")
ap.add_argument("--zoom", type=float, default=1.06)
ap.add_argument("--cx", type=float, default=0.5)
ap.add_argument("--cy", type=float, default=0.5)
ap.add_argument("--seconds", type=float, default=5)
a = ap.parse_args()

fps = 30
frames = int(a.seconds * fps)
# Upscale 4x before zoompan so the sub-pixel motion stays smooth, then render back at 1080x1920.
z = f"1+({a.zoom}-1)*on/{frames - 1}"
x = f"(iw-iw/zoom)*{a.cx}"
y = f"(ih-ih/zoom)*{a.cy}"
vf = (
    "scale=4320:7680:flags=lanczos,"
    f"zoompan=z='{z}':x='{x}':y='{y}':d={frames}:s=1080x1920:fps={fps},"
    "format=yuv420p"
)
subprocess.run(
    [imageio_ffmpeg.get_ffmpeg_exe(), "-v", "error", "-y", "-i", a.image, "-vf", vf,
     "-frames:v", str(frames), "-c:v", "libx264", "-crf", "15", a.out],
    check=True,
)
print(f"wrote {a.out}")
