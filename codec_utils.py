from turbojpeg import TurboJPEG, TJPF_BGR, TJFLAG_FASTDCT


_jpeg = TurboJPEG()  


def encode_bgr_to_jpeg(frame_bgr, quality):

    return _jpeg.encode(frame_bgr, quality=quality, pixel_format=TJPF_BGR, flags=TJFLAG_FASTDCT)


def decode_jpeg_to_bgr(jpeg_bytes):
    return _jpeg.decode(jpeg_bytes, pixel_format=TJPF_BGR)
