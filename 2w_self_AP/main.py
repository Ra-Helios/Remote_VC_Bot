import network
import socket
import machine
import time
from machine import Pin, PWM

# ======================
# Motor Configuration
# ======================
# Define motor pins (adjust according to your wiring)
LEFT_FWD = Pin(27, Pin.OUT)
LEFT_BWD = Pin(26, Pin.OUT)
RIGHT_FWD = Pin(25, Pin.OUT)
RIGHT_BWD = Pin(33, Pin.OUT)

# PWM Configuration
LEFT_PWM = PWM(Pin(32), freq=1000, duty=0)
RIGHT_PWM = PWM(Pin(14), freq=1000, duty=0)

def stop():
    LEFT_FWD.value(0)
    LEFT_BWD.value(0)
    RIGHT_FWD.value(0)
    RIGHT_BWD.value(0)
    LEFT_PWM.duty(0)
    RIGHT_PWM.duty(0)

def move_forward(speed=512):
    stop()
    LEFT_FWD.value(1)
    RIGHT_FWD.value(1)
    LEFT_PWM.duty(speed)
    RIGHT_PWM.duty(speed)

def move_backward(speed=512):
    stop()
    LEFT_BWD.value(1)
    RIGHT_BWD.value(1)
    LEFT_PWM.duty(speed)
    RIGHT_PWM.duty(speed)

def turn_left(speed=512):
    stop()
    RIGHT_FWD.value(1)
    LEFT_BWD.value(1)
    LEFT_PWM.duty(speed)
    RIGHT_PWM.duty(speed)

def turn_right(speed=512):
    stop()
    LEFT_FWD.value(1)
    RIGHT_BWD.value(1)
    LEFT_PWM.duty(speed)
    RIGHT_PWM.duty(speed)

# ======================
# Access Point Setup
# ======================
def setup_ap():
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(
        essid='VoiceCarAP',
        password='voicecar123',
        authmode=network.AUTH_WPA_WPA2_PSK,
        channel=6
    )
    ap.ifconfig(('192.168.4.1', '255.255.255.0', '192.168.4.1', '8.8.8.8'))
    while not ap.active():
        pass
    print('Access Point Ready!')
    print('SSID: VoiceCarAP')
    print('Password: voicecar123')
    print('AP IP:', ap.ifconfig()[0])
    return ap

# ======================
# Web Server & HTML Handling
# ======================
def load_html():
    try:
        with open('voice.html', 'r') as f:
            return f.read()
    except:
        return """<html><body><h1>Error: Interface File Missing</h1></body></html>"""

def handle_request(conn):
    request = conn.recv(1024).decode()
    
    # Process commands
    if '/forward' in request:
        move_forward()
    elif '/backward' in request:
        move_backward()
    elif '/left' in request:
        turn_left()
    elif '/right' in request:
        turn_right()
    elif '/stop' in request:
        stop()
    
    # Send response
    response = load_html()
    conn.send('HTTP/1.1 200 OK\n')
    conn.send('Content-Type: text/html\n')
    conn.send('Connection: close\n\n')
    conn.send(response)
    conn.close()

def start_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('192.168.4.1', 80))
    s.listen(5)
    print('Web server started')
    
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
    # Initialize motors
    stop()
    
    # Setup Access Point
    ap = setup_ap()
    
    # Start web server
    start_server()

if __name__ == '__main__':
    main()
