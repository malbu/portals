MY_ID = 'nano_A'   #todo this has to be changed on each nano after cloning repo
PEER_NANO_INFO = {
    'nano_A': {'ip': '192.168.1.101', 'name': 'Jetson_A'}, #cloning repo vs clone microSD card could lead to issues; might need to manually rename after
    'nano_B': {'ip': '192.168.1.102', 'name': 'Jetson_B'},
    'nano_C': {'ip': '192.168.1.103', 'name': 'Jetson_C'},
}
UDP_PORT          = 5005
CAMERA_SRC        = 0
FRAME_WIDTH       = 640
FRAME_HEIGHT      = 480
JPEG_QUALITY      = 50           # switching to TurboJPEG for encode/decode for speed/ quality 1‑100
FPS_LIMIT         = 30
MAX_DATAGRAM      = 1300         # payload size per UDP packet 
FRAME_DEQUE_LEN   = 5            # per‑peer history depth

def get_key_mappings(my_id, peer_info):
    other = [pid for pid in peer_info if pid != my_id]
    m = {ord('q'): 'quit', ord('m'): 'toggle_dual_view'}
    if len(other) > 0:
        m[ord('1')] = other[0]
    if len(other) > 1:
        m[ord('2')] = other[1]
    return m

KEY_MAPPINGS = get_key_mappings(MY_ID, PEER_NANO_INFO)

def get_other_peer_infos(me, info):
    return [v for k, v in info.items() if k != me]

def get_other_peer_ips(me, info):
    return [v['ip'] for k, v in info.items() if k != me]