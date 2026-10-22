import math

def movie_frame(scene_frame, start, speed, src_fps, scene_fps):
    """1-based movie frame for a given scene frame."""
    t = max(scene_frame - start, 0) / scene_fps
    return math.floor(t * speed * src_fps) + 1

def frame_offset(scene_frame, start, speed, src_fps, scene_fps):
    return movie_frame(scene_frame, start, speed, src_fps, scene_fps) - scene_frame