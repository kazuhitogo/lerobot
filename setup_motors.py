#!/usr/bin/env python3

import argparse
from feetech_servo_sdk import *

def setup_motors(port):
    """Setup motor IDs for SO101 follower arm"""
    
    motors = {
        "shoulder_pan": 1,
        "shoulder_lift": 2, 
        "elbow_flex": 3,
        "wrist_flex": 4,
        "wrist_roll": 5,
        "gripper": 6
    }
    
    # Initialize PortHandler and PacketHandler
    portHandler = PortHandler(port)
    packetHandler = PacketHandler(PROTOCOL_VERSION)
    
    if not portHandler.openPort():
        print(f"Failed to open port {port}")
        return False
        
    portHandler.setBaudRate(1000000)
    
    for motor_name, target_id in reversed(list(motors.items())):
        input(f"Connect the controller board to the '{motor_name}' motor only and press enter.")
        
        # Scan for connected motor (usually ID 1 by default)
        for scan_id in range(1, 10):
            dxl_model_number, dxl_comm_result, dxl_error = packetHandler.ping(portHandler, scan_id)
            if dxl_comm_result == COMM_SUCCESS:
                print(f"Found motor at ID {scan_id}, setting to ID {target_id}")
                
                # Change ID
                dxl_comm_result, dxl_error = packetHandler.write1ByteTxRx(
                    portHandler, scan_id, ADDR_STS_ID, target_id
                )
                
                if dxl_comm_result == COMM_SUCCESS:
                    print(f"'{motor_name}' motor id set to {target_id}")
                else:
                    print(f"Failed to set ID for {motor_name}")
                break
        else:
            print(f"No motor found for {motor_name}")
    
    portHandler.closePort()
    return True

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", required=True, help="Serial port (e.g., /dev/tty.usbmodem5AB90678311)")
    args = parser.parse_args()
    
    setup_motors(args.port)

if __name__ == "__main__":
    main()
