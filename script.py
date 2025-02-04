import logging
from flask import Flask, render_template_string, request
import serial
import time
import threading

# Configure logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s: %(message)s')

app = Flask(__name__)

SERIAL_PORT = "COM6"
BAUD_RATE = 38400

# Create a persistent serial connection and a lock for thread safety
ser_lock = threading.Lock()
try:
    ser_conn = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)  # Adjust timeout to 0.1 seconds
    logging.info(f"Serial connection opened: {SERIAL_PORT} with baud rate {BAUD_RATE}")
except Exception as e:
    ser_conn = None
    logging.error(f"Error opening serial connection: {e}")

# HTML template with buttons and status messages
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>USB Switch Controller</title>
    <style>
        .button { padding: 10px; margin: 5px; width: 100px; font-size: 16px; }
        .green { background-color: green; color: white; }
        .gray { background-color: gray; color: white; }
        .error { color: red; font-weight: bold; }
    </style>
</head>
<body>
    <h1>USB Switch Controller</h1>
    <form method="post">
        {% for port in ['01', '02', '03', '04'] %}
            <button class="button {{ 'green' if port == selected_port else 'gray' }}" name="port" value="{{ port }}">Port {{ port }}</button>
        {% endfor %}
    </form>
    {% if error %}<p class="error">{{ error }}</p>{% endif %}
</body>
</html>
"""

current_port = None

def get_selected_port():
    """Query the USB switch for the active port using the persistent connection."""
    global ser_conn, current_port
    if ser_conn is None:
        logging.warning("Serial connection is not open.")
        return None
    try:
        with ser_lock:
            start_time = time.time()
            # Clear input buffer before writing
            ser_conn.reset_input_buffer()
            ser_conn.write(b'info\n')
            logging.debug(f"Command 'info' sent in {time.time() - start_time:.2f} seconds.")
            
            # Wait for response with a timeout
            response = []
            while True:
                if ser_conn.in_waiting > 0:
                    lines = ser_conn.readlines()
                    for line in lines:
                        logging.debug(f"Line read: {line}")
                        response.append(line)
                        if line.startswith(b'PORT:'):
                            break
                if response:
                    break
                time.sleep(0.01)
            logging.debug(f"Response received in {time.time() - start_time:.2f} seconds: {response}")
            
            for line in response:
                if line.startswith(b'PORT:'):
                    current_port = line.split(b':')[1].strip().decode()
                    logging.debug(f"Port retrieved: {current_port} in {time.time() - start_time:.2f} seconds")
                    return current_port
            logging.debug(f"Port retrieval failed in {time.time() - start_time:.2f} seconds")
        return None
    except Exception as e:
        logging.error(f"Error retrieving port: {e}")
        return None

@app.route("/", methods=["GET", "POST"])
def index():
    error_message = None
    selected_port = get_selected_port()
    logging.info(f"Selected port: {selected_port}")
    
    if request.method == "POST":
        new_port = request.form.get("port")
        logging.info(f"Requested new port: {new_port}")
        if new_port:
            try:
                with ser_lock:
                    start_time = time.time()
                    command = f"sw p{new_port}\n".encode()
                    ser_conn.write(command)
                    logging.debug(f"Command sent: {command}")
                    time.sleep(0.1)
                    logging.debug(f"Port switch command executed in {time.time() - start_time:.2f} seconds")
                # Confirm the port change
                start_time = time.time()
                confirmed_port = get_selected_port()
                if confirmed_port == new_port:
                    selected_port = new_port
                    logging.debug(f"Port switch confirmed in {time.time() - start_time:.2f} seconds")
                else:
                    error_message = f"Failed to switch to port {new_port}"
                    logging.error(error_message)
            except Exception as e:
                error_message = f"Serial error: {e}"
                logging.error(error_message)
    
    return render_template_string(HTML_TEMPLATE, selected_port=selected_port, error=error_message)

@app.route("/api/port", methods=["GET"])
def get_port():
    """API endpoint to get the current port."""
    current_port = get_selected_port()
    return {"current_port": current_port}, 200

@app.route("/api/port", methods=["POST"])
def set_port():
    """API endpoint to set a new port."""
    new_port = request.form.get("port")
    if not new_port:
        return {"error": "Port not specified"}, 400

    logging.info(f"Requested new port: {new_port}")
    try:
        with ser_lock:
            command = f"sw p{new_port}\n".encode()
            ser_conn.write(command)
            logging.debug(f"Command sent: {command}")
            time.sleep(0.1)
        # Confirm the port change
        confirmed_port = get_selected_port()
        if confirmed_port == new_port:
            logging.debug(f"Port switch confirmed: {confirmed_port}")
            return {"current_port": confirmed_port}, 200
        else:
            error_message = f"Failed to switch to port {new_port}"
            logging.error(error_message)
            return {"error": error_message}, 500
    except Exception as e:
        error_message = f"Serial error: {e}"
        logging.error(error_message)
        return {"error": error_message}, 500

if __name__ == "__main__":
    from waitress import serve
    logging.info("Starting server on 0.0.0.0:5000")
    serve(app, host='0.0.0.0', port=5000, threads=8, connection_limit=100)