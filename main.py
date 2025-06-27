import threading, time, concurrent.futures, random, config, cv2, queue
from camera_manager import CameraManager
from network_manager import NetworkManager
from stream_processor import StreamProcessor
from display_manager import DisplayManager
from app_state import AppState
from codec_utils import encode_bgr_to_jpeg
from transition_manager import TransitionManager
from effect_manager import EffectManager
from button_listener import ButtonListener


class VideoStreamerApp:
    def __init__(self):
        peers = config.get_other_peer_infos(config.MY_ID, config.PEER_NANO_INFO)
        self.cam  = CameraManager()
        self.net  = NetworkManager(config.UDP_PORT, peers)
        self.proc = StreamProcessor([p['ip'] for p in peers])
        self.disp = DisplayManager(window_title=config.PEER_NANO_INFO[config.MY_ID]['name'])
        self.state= AppState(config.MY_ID, config.PEER_NANO_INFO, config.KEY_MAPPINGS)
        self.trans = TransitionManager(config.CLIP_DIR, config.TRANSITION_CHANCE,
                                       window_size=(config.FRAME_WIDTH, config.FRAME_HEIGHT))
        self.effects = EffectManager()
        self.running = True
        self.pool = concurrent.futures.ThreadPoolExecutor(max_workers=2)
        # last captured local frame for LOCAL view
        self._latest_local_frame = None

        # queue for keys coming from external button controller
        self._key_queue: "queue.Queue[int]" = queue.Queue()

        # start button listener if serial port configured
        if getattr(config, 'ARDUINO_PORT', None):
            self.btn_listener = ButtonListener(config.ARDUINO_PORT, getattr(config, 'ARDUINO_BAUD', 9600),
                                               self._enqueue_key)
        else:
            self.btn_listener = None


    # background threads
    def _capture_loop(self):
        while self.running:
            frame = self.cam.capture()
            if frame is not None:
                self._latest_local_frame = frame          # keep for LOCAL view
                self.pool.submit(self._encode_and_send, frame)
            time.sleep(0.001)


    def _encode_and_send(self, frame):
        # print('ENC task start')  
        try:
            jpeg = encode_bgr_to_jpeg(frame, config.JPEG_QUALITY)
            # print('SEND -> jpeg', len(jpeg), 'bytes')  
            self.net.send_jpeg(jpeg)
        except Exception as e:
            print('ENC task EXCEPTION', e)


    def _receiver_loop(self):
        while self.running:
            data, ip = self.net.recv_datagram()
            if data:
                # print('RECV <-', len(data), 'bytes from', ip)  
                self.proc.process_datagram(data, ip)


    
    def run(self):
        self.t_capture = threading.Thread(target=self._capture_loop)
        self.t_recv    = threading.Thread(target=self._receiver_loop)

        self.t_capture.start()
        self.t_recv.start()

        while self.running:
            # fetch key from external queue if any; otherwise poll cv2 window
            try:
                k = self._key_queue.get_nowait()
            except queue.Empty:
                k = self.disp.key()
            if k != 255 and k != -1:
                action = self.state.handle_key(k)
                if action and action.get('action') == 'QUIT':
                    self.running = False
                    break
                elif action and action.get('action') == 'SKIP':
                    # user skipped transition clip; stop it and activate pending view
                    self.trans.abort()
                    self.state.activate_pending_view()
                    ips = self.state.current_view_peer_ips()
                    self.effects.start_glitch(ips, config.GLITCH_SEC)
                elif action and action.get('action') == 'SWITCH':
                    next_mode   = action['next_mode']
                    next_target = action['next_target']

                    played = self.trans.arm_transition()
                    if played:
                        # clip will play; queue view for later
                        self.state.queue_pending_view(next_mode, next_target)
                    else:
                        # switch immediately and start glitch
                        self.state.activate_view(next_mode, next_target)
                        ips = self.state.current_view_peer_ips()
                        self.effects.start_glitch(ips, config.GLITCH_SEC)

            # render according to current mode
            if self.state.view_mode == 'TRANSITION':
                frame, done = self.trans.next_frame()
                self.disp.show_fullscreen(frame)
                if done:
                    # apply pending view and start glitch
                    self.state.activate_pending_view()
                    ips = self.state.current_view_peer_ips()
                    self.effects.start_glitch(ips, config.GLITCH_SEC)

            elif self.state.view_mode == 'SINGLE':
                if self.state.single_is_local():
                    # show local camera with possible glitch overlay
                    frame = self.effects.apply(AppState.LOCAL,
                                               self._latest_local_frame)
                    name  = config.PEER_NANO_INFO[config.MY_ID]['name']
                    self.disp.show_single(frame, name)
                else:
                    ip   = self.state.current_single_ip()
                    name = self.state.current_single_name()
                    frame = self.proc.latest(ip)
                    frame = self.effects.apply(ip, frame)
                    self.disp.show_single(frame, name)

            else:  # DUAL
                t = self.state.dual_targets()
                if len(t) == 2:
                    f1 = self.proc.latest(t[0]['ip']); f2 = self.proc.latest(t[1]['ip'])
                    f1 = self.effects.apply(t[0]['ip'], f1)
                    f2 = self.effects.apply(t[1]['ip'], f2)
                    self.disp.show_dual(f1, t[0]['name'], f2, t[1]['name'])
                elif len(t) == 1:
                    f1 = self.proc.latest(t[0]['ip']); f1 = self.effects.apply(t[0]['ip'], f1)
                    self.disp.show_single(f1, t[0]['name'])
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
        if self.btn_listener:
            self.btn_listener.stop()
        cv2.destroyAllWindows()


    def _enqueue_key(self, key_code: int):
        """callback invoked by ButtonListener thread"""
        try:
            self._key_queue.put_nowait(key_code)
        except queue.Full:
            pass


if __name__ == '__main__':
    VideoStreamerApp().run()
