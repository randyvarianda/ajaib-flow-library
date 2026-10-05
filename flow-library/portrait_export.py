from pathlib import Path
import subprocess
import sys
import tempfile

import imageio_ffmpeg


def portrait_get(handler):
    if handler.path != '/portrait-health':
        return False
    handler.send_response(200)
    handler.send_header('Content-Length', '2')
    handler.end_headers()
    handler.wfile.write(b'OK')
    return True


def portrait_post(handler):
    if handler.path != '/export-portrait-mp4':
        return False
    try:
        length = int(handler.headers.get('Content-Length', 0))
        fps = int(handler.headers.get('X-Frame-Rate', '30'))
        if not 0 < length <= 100 * 1024 * 1024 or fps not in (30, 60):
            handler.send_error(400, 'Invalid recording size or frame rate')
            return True
        with tempfile.TemporaryDirectory(prefix='flow-portrait-') as directory:
            source = Path(directory) / 'capture.webm'
            source.write_bytes(handler.rfile.read(length))
            output = Path(directory) / 'portrait.mp4'
            result = subprocess.run([
                imageio_ffmpeg.get_ffmpeg_exe(), '-hide_banner', '-loglevel', 'error',
                '-y', '-i', str(source), '-t', '15', '-an',
                '-vf', f'scale=1080:1920:flags=lanczos,setsar=1,fps={fps}',
                '-c:v', 'libx264', '-preset', 'medium', '-crf', '16',
                '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(output)
            ], capture_output=True, timeout=180)
            if result.returncode:
                raise ValueError('Invalid video recording')
            data = output.read_bytes()
        handler.send_response(200)
        handler.send_header('Content-Type', 'video/mp4')
        handler.send_header('Content-Length', str(len(data)))
        handler.send_header('Content-Disposition', 'attachment; filename="flow-9x16.mp4"')
        handler.end_headers()
        handler.wfile.write(data)
    except (ValueError, subprocess.TimeoutExpired, OSError):
        handler.send_error(400, 'Could not convert the video recording')
    return True
