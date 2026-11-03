import cv2
import numpy as np
import os
import subprocess
import pickle
import pdb


def _h264_output_args():
    """Pick an H.264 encoder installed with this ffmpeg.

    The RoboTwin environment ships ffmpeg with libopenh264, not libx264.
    libopenh264 does not accept libx264's ``-crf`` flag.
    """
    try:
        probe = subprocess.run(
            ["ffmpeg", "-hide_banner", "-encoders"],
            capture_output=True,
            text=True,
            check=False,
        )
        encoders = probe.stdout
    except OSError:
        encoders = ""
    if "libx264" in encoders:
        return ["-vcodec", "libx264", "-crf", "23"]
    if "libopenh264" in encoders:
        return ["-vcodec", "libopenh264", "-b:v", "2M"]
    return ["-vcodec", "mpeg4", "-q:v", "5"]


def images_to_video(imgs: np.ndarray, out_path: str, fps: float = 30.0, is_rgb: bool = True) -> None:
    if (not isinstance(imgs, np.ndarray) or imgs.ndim != 4 or imgs.shape[3] not in (3, 4)):
        raise ValueError("imgs must be a numpy.ndarray of shape (N, H, W, C), with C equal to 3 or 4.")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    n_frames, H, W, C = imgs.shape
    if C == 3:
        pixel_format = "rgb24" if is_rgb else "bgr24"
    else:
        pixel_format = "rgba"
    ffmpeg = subprocess.Popen(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-f",
            "rawvideo",
            "-pixel_format",
            pixel_format,
            "-video_size",
            f"{W}x{H}",
            "-framerate",
            str(fps),
            "-i",
            "-",
            "-pix_fmt",
            "yuv420p",
            *_h264_output_args(),
            f"{out_path}",
        ],
        stdin=subprocess.PIPE,
    )
    ffmpeg.stdin.write(imgs.tobytes())
    ffmpeg.stdin.close()
    if ffmpeg.wait() != 0:
        raise IOError(f"Cannot open ffmpeg. Please check the output path and ensure ffmpeg is supported.")

    print(
        f"🎬 Video is saved to `{out_path}`, containing \033[94m{n_frames}\033[0m frames at {W}×{H} resolution and {fps} FPS."
    )
