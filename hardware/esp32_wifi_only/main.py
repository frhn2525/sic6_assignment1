from machine import Pin, I2C, UART, Timer
import network
import time
from umqtt.simple import MQTTClient
import ujson
import math

# Configuration
WIFI_SSID = "Realme GT Neo 3"
WIFI_PASSWORD = "qwertyuiop1"
MQTT_SERVER = "0.tcp.ap.ngrok.io"
MQTT_PORT = 15484
MQTT_CLIENT_ID = "esp32_accident_detector"
MQTT_USERNAME = "UNI022"
MQTT_PASSWORD = "022"
MQTT_TOPIC_MPU = "sensor/mpu6050"
MQTT_TOPIC_GPS = "sensor/gps"
MQTT_TOPIC_STATUS = "system/status"
MQTT_TOPIC_ACCIDENT = "alert/accident"

# Pin definitions
I2C_SCL_PIN = 22  # GPIO22
I2C_SDA_PIN = 21  # GPIO21
GPS_TX_PIN = 17  # Connect to RX of ESP32
GPS_RX_PIN = 16  # Connect to TX of ESP32

# MPU6050 constants
MPU_ADDR = 0x68
PWR_MGMT_1 = 0x6B
ACCEL_XOUT_H = 0x3B
GYRO_XOUT_H = 0x43

# System states
STATE_INIT = 0
STATE_PARK = 1
STATE_DRIVE = 2
STATE_ACCIDENT = 3
current_state = STATE_INIT

# Accident detection configuration
ACCIDENT_ACCEL_THRESHOLD = 2.5  # g-force threshold
ACCIDENT_GYRO_THRESHOLD = 250.0  # degrees/s threshold
ACCIDENT_DETECTION_WINDOW = 5    # Number of samples to consider
accident_buffer = []             # Buffer to store recent acceleration data
accident_cooldown = 0            # Cooldown timer after accident detection
ACCIDENT_COOLDOWN_PERIOD = 30    # Seconds to wait before allowing new accident detection

# Initialize all variables
i2c = None
gps_uart = None
mqtt_client = None
data_timer = None
gps_timer = None
mqtt_check_timer = None

# GPS data
gps_lat = 0.0
gps_lon = 0.0
gps_valid = False
last_movement_time = 0

# Function to safely initialize hardware
def initialize_hardware():
    global i2c, gps_uart
    try:
        i2c = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=400000)
        gps_uart = UART(2, baudrate=9600, tx=Pin(GPS_TX_PIN), rx=Pin(GPS_RX_PIN))
        return True
    except Exception as e:
        print(f"Hardware initialization error: {e}")
        return False

# Function to connect to WiFi
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    print("Connecting to WiFi...")
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            if not wlan.isconnected():
                wlan.connect(WIFI_SSID, WIFI_PASSWORD)
                timeout = 20
                while not wlan.isconnected() and timeout > 0:
                    print(f"Waiting for connection... {timeout}s")
                    time.sleep(1)
                    timeout -= 1
            if wlan.isconnected():
                print('WiFi connected!')
                print('Network config:', wlan.ifconfig())
                return True
            else:
                print(f'WiFi connection failed (attempt {attempt+1}/{max_retries})')
                time.sleep(2)
        except OSError as e:
            print(f"WiFi connection error: {e}")
            print(f"Retrying ({attempt+1}/{max_retries})...")
            wlan.active(False)
            time.sleep(2)
            wlan.active(True)
            time.sleep(1)
    
    print("All WiFi connection attempts failed")
    return False

# Function to connect to MQTT
def connect_mqtt():
    global mqtt_client
    try:
        client_id = MQTT_CLIENT_ID + "_" + str(int(time.time()))
        mqtt_client = MQTTClient(client_id, MQTT_SERVER, port=MQTT_PORT, 
                                 user=MQTT_USERNAME, password=MQTT_PASSWORD, 
                                 keepalive=30)
        mqtt_client.connect()
        print("Connected to MQTT broker")
        publish_mqtt(MQTT_TOPIC_STATUS, {"state": "PARK", "message": "System initialized"})
        return True
    except Exception as e:
        print("Failed to connect to MQTT broker:", e)
        mqtt_client = None
        return False

