import cv2
import socket
import numpy as np
import threading
import time
import sys


# IP address of the Jetson Nano connecting to
REMOTE_IP = "192.168.1.102" #this sometimes seem to change; make a different subnet; switch to static IP
                            
PORT = 5001 #same on both Jetsons


CAMERA_SRC = 0 # TODO: check if this is always 0 regardless of usb port; seems very likely since it's about the number of cameras connected

# compression Quality 
JPEG_QUALITY = 50

#global flag for stopping threads
running = True

# sender thread 
def sender():
    global running
    sender_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # allow reusing the address
    sender_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    print(f"sender: Opening camera {CAMERA_SRC}...")
    cap = cv2.VideoCapture(CAMERA_SRC)
    if not cap.isOpened():
        print(f"Sender: Error opening video source {CAMERA_SRC}")
        running = False
        sender_socket.close()
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    print(f"Sender: camera opened. streaming to {REMOTE_IP}:{PORT}")

    while running and cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("Sender: Failed to grab frame")
            time.sleep(0.1) # avoid busy-looping if camera fails
            continue

        # encode frame 
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY]
        result, encoded_frame = cv2.imencode('.jpg', frame, encode_param)

        if not result:
            print("Sender: JPEG encoding failed")
            continue

        # send the encoded frame
        try:
            
            # send directly for now instead of chunking
            # check if the frame is too large for UDP
            sender_socket.sendto(encoded_frame.tobytes(), (REMOTE_IP, PORT))
        except socket.error as e:
            print(f"Sender: Socket error: {e}")
            time.sleep(0.5)
        except Exception as e:
             print(f"Sender: Error sending data: {e}")

        # test delay to prevent overwhelming the network/CPU
        # time.sleep(0.01) # ~100 FPS theoretical max test this

    print("Sender: Stopping...")
    cap.release()
    sender_socket.close()
    print("Sender: Thread finished")


# receiver thread 
def receiver():
    global running
    receiver_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # allow reusing the address
    receiver_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # binnd to local host and port to receive data
    # bind to '0.0.0.0' to accept connections on all available interfaces
    try:
        receiver_socket.bind(('0.0.0.0', PORT))
        print(f"Receiver: Listening on port {PORT}")
    except socket.error as e:
        print(f"Receiver: Failed to bind socket on port {PORT}: {e}")
        print("Receiver: Is another application using this port?")
        running = False
        receiver_socket.close()
        return

    # timeout so the socket doesn't block indefinitely
    receiver_socket.settimeout(1.0) # 1 second timeout

    window_name = f"Received Stream from {REMOTE_IP}"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL) # resizable window

    while running:
        try:
            # receive data
            data, addr = receiver_socket.recvfrom(65536) 

            if not data:
                continue # no data received within timeout

            # decode JPEG data
            np_data = np.frombuffer(data, dtype=np.uint8)
            frame = cv2.imdecode(np_data, cv2.IMREAD_COLOR)

            if frame is None:
                # print(f"Receiver: Failed to decode frame from {addr}")
                continue

            # display received frame
            cv2.imshow(window_name, frame)

            # Check for 'q' key press to exit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("Receiver: 'q' pressed, initiating shutdown")
                running = False # signal other thread to stop
                break

        except socket.timeout:
            # print("Receiver: Socket timeout") # Normal if no data is being sent
            # check if we should still be running
             if not running:
                 break
             # If 'q' was pressed in imshow but no data was received, check again
             if cv2.waitKey(1) & 0xFF == ord('q'):
                 print("Receiver: 'q' pressed during timeout, initiating shutdown")
                 running = False
                 break
             continue # continue listening
        except socket.error as e:
            print(f"Receiver: Socket error: {e}")
            time.sleep(0.5) # wait a bit before trying again
        except Exception as e:
            print(f"Receiver: Error processing received data: {e}")


    print("Receiver: Stopping...")
    receiver_socket.close()
    cv2.destroyAllWindows()
    print("Receiver: Thread finished")



if __name__ == '__main__':

    print("Starting Simple Streamer...")
    print(f"Local sending thread will stream TO: {REMOTE_IP}:{PORT}")
    print(f"Local receiving thread will listen ON port: {PORT}")

    # create and start threads
    sender_thread = threading.Thread(target=sender, daemon=True)
    receiver_thread = threading.Thread(target=receiver, daemon=True)

    sender_thread.start()
    receiver_thread.start()

    # keep the main thread alive until threads finish (or handle termination)
    # receiver thread will handle the 'q' key press and set 'running' to False
    try:
        while running:
            # check if threads are still alive; exit if both have stopped unexpectedly
            if not sender_thread.is_alive() and not receiver_thread.is_alive():
                 print("Main: Both threads have stopped")
                 running = False # make sure loop terminates
            time.sleep(0.5) # main thread doesn't need to do much work yet
    except KeyboardInterrupt:
        print("Main: CTRL C detected. Stopping threads...")
        running = False

    print("Main: Waiting for threads to finish...")
    sender_thread.join(timeout=2.0) # wait max 2 seconds for sender
    receiver_thread.join(timeout=2.0) # wait max 2 seconds for receiver

    if sender_thread.is_alive():
        print("Main: Sender thread did not terminate gracefully")
    if receiver_thread.is_alive():
        print("Main: Receiver thread did not terminate gracefully")


    cv2.destroyAllWindows() # make sure windows are closed
    print("Main: Application finished.")