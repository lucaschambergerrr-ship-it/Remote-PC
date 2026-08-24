import base64
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from wakeonlan import send_magic_packet

app = Flask(__name__)
app.config['SECRET_KEY'] = 'remote_pc_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

TARGET_MAC_ADDRESS = "F4-B5-20-3B-A6-2D"
pc_connected = False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status', methods=['GET'])
def check_status():
    return jsonify({'online': pc_connected, 'pc_name': 'PC Principal'})

@app.route('/api/wake', methods=['POST'])
def wake_pc():
    try:
        send_magic_packet(TARGET_MAC_ADDRESS)
        return jsonify({'success': True, 'message': 'Paquete mágico enviado'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# Eventos de WebSockets para conectar la PC Local con el Celular
@socketio.on('register_agent')
def handle_register_agent():
    global pc_connected
    pc_connected = True
    emit('status_change', {'online': True}, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    global pc_connected
    pc_connected = False
    emit('status_change', {'online': False}, broadcast=True)

@socketio.on('stream_frame')
def handle_stream_frame(data):
    # Reenvía la pantalla de la PC hacia el celular
    emit('screen_frame', data, broadcast=True)

@socketio.on('input_event')
def handle_input_event(data):
    # Reenvía las órdenes del celular hacia la PC
    emit('execute_input', data, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
