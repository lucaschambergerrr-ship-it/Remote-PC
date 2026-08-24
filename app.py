import os
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
from wakeonlan import send_magic_packet

app = Flask(__name__)
app.config['SECRET_KEY'] = 'remote_pc_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

TARGET_MAC_ADDRESS = "F4-B5-20-3B-A6-2D"

# Importar librerías de control local solo si se ejecuta fuera de la nube
IS_RENDER = os.environ.get('RENDER') is not None

if not IS_RENDER:
    import pyautogui
    import mss
    import numpy as np
    import cv2
    from pynput.keyboard import Controller as KeyboardController, Key
    from pynput.mouse import Controller as MouseController, Button

    pyautogui.FAILSAFE = False
    pyautogui.PAUSE = 0
    mouse = MouseController()
    keyboard = KeyboardController()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status', methods=['GET'])
def check_status():
    return jsonify({'online': True, 'pc_name': 'PC Principal'})

@app.route('/api/wake', methods=['POST'])
def wake_pc():
    try:
        send_magic_packet(TARGET_MAC_ADDRESS)
        return jsonify({'success': True, 'message': 'Paquete mágico enviado'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
