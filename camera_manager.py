import cv2, time, config


class CameraManager:
    def __init__(self):
        self.cap = cv2.VideoCapture(config.CAMERA_SRC)
        if not self.cap.isOpened():
            raise IOError('Cannot open camera')
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH,  config.FRAME_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)
        self.frame_time   = 1.0 / config.FPS_LIMIT if config.FPS_LIMIT else 0
        self.last_capture = 0.0


    def capture(self):
        now = time.time()
        if now - self.last_capture < self.frame_time:
            return None
        ret, frame = self.cap.read()
        if not ret:
            return None
        self.last_capture = now
        return frame


    def release(self):
        if self.cap.isOpened():
            self.cap.release()
