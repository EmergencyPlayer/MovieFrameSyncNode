import bpy, shutil, subprocess, json

def probe_movie_fps(image):
    path = bpy.path.abspath(image.filepath)

    try:
        clip = bpy.data.movieclips.load(path)
        fps = getattr(clip, "fps", 0.0)
        bpy.data.movieclips.remove(clip)
        if fps:
            return float(fps)
    except Exception:
        pass

    if shutil.which("ffprobe"):
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=avg_frame_rate", "-of", "json", path],
            capture_output=True, text=True).stdout
        try:
            n, d = json.loads(out)["streams"][0]["avg_frame_rate"].split("/")
            return float(n) / float(d)
        except Exception:
            pass

    return None