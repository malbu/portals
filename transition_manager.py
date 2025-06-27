# TransitionManager: plays short 640x480 clips prior to view switches
import cv2, random, os
from pathlib import Path
from typing import Tuple, List, Optional


class TransitionManager:
    """Handle random clip playback between UI view switches

    clips are assumed to be 640x480
    """

    def __init__(self, clip_dir: str, chance: float, window_size: Tuple[int, int] = (640, 480)):
        self.clip_paths: List[Path] = [p for p in Path(clip_dir).glob("*.*") if p.is_file()]
        self.chance = float(max(0.0, min(1.0, chance)))
        self.window_size = window_size  # (width, height)

        self.cap: Optional[cv2.VideoCapture] = None

    
    def arm_transition(self) -> bool:
        """Randomly decide whether to play a clip.  Return True if armed"""
        # if none clips on disk or chance roll fails, skip
        if not self.clip_paths or random.random() > self.chance:
            return False

        clip_path = str(random.choice(self.clip_paths))
        # try GStreamer first for hardware-accelerated decode on Jetson
        cap = cv2.VideoCapture(clip_path, cv2.CAP_GSTREAMER)
        if not cap.isOpened():
            # Fallback to any available backend
            cap = cv2.VideoCapture(clip_path)
        if not cap.isOpened():
            # failed to open with any backend, skip transition
            return False

        # warm-up read to prime decoder; ignore content
        cap.read()
        self.cap = cap
        return True

    def next_frame(self):
        """Return (frame, done)  *done* is True when clip finished or not armed"""
        if self.cap is None:
            return None, True

        ok, frame = self.cap.read()
        if not ok or frame is None:
            self.cap.release()
            self.cap = None
            return None, True

        h_target = self.window_size[1]
        w_target = self.window_size[0]

        h, w = frame.shape[:2]
        if (w, h) != (w_target, h_target):
            frame = cv2.resize(frame, (w_target, h_target))
        return frame, False

    def abort(self):
        """immediately stop any playing clip"""
        if self.cap is not None:
            self.cap.release()
            self.cap = None 