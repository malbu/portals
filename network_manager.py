import socket, struct, itertools, config


_HDR = struct.Struct('!HHH')
_MAX_PAYLOAD = config.MAX_DATAGRAM - _HDR.size


class NetworkManager:
    def __init__(self, local_port, peer_infos):
        self._send = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._recv = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._recv.bind(('0.0.0.0', local_port))
        self._recv.settimeout(0.5)
        self.targets = [(p['ip'], local_port) for p in peer_infos]
        self._fid = itertools.count(0)


    def send_jpeg(self, jpeg_bytes):
        fid = next(self._fid) & 0xFFFF
        total = (len(jpeg_bytes) + _MAX_PAYLOAD - 1) // _MAX_PAYLOAD
        for cid in range(total):
            start = cid * _MAX_PAYLOAD
            end   = start + _MAX_PAYLOAD
            header = _HDR.pack(fid, cid, total)
            chunk  = header + jpeg_bytes[start:end]
            for addr in self.targets:
                try:
                    self._send.sendto(chunk, addr)
                except Exception:
                    pass


    def recv_datagram(self):
        try:
            data, (ip, _p) = self._recv.recvfrom(config.MAX_DATAGRAM)
            return data, ip
        except socket.timeout:
            return None, None


    def close(self):
        self._send.close()
        self._recv.close()
