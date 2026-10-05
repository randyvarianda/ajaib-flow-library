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
        loop_duration = int(handler.headers.get('X-Loop-Duration', '0'))
        if loop_duration not in (0, 4, 6, 8, 12):
            raise ValueError('Invalid loop duration')
        aspect = handler.headers.get('X-Aspect-Ratio', '9x16')
        if aspect not in ('9x16', '2x1', 'custom'):
            raise ValueError('Invalid aspect ratio')
        width, height = (2160, 1080) if aspect == '2x1' else (1080, 1920)
        if aspect == 'custom':
            width = int(handler.headers.get('X-Export-Width', 1920))
            height = int(handler.headers.get('X-Export-Height', 1080))
            if any(n < 64 or n > 3840 or n % 2 for n in (width, height)):
                raise ValueError('Dimensions must be even numbers from 64 to 3840')
        if not 0 < length <= 100 * 1024 * 1024 or fps not in (30, 60):
            handler.send_error(400, 'Invalid recording size or frame rate')
            return True
        with tempfile.TemporaryDirectory(prefix='flow-portrait-') as directory:
            source = Path(directory) / 'capture.webm'
            source.write_bytes(handler.rfile.read(length))
            output = Path(directory) / 'portrait.mp4'
            filters = f'scale={width}:{height}:flags=lanczos,setsar=1,fps={fps}'
            command = [imageio_ffmpeg.get_ffmpeg_exe(), '-hide_banner', '-loglevel', 'error', '-y', '-i', str(source)]
            if loop_duration:
                # Join at source time one second: middle, then tail blended into head.
                graph = (
                    f'[0:v]{filters},tpad=stop_mode=clone:stop_duration=1,split=3[a][b][c];'
                    f'[a]trim=start=1:end={loop_duration},setpts=PTS-STARTPTS[mid];'
                    f'[b]trim=start={loop_duration}:end={loop_duration+1},setpts=PTS-STARTPTS[tail];'
                    '[c]trim=start=0:end=1,setpts=PTS-STARTPTS[head];'
                    "[tail][head]blend=all_expr='A*(1-T)+B*T':shortest=1[join];"
                    '[mid][join]concat=n=2:v=1:a=0[out]'
                )
                command += ['-filter_complex', graph, '-map', '[out]', '-frames:v', str(loop_duration * fps)]
            else:
                command += ['-t', '15', '-vf', filters]
            command += ['-an', '-c:v', 'libx264', '-preset', 'medium', '-crf', '16',
                        '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(output)]
            result = subprocess.run(command, capture_output=True, timeout=180)
            if result.returncode:
                raise ValueError('Invalid video recording')
            data = output.read_bytes()
        handler.send_response(200)
        handler.send_header('Content-Type', 'video/mp4')
        handler.send_header('Content-Length', str(len(data)))
        handler.send_header('Content-Disposition', f'attachment; filename="flow-{aspect}.mp4"')
        handler.end_headers()
        handler.wfile.write(data)
    except (ValueError, subprocess.TimeoutExpired, OSError):
        handler.send_error(400, 'Could not convert the video recording')
    return True
