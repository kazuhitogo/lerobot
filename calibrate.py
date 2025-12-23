#!/usr/bin/env python3

import argparse
import json
import os
from pathlib import Path
from feetech_servo_sdk import *

class SO101Calibrator:
    def __init__(self, port, robot_id):
        self.port = port
        self.robot_id = robot_id
        self.motors = {
            "shoulder_pan": 1,
            "shoulder_lift": 2,
            "elbow_flex": 3, 
            "wrist_flex": 4,
            "wrist_roll": 5,
            "gripper": 6
        }
        
        # Initialize communication
        self.portHandler = PortHandler(port)
        self.packetHandler = PacketHandler(PROTOCOL_VERSION)
        
    def connect(self):
        if not self.portHandler.openPort():
            raise Exception(f"Failed to open port {self.port}")
        self.portHandler.setBaudRate(1000000)
        
    def disconnect(self):
        self.portHandler.closePort()
        
    def disable_torque(self):
        for motor_id in self.motors.values():
            self.packetHandler.write1ByteTxRx(self.portHandler, motor_id, ADDR_STS_TORQUE_ENABLE, 0)
            
    def enable_torque(self):
        for motor_id in self.motors.values():
            self.packetHandler.write1ByteTxRx(self.portHandler, motor_id, ADDR_STS_TORQUE_ENABLE, 1)
            
    def read_position(self, motor_id):
        position, _, _ = self.packetHandler.read2ByteTxRx(self.portHandler, motor_id, ADDR_STS_PRESENT_POSITION)
        return position
        
    def calibrate(self):
        print(f"Running calibration of SO101 (port={self.port}, id={self.robot_id})")
        
        self.disable_torque()
        
        input("Move robot to the middle of its range of motion and press ENTER....")
        
        # Record homing positions
        homing_offsets = {}
        for motor_name, motor_id in self.motors.items():
            pos = self.read_position(motor_id)
            homing_offsets[motor_name] = pos
            print(f"{motor_name}: homing offset = {pos}")
            
        print("Move all joints sequentially through their entire ranges of motion.")
        print("Recording positions. Press ENTER to stop...")
        
        range_mins = {name: 4095 for name in self.motors.keys()}
        range_maxes = {name: 0 for name in self.motors.keys()}
        
        # Record range of motion
        import threading
        import time
        
        recording = True
        
        def record_loop():
            while recording:
                for motor_name, motor_id in self.motors.items():
                    pos = self.read_position(motor_id)
                    range_mins[motor_name] = min(range_mins[motor_name], pos)
                    range_maxes[motor_name] = max(range_maxes[motor_name], pos)
                time.sleep(0.1)
                
        record_thread = threading.Thread(target=record_loop)
        record_thread.start()
        
        input()  # Wait for user to press enter
        recording = False
        record_thread.join()
        
        # Save calibration
        calibration = {}
        for motor_name in self.motors.keys():
            calibration[motor_name] = {
                "id": self.motors[motor_name],
                "drive_mode": 0,
                "homing_offset": homing_offsets[motor_name],
                "range_min": range_mins[motor_name],
                "range_max": range_maxes[motor_name]
            }
            
        # Save to file
        calib_dir = Path.home() / ".cache" / "lerobot" / "calibration" / "so101_follower"
        calib_dir.mkdir(parents=True, exist_ok=True)
        calib_file = calib_dir / f"{self.robot_id}.json"
        
        with open(calib_file, 'w') as f:
            json.dump(calibration, f, indent=2)
            
        print(f"Calibration saved to {calib_file}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", required=True, help="Serial port")
    parser.add_argument("--robot_id", required=True, help="Robot ID")
    args = parser.parse_args()
    
    calibrator = SO101Calibrator(args.port, args.robot_id)
    calibrator.connect()
    try:
        calibrator.calibrate()
    finally:
        calibrator.disconnect()

if __name__ == "__main__":
    main()
