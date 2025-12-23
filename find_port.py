#!/usr/bin/env python3

import platform
import time
from pathlib import Path

def find_available_ports():
    from serial.tools import list_ports
    
    if platform.system() == "Windows":
        ports = [port.device for port in list_ports.comports()]
    else:
        ports = [str(path) for path in Path("/dev").glob("tty*")]
    return ports

def find_port():
    print("Finding all available ports for the MotorsBus.")
    ports_before = find_available_ports()
    print("Ports before disconnecting:", ports_before)

    print("Remove the USB cable from your MotorsBus and press Enter when done.")
    input()

    time.sleep(0.5)
    ports_after = find_available_ports()
    ports_diff = list(set(ports_before) - set(ports_after))

    if len(ports_diff) == 1:
        port = ports_diff[0]
        print(f"The port of this MotorsBus is '{port}'")
        print("Reconnect the USB cable.")
    elif len(ports_diff) == 0:
        raise OSError(f"Could not detect the port. No difference was found ({ports_diff}).")
    else:
        raise OSError(f"Could not detect the port. More than one port was found ({ports_diff}).")

def main():
    find_port()

if __name__ == "__main__":
    main()
