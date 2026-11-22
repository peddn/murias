"""
Kleiner Telnet-Client zum Testen: schickt Befehle an einen laufenden Server
und gibt den Mitschnitt aus.

    python tools/play.py <account> <passwort> "befehl 1" "befehl 2" ...

Mit `--ansi` bleiben die Farbcodes erhalten, sonst werden sie entfernt.

"""

import re
import socket
import sys
import time

HOST, PORT = "localhost", 4000
IAC = 255
ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def strip_telnet(data):
    """Telnet-Verhandlungen (IAC ...) aus den Rohdaten entfernen."""
    out = bytearray()
    i = 0
    while i < len(data):
        byte = data[i]
        if byte == IAC and i + 1 < len(data):
            command = data[i + 1]
            if command == 250:  # Subnegotiation bis IAC SE
                end = data.find(bytes([IAC, 240]), i)
                i = len(data) if end < 0 else end + 2
            elif command in (251, 252, 253, 254):
                i += 3
            else:
                i += 2
        else:
            out.append(byte)
            i += 1
    return out.decode("utf-8", errors="replace")


def read(sock, wait=0.6):
    time.sleep(wait)
    chunks = b""
    sock.settimeout(0.3)
    try:
        while True:
            chunk = sock.recv(65536)
            if not chunk:
                break
            chunks += chunk
    except socket.timeout:
        pass
    return strip_telnet(chunks).replace("\r", "")


def play(account, password, commands, keep_ansi=False):
    transcript = []
    with socket.create_connection((HOST, PORT)) as sock:
        read(sock, 1.0)
        for command in [f"connect {account} {password}", *commands]:
            sock.sendall(command.encode("utf-8") + b"\n")
            output = read(sock)
            if not keep_ansi:
                output = ANSI.sub("", output)
            shown = "connect ..." if command.startswith("connect ") else command
            transcript.append(f"> {shown}\n{output.strip()}\n")
    return "\n".join(transcript)


if __name__ == "__main__":
    args = [arg for arg in sys.argv[1:] if arg != "--ansi"]
    if len(args) < 2:
        print(__doc__)
        sys.exit(2)
    print(play(args[0], args[1], args[2:], keep_ansi="--ansi" in sys.argv))
