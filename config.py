MY_ID = 'nano_A'   #todo this has to be changed on each nano after cloning repo
PEER_NANO_INFO = {
    'nano_A': {'ip': '192.168.2.135', 'name': 'Jetson_A'}, #cloning repo vs clone microSD card could lead to issues; might need to manually rename after
    'nano_B': {'ip': '192.168.2.130', 'name': 'Jetson_B'},
    'nano_C': {'ip': '192.168.2.133', 'name': 'Jetson_C'},
}

## testing on one nano, using loopback 
# PEER_NANO_INFO = {
#     'nano_A': {'ip': '127.0.0.1', 'name': 'Me'},
#     'nano_B': {'ip': '127.0.0.1', 'name': 'Loopy_B'},
#     'nano_C': {'ip': '127.0.0.1', 'name': 'Loopy_C'},
# }
UDP_PORT          = 5005
CAMERA_SRC        = 0
FRAME_WIDTH       = 640
FRAME_HEIGHT      = 480
JPEG_QUALITY      = 45           # switching to TurboJPEG for encode/decode for speed/ quality 1‑100
FPS_LIMIT         = 30
MAX_DATAGRAM      = 1300         # payload size per UDP packet 
FRAME_DEQUE_LEN   = 5            # per peer history depth


# folder for 640x480 mp4 clips
CLIP_DIR          = "/home/kineolabs/firefly2025/stream_transitions"
# chance 0.0-1.0 that a video is played during a view switch
TRANSITION_CHANCE = 0.5
# duration that a GPU glitch effect is applied to the live stream
# immediately after switching (seconds)
GLITCH_SEC        = 20.0

# serial port for external button controller
ARDUINO_PORT      = 'auto'  
ARDUINO_BAUD      = 9600

def get_key_mappings(my_id, peer_info):
    """Return key-action mapping

    Rotate view with "1" key
    1 - rotate view (single peer 1 -> single peer 2 -> dual view -> single peer 1 ->...)

    q - quit
    """


    return {
        ord('q'): 'quit',
        ord('1'): 'rotate_view',
    }

KEY_MAPPINGS = get_key_mappings(MY_ID, PEER_NANO_INFO)

def get_other_peer_infos(me, info):
    return [v for k, v in info.items() if k != me]

def get_other_peer_ips(me, info):
    return [v['ip'] for k, v in info.items() if k != me]