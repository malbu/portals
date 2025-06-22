import cv2, numpy as np


class DisplayManager:
    def __init__(self, window_title="Stream"):
        self.title = window_title
        # create a resizable window first
        cv2.namedWindow(self.title, cv2.WINDOW_NORMAL)

        # try to switch the window to fullscreen regardless of single or dual view layout
        try:
            cv2.setWindowProperty(self.title, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        except Exception:
            
            try:
                cv2.setWindowProperty(self.title, cv2.WND_PROP_FULLSCREEN, 1)
            except Exception:
                pass


    def _placeholder(self, text, h=480, w=640):
        img = np.zeros((h, w, 3), np.uint8)
        cv2.putText(img, text, (40, h//2), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)
        return img


    def show_single(self, frame, name):
        if frame is None:
            frame = self._placeholder(f"Waiting {name}")
        cv2.imshow(self.title, frame)
        cv2.setWindowTitle(self.title, f"{self.title} – {name}")


    def show_dual(self, f1, n1, f2, n2):
        if f1 is None:
            f1 = self._placeholder(f"No {n1}")
        if f2 is None:
            f2 = self._placeholder(f"No {n2}")
        h = 480
        f1 = cv2.resize(f1, (int(f1.shape[1]*h/f1.shape[0]), h))
        f2 = cv2.resize(f2, (int(f2.shape[1]*h/f2.shape[0]), h))
        comp = np.concatenate([f1, f2], axis=1)
        cv2.imshow(self.title, comp)
        cv2.setWindowTitle(self.title, f"{self.title} - {n1} | {n2}")


    def key(self):
        return cv2.waitKey(1) & 0xFF


    def close(self):
        cv2.destroyAllWindows()


    def show_fullscreen(self, frame):
        """render a frame that matches the fullscreen window size
        if frame is None draw placeholder to keep the window active
        """
        if frame is None:
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.imshow(self.title, frame)
