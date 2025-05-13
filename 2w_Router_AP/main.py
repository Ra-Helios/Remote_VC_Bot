import network
import socket
import machine
import time

# Motor Control Pins (ESP32-WROOM)
left_fwd = machine.Pin(27, machine.Pin.OUT)
left_bwd = machine.Pin(26, machine.Pin.OUT)
right_fwd = machine.Pin(25, machine.Pin.OUT)
right_bwd = machine.Pin(33, machine.Pin.OUT)

# WiFi Config
SSID = "YOUR_WIFI"
PASSWORD = "YOUR_PASSWORD"

sta = network.WLAN(network.STA_IF)
sta.active(True)
sta.connect(SSID, PASSWORD)

while not sta.isconnected():
    pass

print("IP:", sta.ifconfig()[0])

# Load HTML
with open("voice_control.html", "r") as f:
    html = f.read()

# Web Server
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('', 80))
s.listen(5)

def move(cmd):
    left_fwd.value(0)
    left_bwd.value(0)
    right_fwd.value(0)
    right_bwd.value(0)
    
    if cmd == 'forward':
        left_fwd.value(1)
        right_fwd.value(1)
    elif cmd == 'backward':
        left_bwd.value(1)
        right_bwd.value(1)
    elif cmd == 'left':
        right_fwd.value(1)
        left_bwd.value(1)
    elif cmd == 'right':
        left_fwd.value(1)
        right_bwd.value(1)

while True:
    conn, addr = s.accept()
    request = conn.recv(1024).decode()
    
    if 'GET /forward' in request:
        move('forward')
    elif 'GET /backward' in request:
        move('backward')
    elif 'GET /left' in request:
        move('left')
    elif 'GET /right' in request:
        move('right')
    
    conn.send('HTTP/1.1 200 OK\n')
    conn.send('Content-Type: text/html\n\n')
    conn.send(html)
    conn.close()
