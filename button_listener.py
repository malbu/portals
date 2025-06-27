import threading, serial, time
from typing import Optional
from serial.tools import list_ports

class ButtonListener:
    """background serial listener that converts Arduino messages to key codes.

    
    when BUTTON2_RELEASED is received inject the key code for character '1'
    """

    def __init__(self, port: Optional[str], baud: int, callback):
        
        if port in (None, '', 'auto'):
            port = self._detect_port()
        self.port = port
        self.baud = baud
        self.callback = callback
        self._stop = False
        self.ser = None
        # if no port found abort listener
        if self.port is None:
            print("[WARN] ButtonListener: no serial port found for Arduino")
            return

        try:
            self.ser = serial.Serial(self.port, self.baud, timeout=0.1)
            time.sleep(2.0)  # give Arduino time to reset
            print(f"[INFO] ButtonListener connected to {self.port} @ {self.baud}")
        except Exception as e:
            print(f"[WARN] ButtonListener: cannot open serial port {self.port}: {e}")
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def _loop(self):
        if self.ser is None:
            return
        while not self._stop:
            try:
                if self.ser.in_waiting:
                    line = self.ser.readline().decode("utf-8", errors="ignore").strip()
                    if not line:
                        continue
                    # Debug
                    # print("[BTN]", line)
                    if line == "BUTTON2_RELEASED":
                        self.callback(ord('1'))
            except Exception as e:
                # tolerate serial errors; keep trying
                print(f"[WARN] ButtonListener: serial error {e}")
                time.sleep(0.1)
            time.sleep(0.005)

    def stop(self):
        self._stop = True
        if self.thread.is_alive():
            self.thread.join(timeout=1.0)
        if self.ser:
            try:
                self.ser.close()
            except Exception:
                pass

    def _detect_port(self):
        """return first candidate port that looks like an Arduino, else first ttyACM/ttyUSB, else None"""
        ports = list(list_ports.comports())
        if not ports:
            return None
        # prioritize ones that mention Arduino in their description
        for p in ports:
            desc = (p.description or '').lower()
            if 'arduino' in desc:
                return p.device
        return ports[0].device 