# Publish MQTT message with retry
def publish_mqtt(topic, message):
    global mqtt_client
    if mqtt_client is None:
        try:
            if not connect_mqtt():
                print("MQTT connection failed, cannot publish")
                return False
        except Exception as e:
            print(f"Error reconnecting MQTT in publish: {e}")
            return False
    if isinstance(message, dict):
        try:
            message = ujson.dumps(message)
        except Exception as e:
            print(f"JSON serialization error: {e}")
            return False
    if not isinstance(message, (str, bytes)):
        try:
            message = str(message)
        except Exception as e:
            print(f"String conversion error: {e}")
            return False
    if isinstance(message, str):
        message = message.encode('utf-8')
    if isinstance(topic, str):
        topic = topic.encode('utf-8')
    for attempt in range(3):
        try:
            mqtt_client.publish(topic, message)
            return True
        except Exception as e:
            print(f"Failed to publish MQTT message (attempt {attempt+1}): {e}")
            try:
                mqtt_client = None
                time.sleep(1)
                if connect_mqtt():
                    print("MQTT reconnected, retrying publish...")
                else:
                    print("MQTT reconnection failed")
            except Exception as reconnect_err:
                print(f"MQTT reconnection error: {reconnect_err}")
    return False

# Check MQTT connection periodically
def check_mqtt_connection(timer):
    global mqtt_client
    try:
        if mqtt_client is None:
            connect_mqtt()
    except Exception as e:
        print(f"MQTT connection check error: {e}")
        mqtt_client = None
        try:
            connect_mqtt()
        except:
            pass

# Initialize MPU6050
def init_mpu6050():
    global i2c
    if i2c is None:
        print("I2C not initialized")
        return False
    try:
        i2c.writeto_mem(MPU_ADDR, PWR_MGMT_1, b'\x00')
        time.sleep(0.1)
        if MPU_ADDR not in i2c.scan():
            print("MPU6050 not found!")
            return False
        print("MPU6050 initialized")
        return True
    except Exception as e:
        print("Failed to initialize MPU6050:", e)
        return False

# Read acceleration data from MPU6050
def read_mpu6050():
    global i2c
    if i2c is None:
        print("I2C not initialized in read_mpu6050")
        return {"accel": {"x": 0, "y": 0, "z": 0}, "gyro": {"x": 0, "y": 0, "z": 0}}
    try:
        data = i2c.readfrom_mem(MPU_ADDR, ACCEL_XOUT_H, 14)
        def conv(high, low):
            val = (high << 8) | low
            return val - 65536 if val > 32767 else val
        accel_x = conv(data[0], data[1]) / 16384.0
        accel_y = conv(data[2], data[3]) / 16384.0
        accel_z = conv(data[4], data[5]) / 16384.0
        gyro_x = conv(data[8], data[9]) / 131.0
        gyro_y = conv(data[10], data[11]) / 131.0
        gyro_z = conv(data[12], data[13]) / 131.0
        return {"accel": {"x": accel_x, "y": accel_y, "z": accel_z},
                "gyro": {"x": gyro_x, "y": gyro_y, "z": gyro_z},
                "timestamp": time.time()}
    except Exception as e:
        print("Failed to read MPU6050:", e)
        return {"accel": {"x": 0, "y": 0, "z": 0}, "gyro": {"x": 0, "y": 0, "z": 0}, "timestamp": time.time()}

# Parse NMEA data from GPS
def parse_gps_data(line):
    global gps_lat, gps_lon, gps_valid
    try:
        if b"$GPRMC" in line:
            parts = line.decode('ascii').split(',')
            if len(parts) >= 10 and parts[2] == 'A':
                lat_deg = float(parts[3][:2])
                lat_min = float(parts[3][2:])
                lat = lat_deg + lat_min / 60.0
                if parts[4] == 'S':
                    lat = -lat
                lon_deg = float(parts[5][:3])
                lon_min = float(parts[5][3:])
                lon = lon_deg + lon_min / 60.0
                if parts[6] == 'W':
                    lon = -lon
                gps_lat = lat
                gps_lon = lon
                gps_valid = True
                return True
        return False
    except Exception as e:
        print("GPS parsing error:", e)
        return False

