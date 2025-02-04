# USB Switch Controller

This project provides a web interface and a simple REST API to control a USB switch using a serial connection.

## Requirements

- Python 3.x
- Flask
- pyserial
- waitress

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/reneroger/usb-switch-controller.git
    cd usb-switch-controller
    ```

2. Create a virtual environment and activate it:
    ```sh
    python -m venv .venv
    source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
    ```

3. Install the required packages:
    ```sh
    pip install -r requirements.txt
    ```

## Configuration

Update the `SERIAL_PORT` and `BAUD_RATE` variables in `script.py` to match your USB switch's configuration.

## Usage

1. Start the server:
    ```sh
    python script.py --port COM6 --baudrate 38400
    ```

2. Open your web browser and navigate to `http://localhost:5000` to access the web interface.

## REST API

### Get Current Port

- **URL:** `/api/port`
- **Method:** `GET`
- **Response:**
    ```json
    {
        "current_port": "01"
    }
    ```

### Set New Port

- **URL:** `/api/port`
- **Method:** `POST`
- **Data:**
    ```json
    {
        "port": "02"
    }
    ```
- **Response:**
    ```json
    {
        "current_port": "02"
    }
    ```

## Example Usage with `curl`

### Get Current Port

```sh
curl -X GET http://localhost:5000/api/port
```

### Set New Port

```sh
curl -X POST http://localhost:5000/api/port -d "port=02"
```

## License

This project is licensed under the MIT License.

## Acknowledgements

This script was created with the help of GitHub Copilot.
