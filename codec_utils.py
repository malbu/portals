from turbojpeg import TurboJPEG, TJPF_BGR, TJFLAG_FASTDCT
import threading


# now each thread gets its own TurboJPEG instance.  Turns out the C implementation is not
# guaranteed to be re-entrant; single instance across encode
# and decode threads can lead to crashes

_thread_local = threading.local()


def _get_jpeg():

    jpeg = getattr(_thread_local, 'jpeg', None)
    if jpeg is None:
        jpeg = TurboJPEG()
        _thread_local.jpeg = jpeg
    return jpeg


def encode_bgr_to_jpeg(frame_bgr, quality):

    jpeg = _get_jpeg()
    return jpeg.encode(frame_bgr, quality=quality, pixel_format=TJPF_BGR, flags=TJFLAG_FASTDCT)


def decode_jpeg_to_bgr(jpeg_bytes):

    jpeg = _get_jpeg()
    try:
        return jpeg.decode(jpeg_bytes, pixel_format=TJPF_BGR)
    except Exception:
        # corrupted payload or internal decoder error
        return None
