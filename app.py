from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
from wakeonlan import send_magic_packet

app = Flask(__name__)
app.config['SECRET_KEY'] = 'remote_pc_secret_key'
# cors_allowed_origins="*" permite la conexión directa sin bloqueos
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')

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

# Control de estado mediante WebSockets
@socketio.on('connect')
def handle_connect():
    # Enviar el estado actual apenas el navegador/celular se conecta
    emit('status_change', {'online': pc_connected})

@socketio.on('register_agent')
def handle_register_agent():
    global pc_connected
    pc_connected = True
    print("--> Agente PC conectado y registrado")
    # Notificar a todos los celulares conectados que la PC está ONLINE
    emit('status_change', {'online': True}, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    # Nota: Si el agente se desconecta, marcamos offline
    pass

@socketio.on('agent_disconnect')
def handle_agent_disconnect():
    global pc_connected
    pc_connected = False
    print("--> Agente PC desconectado")
    emit('status_change', {'online': False}, broadcast=True)

@socketio.on('stream_frame')
def handle_stream_frame(data):
    # Reenvía la captura de pantalla al celular
    emit('screen_frame', data, broadcast=True)

@socketio.on('input_event')
def handle_input_event(data):
    # Reenvía los eventos de mouse/teclado hacia la PC
    emit('execute_input', data, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