# Read GPS data
def read_gps(timer=None):
    global gps_uart, gps_valid
    if gps_uart is None:
        print("GPS UART not initialized in read_gps")
        return None
    try:
        if gps_uart.any():
            buffer = b""
            while gps_uart.any():
                buffer += gps_uart.readline()
                time.sleep(0.05)
            lines = buffer.split(b'\r\n')
            for line in lines:
                if line:
                    if parse_gps_data(line):
                        gps_data = {"lat": gps_lat, "lon": gps_lon, "valid": True, "timestamp": time.time()}
                        publish_mqtt(MQTT_TOPIC_GPS, gps_data)
                        return gps_data
        if not gps_valid:
            gps_data = {"lat": 0, "lon": 0, "valid": False, "timestamp": time.time()}
            publish_mqtt(MQTT_TOPIC_GPS, gps_data)
    except Exception as e:
        print("Error reading GPS:", e)
    return None

# Detect accident based on sensor data
def detect_accident(sensor_data):
    global accident_buffer, accident_cooldown
    current_time = time.time()
    if current_time < accident_cooldown:
        return False
    accident_buffer.append(sensor_data)
    if len(accident_buffer) > ACCIDENT_DETECTION_WINDOW:
        accident_buffer.pop(0)
    if len(accident_buffer) < ACCIDENT_DETECTION_WINDOW:
        return False
    for data in accident_buffer:
        accel = data["accel"]
        gyro = data["gyro"]
        accel_magnitude = math.sqrt(accel["x"]**2 + accel["y"]**2 + accel["z"]**2)
        gyro_magnitude = math.sqrt(gyro["x"]**2 + gyro["y"]**2 + gyro["z"]**2)
        if accel_magnitude > ACCIDENT_ACCEL_THRESHOLD or gyro_magnitude > ACCIDENT_GYRO_THRESHOLD:
            accident_buffer = []
            accident_cooldown = current_time + ACCIDENT_COOLDOWN_PERIOD
            return True
    return False

# Handle accident event
def handle_accident():
    global current_state, gps_lat, gps_lon, gps_valid
    print("ACCIDENT DETECTED! Sending alert...")
    alert = {"event": "accident", "timestamp": time.time(), 
             "location": {"lat": gps_lat, "lon": gps_lon, "valid": gps_valid},
             "severity": "high"}
    publish_mqtt(MQTT_TOPIC_ACCIDENT, alert)
    current_state = STATE_ACCIDENT
    publish_mqtt(MQTT_TOPIC_STATUS, {"state": "ACCIDENT", "message": "Accident detected! Alert sent."})
    print("Accident alert sent")

# Function to send sensor data
def send_sensor_data(timer=None):
    global current_state, last_movement_time, accident_cooldown
    try:
        sensor_data = read_mpu6050()
        publish_mqtt(MQTT_TOPIC_MPU, sensor_data)
        accel = sensor_data["accel"]
        gyro = sensor_data["gyro"]
        accel_magnitude = math.sqrt(accel["x"]**2 + accel["y"]**2 + accel["z"]**2)
        gyro_magnitude = math.sqrt(gyro["x"]**2 + gyro["y"]**2 + gyro["z"]**2)
        accel_change = abs(accel_magnitude - 1.0)
        current_time = time.time()

        if current_state == STATE_PARK:
            if accel_change > 0.3 or gyro_magnitude > 15.0:
                current_state = STATE_DRIVE
                publish_mqtt(MQTT_TOPIC_STATUS, {"state": "DRIVE", "message": "Movement detected, switching to DRIVE mode"})
                print("Movement detected, switching to DRIVE mode")
                last_movement_time = current_time
                accident_buffer.clear()

        elif current_state == STATE_DRIVE:
            if detect_accident(sensor_data):
                handle_accident()
            elif accel_change > 0.3 or gyro_magnitude > 15.0:
                last_movement_time = current_time
            elif current_time - last_movement_time > 20:
                current_state = STATE_PARK
                publish_mqtt(MQTT_TOPIC_STATUS, {"state": "PARK", "message": "No movement detected for 20s, switching to PARK mode"})
                print("No movement detected for 20s, switching to PARK mode")

        elif current_state == STATE_ACCIDENT:
            if accel_change > 0.3 or gyro_magnitude > 15.0:
                last_movement_time = current_time
            elif current_time - last_movement_time > 20:
                current_state = STATE_PARK
                publish_mqtt(MQTT_TOPIC_STATUS, {"state": "PARK", "message": "No movement after accident for 20s, switching to PARK mode"})
                print("No movement after accident for 20s, switching to PARK mode")

    except Exception as e:
        print(f"Error in send_sensor_data: {e}")

