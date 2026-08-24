import base64
import time
import cv2
import mss
import numpy as np
import pyautogui
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
from pynput.keyboard import Controller as KeyboardController, Key
from pynput.mouse import Controller as MouseController, Button
import config

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0

app = Flask(__name__)
app.config['SECRET_KEY'] = 'remote_pc_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

mouse = MouseController()
keyboard = KeyboardController()

KEY_MAP = {
    'Enter': Key.enter,
    'Backspace': Key.backspace,
    'Space': Key.space,
    'Escape': Key.esc,
    'Tab': Key.tab,
    'ArrowUp': Key.up,
    'ArrowDown': Key.down,
    'ArrowLeft': Key.left,
    'ArrowRight': Key.right
}

streaming_active = False

def draw_cursor(img, x, y):
    pts = np.array([[x, y], [x, y + 18], [x + 5, y + 14], [x + 10, y + 21], 
                    [x + 13, y + 19], [x + 8, y + 13], [x + 14, y + 13]], np.int32)
    pts = pts.reshape((-1, 1, 2))
    cv2.polylines(img, [pts], True, (0, 0, 0), 2)
    cv2.fillPoly(img, [pts], (255, 255, 255))

def capture_and_stream():
    global streaming_active
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        frame_delay = 1.0 / config.TARGET_FPS

        while streaming_active:
            start_time = time.time()
            
            raw_img = sct.grab(monitor)
            frame = np.array(raw_img)

            orig_h, orig_w = frame.shape[:2]
            target_w = 1280
            target_h = int(orig_h * (target_w / orig_w))
            frame_resized = cv2.resize(frame, (target_w, target_h), interpolation=cv2.INTER_LINEAR)

            mx, my = mouse.position
            cur_x = int(mx * (target_w / monitor['width']))
            cur_y = int(my * (target_h / monitor['height']))
            draw_cursor(frame_resized, cur_x, cur_y)

            encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), config.JPEG_QUALITY]
            _, buffer = cv2.imencode('.jpg', frame_resized, encode_params)
            jpg_str = base64.b64encode(buffer).decode('utf-8')

            socketio.emit('screen_frame', {'image': jpg_str})

            elapsed = time.time() - start_time
            sleep_time = frame_delay - elapsed
            if sleep_time > 0:
                socketio.sleep(sleep_time)
            else:
                socketio.sleep(0.001)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status', methods=['GET'])
def check_status():
    """Ruta para comprobar si el servidor está activo y respondiendo."""
    return jsonify({'online': True, 'pc_name': 'PC Principal'})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json or {}
    code_input = data.get('code', '').strip()
    if code_input.upper() == config.PAIRING_CODE.upper():
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Código incorrecto'}), 401

@socketio.on('connect')
def handle_connect():
    global streaming_active
    if not streaming_active:
        streaming_active = True
        socketio.start_background_task(target=capture_and_stream)

@socketio.on('mouse_move')
def handle_mouse_move(data):
    dx = data.get('dx', 0) * config.MOUSE_SENSITIVITY
    dy = data.get('dy', 0) * config.MOUSE_SENSITIVITY
    mouse.move(dx, dy)

@socketio.on('mouse_click')
def handle_mouse_click(data):
    action = data.get('action')
    if action == 'left':
        mouse.click(Button.left, 1)
    elif action == 'right':
        mouse.click(Button.right, 1)
    elif action == 'double':
        mouse.click(Button.left, 2)

@socketio.on('mouse_scroll')
def handle_mouse_scroll(data):
    direction = data.get('direction')
    amount = 4 if direction == 'up' else -4
    mouse.scroll(0, amount)

@socketio.on('key_press')
def handle_key_press(data):
    key_name = data.get('key')
    if key_name in KEY_MAP:
        keyboard.press(KEY_MAP[key_name])
        keyboard.release(KEY_MAP[key_name])

if __name__ == '__main__':
    print("=" * 50)
    print("           REMOTE PC SERVER STARTED")
    print("=" * 50)
    print(f"  CELULAR: http://{config.LOCAL_IP}:{config.PORT}")
    print(f"  CÓDIGO:  {config.PAIRING_CODE}")
    print("=" * 50)
    socketio.run(app, host=config.HOST, port=config.PORT, log_output=False)
    from wakeonlan import send_magic_packet

# Coloca aquí la dirección MAC de la tarjeta de red de tu PC
TARGET_MAC_ADDRESS = "F4-B5-20-3B-A6-2D" 

@app.route('/api/wake', methods=['POST'])
def wake_pc():
    try:
        send_magic_packet(TARGET_MAC_ADDRESS)
        return jsonify({'success': True, 'message': 'Señal de encendido enviada'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
