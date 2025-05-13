import network
import socket
import machine
import time
from machine import Pin, PWM, ADC

# ======================
# Motor Configuration (4-Wheel)
# ======================
class MotorGroup:
    def __init__(self, front_fwd, front_bwd, rear_fwd, rear_bwd, pwm_pin):
        self.front_fwd = Pin(front_fwd, Pin.OUT)
        self.front_bwd = Pin(front_bwd, Pin.OUT)
        self.rear_fwd = Pin(rear_fwd, Pin.OUT)
        self.rear_bwd = Pin(rear_bwd, Pin.OUT)
        self.pwm = PWM(Pin(pwm_pin), freq=1000, duty=0)

    def drive(self, direction, speed=512):
        speed = min(1023, max(0, speed))
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
    front_fwd=27,   # Front Left Forward
    front_bwd=26,   # Front Left Backward
    rear_fwd=14,    # Rear Left Forward
    rear_bwd=12,    # Rear Left Backward
    pwm_pin=32      # Left PWM
)

right_side = MotorGroup(
    front_fwd=25,   # Front Right Forward
    front_bwd=33,   # Front Right Backward
    rear_fwd=13,    # Rear Right Forward
    rear_bwd=15,    # Rear Right Backward
    pwm_pin=14      # Right PWM
)

# ======================
# Power Management
# ======================
vin = ADC(Pin(35))  # Voltage monitoring on GPIO35
vin.atten(ADC.ATTN_11DB)

def check_voltage():
    raw = vin.read()
    voltage = (raw / 4095) * 3.3 * 2  # Voltage divider calculation
    if voltage < 7.0:  # Critical level for 2S LiPo
        stop()
        print(f"Low voltage: {voltage:.2f}V! Stopping...")
        return False
    return True

# ======================
# Movement Functions (4-Wheel)
# ======================
def stop():
    left_side.drive('stop')
    right_side.drive('stop')

def move(direction, speed=512):
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
# Access Point & Web Server
# ======================
def setup_ap():
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(
        essid='4WheelVoiceCar',
        password='voicecar123',
        authmode=network.AUTH_WPA_WPA2_PSK,
        channel=6
    )
    ap.ifconfig(('192.168.4.1', '255.255.255.0', '192.168.4.1', '8.8.8.8'))
    while not ap.active():
        pass
    print('AP Ready:', ap.ifconfig()[0])
    return ap

def load_html():
    try:
        with open('voice.html', 'r') as f:
            return f.read()
    except:
        return "<h1>Control Interface</h1><p>HTML file missing</p>"

def handle_request(conn):
    request = conn.recv(1024).decode()
    
    if '/forward' in request:
        move('forward')
    elif '/backward' in request:
        move('backward')
    elif '/left' in request:
        move('left')
    elif '/right' in request:
        move('right')
    elif '/stop' in request:
        stop()
    
    conn.send('HTTP/1.1 200 OK\n')
    conn.send('Content-Type: text/html\n\n')
    conn.send(load_html())
    conn.close()

def start_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('192.168.4.1', 80))
    s.listen(5)
    
    while True:
        conn, addr = s.accept()
        try:
            handle_request(conn)
        except Exception as e:
            print('Server error:', e)
        finally:
            conn.close()

# ======================
# Main Execution
# ======================
def main():
    stop()  # Initialize motors in stopped state
    setup_ap()
    start_server()

if __name__ == '__main__':
    main()
