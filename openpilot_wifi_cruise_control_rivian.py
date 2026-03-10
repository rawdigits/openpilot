#!/usr/bin/env python3
"""WiFi Cruise Control for Rivian — accepts direct speed set, follow distance, or button presses.

Protocol:
  SET:<speed_mph>\n   — set cruise speed directly (e.g. "SET:71\n")
  GAP:<level>\n       — set follow distance (1=closest/aggressive, 2=standard, 3=relaxed, 4=relaxed)
  w                   — speed up +1 mph (button press)
  s                   — speed down -1 mph (button press)
  Arrow Up/Down       — same as w/s via telnet
"""

import socket
import threading
import time
from cereal import messaging
from openpilot.common.params import Params

MPH_TO_MS = 0.44704  # 1 mph in m/s

# Rivian follow level (1-4) → openpilot LongitudinalPersonality
# 0=aggressive, 1=standard, 2=relaxed
FOLLOW_MAP = {
    1: 0,  # Level 1 (closest)  → aggressive
    2: 1,  # Level 2            → standard
    3: 2,  # Level 3            → relaxed
    4: 2,  # Level 4 (farthest) → relaxed
}


class WiFiCruiseControl:
    def __init__(self, port=8080):
        self.port = port
        self.pm = messaging.PubMaster(['uiSetSpeed'])
        self.params = Params()
        self.running = True

    def send_button(self, signal):
        """Send uiSetSpeed message with button signal (+1/-1/0)"""
        msg = messaging.new_message('uiSetSpeed')
        msg.uiSetSpeed.buttonSignal = signal
        self.pm.send('uiSetSpeed', msg)

    def send_target_speed(self, speed_mph):
        """Send uiSetSpeed message with direct target speed"""
        msg = messaging.new_message('uiSetSpeed')
        msg.uiSetSpeed.targetSpeed = speed_mph * MPH_TO_MS
        self.pm.send('uiSetSpeed', msg)

    def set_follow_distance(self, rivian_level):
        """Set openpilot follow distance from Rivian level (1-4)"""
        personality = FOLLOW_MAP.get(rivian_level)
        if personality is not None:
            self.params.put_nonblocking('LongitudinalPersonality', str(personality))
            return True
        return False

    def press_button(self, signal, duration=0.1):
        """Press and release a button"""
        self.send_button(signal)  # Press
        time.sleep(duration)
        self.send_button(0)  # Release

    def handle_client(self, conn, addr):
        print(f"Client connected: {addr[0]}:{addr[1]}")

        # Enable character-at-a-time mode (telnet negotiation)
        conn.send(b"\xff\xfb\x01")  # IAC WILL ECHO
        conn.send(b"\xff\xfb\x03")  # IAC WILL SUPPRESS_GO_AHEAD
        conn.send(b"\xff\xfd\x03")  # IAC DO SUPPRESS_GO_AHEAD

        welcome = b"\r\n"
        welcome += b"========================================\r\n"
        welcome += b"   WiFi Cruise Control for Rivian\r\n"
        welcome += b"========================================\r\n"
        welcome += b"\r\n"
        welcome += b"Controls:\r\n"
        welcome += b"  w / Up Arrow    = Speed up (+1)\r\n"
        welcome += b"  s / Down Arrow  = Speed down (-1)\r\n"
        welcome += b"  SET:<mph>       = Set speed directly\r\n"
        welcome += b"  GAP:<1-4>       = Set follow distance\r\n"
        welcome += b"  q               = Quit\r\n"
        welcome += b"\r\n"
        conn.send(welcome)

        escape_seq = b""
        line_buf = b""

        try:
            while self.running:
                conn.settimeout(30.0)
                try:
                    data = conn.recv(1)
                except socket.timeout:
                    continue

                if not data:
                    break

                # Skip telnet IAC sequences
                if data[0] >= 0xF0:
                    conn.recv(2)
                    continue

                # Handle escape sequences (arrow keys)
                if data == b'\x1b':
                    escape_seq = data
                    continue
                elif escape_seq:
                    escape_seq += data
                    if data in (b'A', b'B', b'C', b'D'):
                        if escape_seq == b'\x1b[A':  # UP
                            conn.send(b"[+] Speed up\r\n")
                            print(f"[{addr[0]}] Speed UP (+1)")
                            self.press_button(1)
                        elif escape_seq == b'\x1b[B':  # DOWN
                            conn.send(b"[-] Speed down\r\n")
                            print(f"[{addr[0]}] Speed DOWN (-1)")
                            self.press_button(-1)
                        escape_seq = b""
                    elif len(escape_seq) > 5:
                        escape_seq = b""
                    continue

                char = data.decode('ascii', errors='ignore')

                # Line-based commands (SET:xx, GAP:x)
                if char == '\n' or char == '\r':
                    if line_buf:
                        line = line_buf.decode('ascii', errors='ignore').strip()
                        line_buf = b""
                        upper = line.upper()
                        if upper.startswith('SET:'):
                            try:
                                speed = float(line[4:])
                                if 5 <= speed <= 150:
                                    self.send_target_speed(speed)
                                    conn.send(f"[=] Set speed: {speed:.0f} mph\r\n".encode())
                                    print(f"[{addr[0]}] SET speed to {speed:.0f} mph")
                                else:
                                    conn.send(b"[!] Speed out of range (5-150)\r\n")
                            except ValueError:
                                conn.send(b"[!] Invalid speed value\r\n")
                        elif upper.startswith('GAP:'):
                            try:
                                level = int(line[4:])
                                if self.set_follow_distance(level):
                                    names = {1: "aggressive", 2: "standard", 3: "relaxed", 4: "relaxed"}
                                    name = names.get(level, "unknown")
                                    conn.send(f"[~] Follow: Level {level} ({name})\r\n".encode())
                                    print(f"[{addr[0]}] GAP Level {level} ({name})")
                                else:
                                    conn.send(b"[!] Invalid gap level (1-4)\r\n")
                            except ValueError:
                                conn.send(b"[!] Invalid gap value\r\n")
                    continue

                # Check if building a line command
                if char in 'SsEeTtGgAaPp:0123456789.' or line_buf:
                    line_buf += data
                    if len(line_buf) > 20:  # prevent buffer overflow
                        line_buf = b""
                    continue

                # Single-char commands
                if char == 'w':
                    conn.send(b"[+] Speed up\r\n")
                    print(f"[{addr[0]}] Speed UP (+1)")
                    self.press_button(1)
                elif char == 's':
                    conn.send(b"[-] Speed down\r\n")
                    print(f"[{addr[0]}] Speed DOWN (-1)")
                    self.press_button(-1)
                elif char == 'q':
                    conn.send(b"Bye!\r\n")
                    break

        except Exception as e:
            print(f"Client {addr[0]} error: {e}")
        finally:
            conn.close()
            print(f"Client disconnected: {addr[0]}")

    def run(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('0.0.0.0', self.port))
        server.listen(5)

        print("")
        print("========================================")
        print("  WiFi Cruise Control for Rivian")
        print("========================================")
        print(f"Listening on port {self.port}")
        print("")
        print("Connect from any device on comma WiFi:")
        print(f"  telnet <comma-ip> {self.port}")
        print("")
        print("Commands: w/s (buttons), SET:<mph> (direct), GAP:<1-4> (follow)")
        print("Press Ctrl+C to stop")
        print("")

        try:
            while self.running:
                server.settimeout(1.0)
                try:
                    conn, addr = server.accept()
                    threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True).start()
                except socket.timeout:
                    continue
        except KeyboardInterrupt:
            print("\nShutting down...")
        finally:
            server.close()
            print("Server stopped")

if __name__ == '__main__':
    WiFiCruiseControl(port=8080).run()
