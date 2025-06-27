import time, random, cv2, numpy as np
from typing import Dict, List


_GPU_AVAILABLE = cv2.cuda.getCudaEnabledDeviceCount() > 0


class _GpuHelper:
    """wrapper for CUDA operations with fallback"""

    @staticmethod
    def upload(frame):
        if not _GPU_AVAILABLE:
            return None
        return cv2.cuda_GpuMat(frame)

    @staticmethod
    def download(gpu_mat):
        if not _GPU_AVAILABLE or gpu_mat is None:
            return None
        return gpu_mat.download()


class EffectManager:
    """applies temporary effect to frames coming from peers

    after start_glitch is called for a set of peer IPs, frames belonging to
    those peers are run through one of three effects for specified duration
    """

    def __init__(self):
        # state per peer ip
        self._state: Dict[str, Dict] = {}

        # pre-compute scan-line noise texture for CPU fallback
        self._scan_noise = np.random.randint(0, 6, (480,), dtype=np.int16)  # per row offset

    
    def start_glitch(self, peer_ips: List[str], duration_sec: float):
        now = time.time()
        for ip in peer_ips:
            self._state[ip] = {
                'active': True,
                't_end': now + duration_sec,
                'effect': random.randint(0, 2),  # 0,1,2
            }

    
    def apply(self, ip: str, frame):
        if frame is None:
            return None

        rec = self._state.get(ip)
        if not rec or time.time() > rec['t_end']:
            return frame

        effect_id = rec['effect']
        if effect_id == 0:
            return self._channel_shift(frame)
        elif effect_id == 1:
            return self._scan_line_offset(frame)
        else:
            return self._noise_overlay(frame)


    @staticmethod
    def _to_cpu(mat):
        """return a numpy array whether mat is a cv2.cuda_GpuMat or already CPU"""
        if mat is None:
            return None
        return mat.download() if hasattr(mat, 'download') else mat

    def _channel_shift(self, frame):
        # small random translation for G channel
        shift_x = random.randint(-5, 5)
        shift_y = random.randint(-5, 5)

        if _GPU_AVAILABLE:
            gpu = cv2.cuda_GpuMat()
            gpu.upload(frame)
            # split channels
            b, g, r = cv2.cuda.split(gpu)
            # affine matrix for shift
            M = np.float32([[1, 0, shift_x], [0, 1, shift_y]])
            # destination size (width, height) must match original frame
            h_src, w_src = frame.shape[:2]
            g_shift = cv2.cuda.warpAffine(g, M, (w_src, h_src))
            merged = cv2.cuda.merge([b, g_shift, r])
            return self._to_cpu(merged)

        # # CPU fallback 
        # g = np.roll(frame[:, :, 1], shift_x, axis=1)
        # g = np.roll(g, shift_y, axis=0)
        # out = frame.copy()
        # out[:, :, 1] = g
        # return out

    def _scan_line_offset(self, frame):
        h, w = frame.shape[:2]
        out = np.empty_like(frame)

        if _GPU_AVAILABLE:
            # generate offset map on CPU (int16 per row) then upload once
            offsets = (np.random.randint(-5, 6, (h,), dtype=np.int16))
            xmap = np.tile(np.arange(w, dtype=np.float32), (h, 1))
            ymap = np.tile(np.arange(h, dtype=np.float32).reshape(-1, 1), (1, w))
            for y in range(h):
                xmap[y] += offsets[y]
            gpu_frame = cv2.cuda_GpuMat()
            gpu_frame.upload(frame)
            gpu_xmap = cv2.cuda_GpuMat()
            gpu_xmap.upload(xmap)
            gpu_ymap = cv2.cuda_GpuMat()
            gpu_ymap.upload(ymap)
            warped = cv2.cuda.remap(gpu_frame, gpu_xmap, gpu_ymap, interpolation=cv2.INTER_LINEAR)
            return self._to_cpu(warped)

        # # CPU fallback
        # for y in range(h):
        #     dx = random.randint(-5, 5)
        #     out[y] = np.roll(frame[y], dx, axis=1)
        # return out

    def _noise_overlay(self, frame):
        alpha = 0.5
        h, w = frame.shape[:2]
        if _GPU_AVAILABLE:
            noise = np.random.randint(0, 256, (h, w), dtype=np.uint8)
            gpu_frame = cv2.cuda_GpuMat()
            gpu_frame.upload(frame)
            gpu_noise = cv2.cuda_GpuMat()
            gpu_noise.upload(noise)
            noise_bgr = cv2.cuda.cvtColor(gpu_noise, cv2.COLOR_GRAY2BGR)
            out_gpu = cv2.cuda.addWeighted(gpu_frame, 1.0, noise_bgr, alpha, 0.0)
            return self._to_cpu(out_gpu)

        # noise = np.random.randint(0, 256, frame.shape[:2], dtype=np.uint8)
        # noise_bgr = cv2.cvtColor(noise, cv2.COLOR_GRAY2BGR)
        # out = cv2.addWeighted(frame, 1.0, noise_bgr, alpha, 0.0)
        # return out 