# Safe timer initialization
def setup_timers():
    global data_timer, gps_timer, mqtt_check_timer
    data_timer = None
    gps_timer = None
    mqtt_check_timer = None
    
    try:
        data_timer = Timer(0)
        data_timer.init(period=200, mode=Timer.PERIODIC, callback=send_sensor_data)
        print("Sensor data timer initialized (5Hz)")
        
        gps_timer = Timer(1)
        gps_timer.init(period=2000, mode=Timer.PERIODIC, callback=read_gps)
        print("GPS read timer initialized (0.5Hz)")
        
        mqtt_check_timer = Timer(2)
        mqtt_check_timer.init(period=30000, mode=Timer.PERIODIC, callback=check_mqtt_connection)
        print("MQTT check timer initialized")
        
        return True
    except Exception as e:
        print(f"Error setting up timers: {e}")
        try:
            if data_timer is not None:
                data_timer.deinit()
                data_timer = None
        except:
            pass
        try:
            if gps_timer is not None:
                gps_timer.deinit()
                gps_timer = None
        except:
            pass
        try:
            if mqtt_check_timer is not None:
                mqtt_check_timer.deinit()
                mqtt_check_timer = None
        except:
            pass
        return False

# Safe cleanup function
def safe_cleanup():
    global data_timer, gps_timer, mqtt_check_timer, mqtt_client
    print("Performing system cleanup...")
    
    try:
        if data_timer is not None:
            data_timer.deinit()
            print("Data timer deinitialized")
    except Exception as e:
        print(f"Error cleaning up data timer: {e}")
    
    try:
        if gps_timer is not None:
            gps_timer.deinit()
            print("GPS timer deinitialized")
    except Exception as e:
        print(f"Error cleaning up GPS timer: {e}")
    
    try:
        if mqtt_check_timer is not None:
            mqtt_check_timer.deinit()
            print("MQTT check timer deinitialized")
    except Exception as e:
        print(f"Error cleaning up MQTT timer: {e}")
    
    try:
        if mqtt_client is not None:
            mqtt_client.disconnect()
            print("MQTT client disconnected")
    except Exception as e:
        print(f"Error disconnecting MQTT: {e}")
    
    print("System cleanup complete")

# Main function
def main():
    global current_state, accident_buffer
    print("=== ESP32 Accident Detection System ===")
    
    accident_buffer = []
    
    if not initialize_hardware():
        print("Critical error: Hardware initialization failed!")
        return
    
    if not init_mpu6050():
        print("Failed to initialize MPU6050, retrying...")
        time.sleep(1)
        if not init_mpu6050():
            print("Critical error: MPU6050 initialization failed!")
            return
    
    if not connect_wifi():
        print("Critical error: Wi-Fi connection failed!")
        return
    
    if not connect_mqtt():
        print("Warning: MQTT connection failed, will retry later")
    
    current_state = STATE_PARK
    
    if not setup_timers():
        print("Warning: Timer setup failed, continuing with limited functionality")
    
    publish_mqtt(MQTT_TOPIC_STATUS, {"state": "PARK", "message": "System initialized in PARK mode"})
    print("System initialized and running in PARK mode")
    
    try:
        while True:
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("Program terminated by user")
    except Exception as e:
        print(f"Error in main loop: {e}")
    finally:
        safe_cleanup()

# Start the program
if __name__ == "__main__":
    main()
