import time
import base64
import cv2
import mss
import numpy as np
import pyautogui
import socketio
from pynput.keyboard import Controller as KeyboardController, Key
from pynput.mouse import Controller as MouseController, Button

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0

# ⚠️ PEGA AQUÍ TU URL EXACTA DE RENDER ⚠️
RENDER_URL = "https://TU-PROYECTO.onrender.com"

sio = socketio.Client(reconnection=True, reconnection_attempts=0, reconnection_delay=2)
mouse = MouseController()
keyboard = KeyboardController()

KEY_MAP = {
    'Enter': Key.enter, 'Backspace': Key.backspace, 'Space': Key.space,
    'Escape': Key.esc, 'Tab': Key.tab, 'ArrowUp': Key.up,
    'ArrowDown': Key.down, 'ArrowLeft': Key.left, 'ArrowRight': Key.right
}

@sio.event
def connect():
    print("✅ ¡Conectado con éxito al servidor en la nube (Render)!")
    sio.emit('register_agent')

@sio.event
def disconnect():
    print("❌ Desconectado del servidor. Intentando reconectar...")

@sio.on('execute_input')
def on_execute_input(data):
    event_type = data.get('type')
    if event_type == 'mouse_move':
        dx = data.get('dx', 0) * 1.5
        dy = data.get('dy', 0) * 1.5
        mouse.move(dx, dy)
    elif event_type == 'mouse_click':
        act = data.get('action')
        if act == 'left': mouse.click(Button.left, 1)
        elif act == 'right': mouse.click(Button.right, 1)
    elif event_type == 'key_press':
        k = data.get('key')
        if k in KEY_MAP:
            keyboard.press(KEY_MAP[k])
            keyboard.release(KEY_MAP[k])

def stream_screen():
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        while True:
            if sio.connected:
                try:
                    raw_img = sct.grab(monitor)
                    frame = np.array(raw_img)
                    frame_resized = cv2.resize(frame, (1280, 720))
                    _, buffer = cv2.imencode('.jpg', frame_resized, [int(cv2.IMWRITE_JPEG_QUALITY), 50])
                    jpg_str = base64.b64encode(buffer).decode('utf-8')
                    sio.emit('stream_frame', {'image': jpg_str})
                except Exception as e:
                    print(f"Error enviando captura: {e}")
                time.sleep(0.06)
            else:
                time.sleep(1)

if __name__ == '__main__':
    while True:
        try:
            if not sio.connected:
                print("Conectando a Render...")
                sio.connect(RENDER_URL)
                stream_screen()
        except Exception as e:
            print(f"Error de conexión: {e}. Reintentando en 3 segundos...")
            time.sleep(3)
