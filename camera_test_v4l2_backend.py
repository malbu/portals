import cv2, time
cap = cv2.VideoCapture(0, cv2.CAP_V4L2)    
print('Backend:', cap.getBackendName())
for i in range(5):
    ok, _ = cap.read()
    print(i, ok)
    time.sleep(0.2)
cap.release()