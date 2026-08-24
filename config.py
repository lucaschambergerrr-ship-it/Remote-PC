import socket

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

HOST = "0.0.0.0"
PORT = 5000
LOCAL_IP = get_local_ip()

PAIRING_CODE = "lucas1029"

# Sensibilidad y rendimiento del stream
MOUSE_SENSITIVITY = 3.5
TARGET_FPS = 30
JPEG_QUALITY = 55