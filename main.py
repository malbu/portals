import threading, time, concurrent.futures, config, cv2
from camera_manager import CameraManager
from network_manager import NetworkManager
from stream_processor import StreamProcessor
from display_manager import DisplayManager
from app_state import AppState
from codec_utils import encode_bgr_to_jpeg


class VideoStreamerApp:
    def __init__(self):
        peers = config.get_other_peer_infos(config.MY_ID, config.PEER_NANO_INFO)
        self.cam  = CameraManager()
        self.net  = NetworkManager(config.UDP_PORT, peers)
        self.proc = StreamProcessor([p['ip'] for p in peers])
        self.disp = DisplayManager(window_title=config.PEER_NANO_INFO[config.MY_ID]['name'])
        self.state= AppState(config.MY_ID, config.PEER_NANO_INFO, config.KEY_MAPPINGS)
        self.running = True
        self.pool = concurrent.futures.ThreadPoolExecutor(max_workers=2)


    # background threads
    def _capture_loop(self):
        while self.running:
            frame = self.cam.capture()
            if frame is not None:
                self.pool.submit(self._encode_and_send, frame)
            time.sleep(0.001)


    def _encode_and_send(self, frame):
        jpeg = encode_bgr_to_jpeg(frame, config.JPEG_QUALITY)
        self.net.send_jpeg(jpeg)


    def _receiver_loop(self):
        while self.running:
            data, ip = self.net.recv_datagram()
            if data:
                self.proc.process_datagram(data, ip)


    
    def run(self):
        self.t_capture = threading.Thread(target=self._capture_loop)
        self.t_recv    = threading.Thread(target=self._receiver_loop)

        self.t_capture.start()
        self.t_recv.start()

        while self.running:
            k = self.disp.key()
            if k != 255 and k != -1:
                if self.state.handle_key(k) == 'QUIT':
                    self.running = False
                    break
            if self.state.view_mode == 'SINGLE':
                ip = self.state.current_single_ip()
                name = self.state.current_single_name()
                frame = self.proc.latest(ip) if ip else None
                self.disp.show_single(frame, name)
            else:
                t = self.state.dual_targets()
                if len(t) == 2:
                    f1 = self.proc.latest(t[0]['ip']); f2 = self.proc.latest(t[1]['ip'])
                    self.disp.show_dual(f1, t[0]['name'], f2, t[1]['name'])
                elif len(t) == 1:
                    f1 = self.proc.latest(t[0]['ip']); self.disp.show_single(f1, t[0]['name'])
            time.sleep(0.01)
        self.cleanup()


    def cleanup(self):
        # signal worker threads to stop
        self.running = False

        # wait for capture and receiver threads to finish 
        if hasattr(self, 't_capture'):
            self.t_capture.join(timeout=2.0)
        if hasattr(self, 't_recv'):
            self.t_recv.join(timeout=2.0)

        # all encode tasks must be done before closing the sockets
        self.pool.shutdown(wait=True)

        self.cam.release()
        self.net.close()
        self.disp.close()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    VideoStreamerApp().run()
