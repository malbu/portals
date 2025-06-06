import cv2, time, config


class CameraManager:
    def __init__(self):
        # use the V4L2 backend explicitly
        self.cap = cv2.VideoCapture(config.CAMERA_SRC, cv2.CAP_V4L2)
        if not self.cap.isOpened():
            raise IOError('Cannot open camera')
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH,  config.FRAME_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)


        w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        if (w, h) != (config.FRAME_WIDTH, config.FRAME_HEIGHT):
            print(f"[WARN] Camera resolution is {w}x{h} instead of "
                  f"{config.FRAME_WIDTH}x{config.FRAME_HEIGHT}. Frames larger than"
                  " expected may be dropped by the stream processor.")

        self.frame_time   = 1.0 / config.FPS_LIMIT if config.FPS_LIMIT else 0
        self.last_capture = 0.0

        print('[INFO] capture thread running')


    def capture(self):
        now = time.time()
        if now - self.last_capture < self.frame_time:
            return None
        ret, frame = self.cap.read()
        print('CAP ret=', ret, '; shape=',
              None if frame is None else frame.shape)
        if not ret:
            return None
        self.last_capture = now
        return frame


    def release(self):
        if self.cap.isOpened():
            self.cap.release()
