import cv2, time, config
cap = cv2.VideoCapture(config.CAMERA_SRC, cv2.CAP_V4L2)
cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
for i in range(10):
    ok, frame = cap.read()
    print(f'{i}: ok={ok}, shape={None if frame is None else frame.shape}')
    time.sleep(0.1)
cap.release()