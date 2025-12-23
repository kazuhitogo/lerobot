#!/usr/bin/env python3

import tkinter as tk
from tkinter import ttk
import threading
import time
import json
from pathlib import Path
from feetech_servo_sdk import *

class SO101ControlPanel:
    def __init__(self, port="/dev/tty.usbmodem5AB90678311", robot_id="my_first_follower_arm"):
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
        
        # Communication
        self.portHandler = None
        self.packetHandler = None
        self.connected = False
        self.running = False
        
        # GUI setup
        self.root = tk.Tk()
        self.root.title("SO101 制御パネル")
        self.root.geometry("600x500")
        self.root.configure(bg="#2b2b2b")
        
        self.monitor_labels = {}
        self.sliders = {}
        self.control_labels = {}
        
        self.create_widgets()
        
    def create_widgets(self):
        # タイトル
        title = tk.Label(self.root, text="SO101 制御パネル", font=("Arial", 18, "bold"),
                        bg="#2b2b2b", fg="#ffffff")
        title.pack(pady=10)
        
        # メインフレーム
        main_frame = tk.Frame(self.root, bg="#2b2b2b")
        main_frame.pack(padx=20, pady=10, fill="both", expand=True)
        
        # 左側：モニター
        monitor_frame = tk.LabelFrame(main_frame, text="現在値モニター", font=("Arial", 12, "bold"),
                                    bg="#2b2b2b", fg="#ffffff", bd=2, relief="groove")
        monitor_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        for i, motor in enumerate(self.motors.keys()):
            name_label = tk.Label(monitor_frame, text=f"{motor}:", font=("Arial", 10, "bold"),
                                bg="#2b2b2b", fg="#ffffff", width=12, anchor="w")
            name_label.grid(row=i, column=0, sticky="w", padx=5, pady=3)
            
            value_label = tk.Label(monitor_frame, text="0", font=("Arial", 11, "bold"),
                                 bg="#4a90e2", fg="#ffffff", width=8, anchor="center",
                                 relief="raised", bd=2)
            value_label.grid(row=i, column=1, padx=5, pady=3)
            
            self.monitor_labels[motor] = value_label
        
        # 右側：コントローラ
        control_frame = tk.LabelFrame(main_frame, text="手動制御", font=("Arial", 12, "bold"),
                                    bg="#2b2b2b", fg="#ffffff", bd=2, relief="groove")
        control_frame.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        for i, motor in enumerate(self.motors.keys()):
            name_label = tk.Label(control_frame, text=f"{motor}:", font=("Arial", 9, "bold"),
                                bg="#2b2b2b", fg="#ffffff", width=12, anchor="w")
            name_label.grid(row=i, column=0, sticky="w", padx=3, pady=2)
            
            if motor == "gripper":
                slider_range = (0, 4095)
            else:
                slider_range = (0, 4095)
            
            slider = tk.Scale(control_frame, from_=slider_range[0], to=slider_range[1], orient="horizontal",
                            bg="#666666", fg="#ffffff", font=("Arial", 8),
                            highlightbackground="#2b2b2b", troughcolor="#444444",
                            length=150, command=lambda val, m=motor: self.on_slider_change(m, val))
            slider.grid(row=i, column=1, padx=3, pady=2)
            slider.set(2048)  # Middle position
            
            target_label = tk.Label(control_frame, text="2048", font=("Arial", 9, "bold"),
                                  bg="#ff6b35", fg="#ffffff", width=6, anchor="center")
            target_label.grid(row=i, column=2, padx=3, pady=2)
            
            self.sliders[motor] = slider
            self.control_labels[motor] = target_label
        
        # ボタンフレーム
        button_frame = tk.Frame(self.root, bg="#2b2b2b")
        button_frame.pack(pady=15)
        
        self.connect_btn = tk.Button(button_frame, text="接続", command=self.toggle_connection,
                                   bg="#28a745", fg="#ffffff", font=("Arial", 11, "bold"),
                                   relief="raised", bd=3, padx=20, pady=5)
        self.connect_btn.pack(side="left", padx=10)
        
        reset_btn = tk.Button(button_frame, text="リセット", command=self.reset_positions,
                            bg="#ffc107", fg="#000000", font=("Arial", 11, "bold"),
                            relief="raised", bd=3, padx=15, pady=5)
        reset_btn.pack(side="left", padx=10)
        
        sync_btn = tk.Button(button_frame, text="現在値同期", command=self.sync_sliders,
                           bg="#17a2b8", fg="#ffffff", font=("Arial", 11, "bold"),
                           relief="raised", bd=3, padx=15, pady=5)
        sync_btn.pack(side="left", padx=10)
        
        self.status_label = tk.Label(button_frame, text="未接続", font=("Arial", 11, "bold"),
                                   bg="#2b2b2b", fg="#ffc107")
        self.status_label.pack(side="left", padx=15)
    
    def connect_robot(self):
        self.portHandler = PortHandler(self.port)
        self.packetHandler = PacketHandler(PROTOCOL_VERSION)
        
        if not self.portHandler.openPort():
            raise Exception(f"Failed to open port {self.port}")
        
        self.portHandler.setBaudRate(1000000)
        
        # Enable torque for all motors
        for motor_id in self.motors.values():
            self.packetHandler.write1ByteTxRx(self.portHandler, motor_id, ADDR_STS_TORQUE_ENABLE, 1)
        
        self.connected = True
        
    def disconnect_robot(self):
        if self.portHandler:
            # Disable torque
            for motor_id in self.motors.values():
                self.packetHandler.write1ByteTxRx(self.portHandler, motor_id, ADDR_STS_TORQUE_ENABLE, 0)
            self.portHandler.closePort()
        self.connected = False
        
    def toggle_connection(self):
        if not self.running:
            self.start_monitoring()
        else:
            self.stop_monitoring()
    
    def start_monitoring(self):
        try:
            self.connect_robot()
            self.running = True
            self.connect_btn.config(text="切断", bg="#dc3545")
            self.status_label.config(text="接続中", fg="#28a745")
            
            self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
            self.monitor_thread.start()
            
        except Exception as e:
            self.status_label.config(text=f"エラー: {str(e)}", fg="#dc3545")
    
    def stop_monitoring(self):
        self.running = False
        try:
            self.disconnect_robot()
        except:
            pass
        self.connect_btn.config(text="接続", bg="#28a745")
        self.status_label.config(text="未接続", fg="#ffc107")
    
    def monitor_loop(self):
        while self.running:
            try:
                positions = {}
                for motor_name, motor_id in self.motors.items():
                    pos, _, _ = self.packetHandler.read2ByteTxRx(
                        self.portHandler, motor_id, ADDR_STS_PRESENT_POSITION
                    )
                    positions[motor_name] = pos
                
                self.root.after(0, self.update_monitor, positions)
                time.sleep(0.1)
            except Exception as e:
                self.root.after(0, lambda: self.status_label.config(text=f"エラー", fg="#dc3545"))
                break
    
    def update_monitor(self, positions):
        for motor, pos in positions.items():
            self.monitor_labels[motor].config(text=str(pos))
    
    def on_slider_change(self, motor, value):
        if not self.running:
            return
        
        try:
            val = int(float(value))
            self.control_labels[motor].config(text=str(val))
            
            motor_id = self.motors[motor]
            self.packetHandler.write2ByteTxRx(
                self.portHandler, motor_id, ADDR_STS_GOAL_POSITION, val
            )
            
        except Exception as e:
            self.status_label.config(text="制御エラー", fg="#dc3545")
    
    def reset_positions(self):
        for motor in self.motors.keys():
            self.sliders[motor].set(2048)
    
    def sync_sliders(self):
        if not self.running:
            return
        try:
            for motor_name, motor_id in self.motors.items():
                pos, _, _ = self.packetHandler.read2ByteTxRx(
                    self.portHandler, motor_id, ADDR_STS_PRESENT_POSITION
                )
                self.sliders[motor_name].set(pos)
        except Exception as e:
            self.status_label.config(text="同期エラー", fg="#dc3545")
    
    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
    
    def on_closing(self):
        if self.running:
            self.stop_monitoring()
        self.root.destroy()

def main():
    import sys
    port = sys.argv[1] if len(sys.argv) > 1 else "/dev/tty.usbmodem5AB90678311"
    app = SO101ControlPanel(port)
    app.run()

if __name__ == "__main__":
    main()
