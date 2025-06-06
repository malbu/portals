import collections, time, struct, config
from codec_utils import decode_jpeg_to_bgr


_HDR = struct.Struct('!HHH')

#  datagrams that would lead to excessive memory use or invalid indices are now rejected
_MAX_CHUNKS = 64  # With 1.3 kB chunks and 480p/50 % quality JPEG, 64 is plenty


class StreamProcessor:
    def __init__(self, peer_ips):
        self.deques = {ip: collections.deque(maxlen=config.FRAME_DEQUE_LEN) for ip in peer_ips}
        self._assem = {}


    def _expire_old(self):
        t = time.time()
        for k in list(self._assem.keys()):
            if self._assem[k]['deadline'] < t:
                del self._assem[k]


    def process_datagram(self, data, ip):
        if ip not in self.deques or len(data) < _HDR.size:
            return
        fid, cid, total = _HDR.unpack_from(data)
        payload = data[_HDR.size:]
        key = (ip, fid)
        rec = self._assem.get(key)

        # sanitycheck for header values
        if total == 0 or total > _MAX_CHUNKS or cid >= total:
            return  

        if rec is None:
            rec = {
                'chunks': [None] * total,
                'left': total,
                'deadline': time.time() + 1.0,
            }
            self._assem[key] = rec
        if cid < total and rec['chunks'][cid] is None:
            rec['chunks'][cid] = payload
            rec['left'] -= 1
        if rec['left'] == 0:
            jpeg = b"".join(rec['chunks'])
            frame = decode_jpeg_to_bgr(jpeg)
            if frame is not None:
                self.deques[ip].append(frame)
            del self._assem[key]
        self._expire_old()


    def latest(self, ip):
        dq = self.deques.get(ip)
        if not dq:
            return None
        try:
            return dq[-1]
        except IndexError:
            # deque was emptied between len() and index due to another thread
            return None
