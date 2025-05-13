import network
import socket
import machine
import time
from machine import Pin, PWM, ADC

# ======================
# Motor Configuration
# ======================
class MotorGroup:
    def __init__(self, front_fwd, front_bwd, rear_fwd, rear_bwd, pwm_pin):
        self.front_fwd = Pin(front_fwd, Pin.OUT)
        self.front_bwd = Pin(front_bwd, Pin.OUT)
        self.rear_fwd = Pin(rear_fwd, Pin.OUT)
        self.rear_bwd = Pin(rear_bwd, Pin.OUT)
        self.pwm = PWM(Pin(pwm_pin), freq=1000, duty=0)

    def drive(self, direction, speed):
        speed = min(1023, max(0, int(speed * 1023)))
        self.pwm.duty(speed)
        
        if direction == 'fwd':
            self.front_fwd.value(1)
            self.front_bwd.value(0)
            self.rear_fwd.value(1)
            self.rear_bwd.value(0)
        elif direction == 'bwd':
            self.front_fwd.value(0)
            self.front_bwd.value(1)
            self.rear_fwd.value(0)
            self.rear_bwd.value(1)
        else:  # Stop
            self.front_fwd.value(0)
            self.front_bwd.value(0)
            self.rear_fwd.value(0)
            self.rear_bwd.value(0)
            self.pwm.duty(0)

# Initialize motor groups
left_side = MotorGroup(
    front_fwd=27,   # GPIO27 - Front Left Forward
    front_bwd=26,   # GPIO26 - Front Left Backward
    rear_fwd=14,    # GPIO14 - Rear Left Forward
    rear_bwd=12,    # GPIO12 - Rear Left Backward
    pwm_pin=32      # GPIO32 - Left PWM
)

right_side = MotorGroup(
    front_fwd=25,   # GPIO25 - Front Right Forward
    front_bwd=33,   # GPIO33 - Front Right Backward
    rear_fwd=13,    # GPIO13 - Rear Right Forward
    rear_bwd=15,    # GPIO15 - Rear Right Backward
    pwm_pin=14      # GPIO14 - Right PWM
)

# ======================
# Power Management
# ======================
vin = ADC(Pin(35))  # GPIO35 for voltage monitoring
vin.atten(ADC.ATTN_11DB)

def check_voltage():
    raw = vin.read()
    voltage = (raw / 4095) * 3.3 * 2  # Voltage divider ratio
    if voltage < 7.0:  # 7V threshold for 2S LiPo
        stop()
        print(f"Low voltage: {voltage:.2f}V! Stopping...")
        return False
    return True

# ======================
# Movement Functions
# ======================
def stop():
    left_side.drive('stop', 0)
    right_side.drive('stop', 0)

def move(direction, speed=0.5):
    if not check_voltage():
        return
    
    if direction == 'forward':
        left_side.drive('fwd', speed)
        right_side.drive('fwd', speed)
    elif direction == 'backward':
        left_side.drive('bwd', speed)
        right_side.drive('bwd', speed)
    elif direction == 'left':
        left_side.drive('bwd', speed)
        right_side.drive('fwd', speed)
    elif direction == 'right':
        left_side.drive('fwd', speed)
        right_side.drive('bwd', speed)

# ======================
# WiFi & Web Server
# ======================
def connect_wifi(ssid, password):
    sta = network.WLAN(network.STA_IF)
    sta.active(True)
    
    if not sta.isconnected():
        print("Connecting to WiFi...")
        sta.connect(ssid, password)
        
        for _ in range(20):
            if sta.isconnected():
                break
            time.sleep(1)
        
    if sta.isconnected():
        print("IP:", sta.ifconfig()[0])
        return True
    else:
        print("Connection failed!")
        return False

def start_server():
    try:
        with open("voice_control.html") as f:
            html = f.read()
    except:
        html = "<h1>Voice Control Interface</h1>"

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 80))
    s.listen(5)

    while True:
        if not check_voltage():
            time.sleep(1)
            continue
            
        conn, addr = s.accept()
        request = conn.recv(1024).decode()
        
        response = html
        if 'GET /forward' in request:
            move('forward')
        elif 'GET /backward' in request:
            move('backward')
        elif 'GET /left' in request:
            move('left')
        elif 'GET /right' in request:
            move('right')
        elif 'GET /stop' in request:
            stop()

        conn.send('HTTP/1.1 200 OK\n')
        conn.send('Content-Type: text/html\n\n')
        conn.send(response)
        conn.close()

# ======================
# Main Execution
# ======================
if __name__ == "__main__":
    if connect_wifi("YOUR_SSID", "YOUR_PASSWORD"):
        start_server()
    else:
        print("Failed to initialize. Restarting...")
        machine.reset()
