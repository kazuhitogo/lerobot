#!/usr/bin/env python3

import tkinter as tk
from tkinter import ttk
import threading
import time
from lerobot.robots.so101_follower import SO101Follower
from lerobot.robots.so101_follower.config_so101_follower import SO101FollowerConfig

class SO101ControlPanel:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("SO101 制御パネル")
        self.root.geometry("600x500")
        self.root.configure(bg="#2b2b2b")
        
        # サーボ名
        self.motors = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"]
        self.monitor_labels = {}
        self.sliders = {}
        self.control_labels = {}
        
        # GUI作成
        self.create_widgets()
        
        # ロボット初期化
        config = SO101FollowerConfig(
            port="/dev/tty.usbmodem5AB90678311",
            id="my_first_follower_arm"
        )
        self.robot = SO101Follower(config)
        self.running = False
        
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
        
        for i, motor in enumerate(self.motors):
            name_label = tk.Label(monitor_frame, text=f"{motor}:", font=("Arial", 10, "bold"),
                                bg="#2b2b2b", fg="#ffffff", width=12, anchor="w")
            name_label.grid(row=i, column=0, sticky="w", padx=5, pady=3)
            
            value_label = tk.Label(monitor_frame, text="0.0", font=("Arial", 11, "bold"),
                                 bg="#4a90e2", fg="#ffffff", width=8, anchor="center",
                                 relief="raised", bd=2)
            value_label.grid(row=i, column=1, padx=5, pady=3)
            
            self.monitor_labels[motor] = value_label
        
        # 右側：コントローラ
        control_frame = tk.LabelFrame(main_frame, text="手動制御", font=("Arial", 12, "bold"),
                                    bg="#2b2b2b", fg="#ffffff", bd=2, relief="groove")
        control_frame.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        for i, motor in enumerate(self.motors):
            name_label = tk.Label(control_frame, text=f"{motor}:", font=("Arial", 9, "bold"),
                                bg="#2b2b2b", fg="#ffffff", width=12, anchor="w")
            name_label.grid(row=i, column=0, sticky="w", padx=3, pady=2)
            
            # Gripperは0-100、他は-180から180
            if motor == "gripper":
                slider_range = (0, 100)
            else:
                slider_range = (-180, 180)
            
            slider = tk.Scale(control_frame, from_=slider_range[0], to=slider_range[1], orient="horizontal",
                            bg="#666666", fg="#ffffff", font=("Arial", 8),
                            highlightbackground="#2b2b2b", troughcolor="#444444",
                            length=150, command=lambda val, m=motor: self.on_slider_change(m, val))
            slider.grid(row=i, column=1, padx=3, pady=2)
            
            # Gripperは中間値、他は0
            if motor == "gripper":
                slider.set(50)
            else:
                slider.set(0)
            
            target_label = tk.Label(control_frame, text="0", font=("Arial", 9, "bold"),
                                  bg="#ff6b35", fg="#ffffff", width=6, anchor="center")
            target_label.grid(row=i, column=2, padx=3, pady=2)
            
            self.sliders[motor] = slider
            self.control_labels[motor] = target_label
        
        # ボタンフレーム
        button_frame = tk.Frame(self.root, bg="#2b2b2b")
        button_frame.pack(pady=15)
        
        self.connect_btn = tk.Button(button_frame, text="接続", command=self.toggle_connection,
                                   bg="#28a745", fg="#ffffff", font=("Arial", 11, "bold"),
                                   relief="raised", bd=3, padx=20, pady=5,
                                   activebackground="#218838", activeforeground="#ffffff")
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
    
    def toggle_connection(self):
        if not self.running:
            self.start_monitoring()
        else:
            self.stop_monitoring()
    
    def start_monitoring(self):
        try:
            self.robot.connect()
            self.running = True
            self.connect_btn.config(text="切断", bg="#dc3545", fg="#ffffff",
                                  activebackground="#c82333", activeforeground="#ffffff")
            self.status_label.config(text="接続中", fg="#28a745")
            
            # 監視スレッド開始
            self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
            self.monitor_thread.start()
            
        except Exception as e:
            self.status_label.config(text=f"エラー: {str(e)}", fg="#dc3545")
    
    def stop_monitoring(self):
        self.running = False
        try:
            self.robot.disconnect()
        except:
            pass
        self.connect_btn.config(text="接続", bg="#28a745", fg="#ffffff",
                              activebackground="#218838", activeforeground="#ffffff")
        self.status_label.config(text="未接続", fg="#ffc107")
    
    def monitor_loop(self):
        while self.running:
            try:
                obs = self.robot.get_observation()
                self.root.after(0, self.update_monitor, obs)
                time.sleep(0.1)
            except Exception as e:
                self.root.after(0, lambda: self.status_label.config(text=f"エラー: {str(e)}", fg="#dc3545"))
                break
    
    def update_monitor(self, obs):
        for motor in self.motors:
            key = f"{motor}.pos"
            if key in obs:
                value = obs[key]
                self.monitor_labels[motor].config(text=f"{value:.1f}")
    
    def on_slider_change(self, motor, value):
        if not self.running:
            return
        
        try:
            val = float(value)
            self.control_labels[motor].config(text=f"{val:.0f}")
            
            # ロボットに送信
            action = {f"{motor}.pos": val}
            self.robot.send_action(action)
            
        except Exception as e:
            self.status_label.config(text=f"制御エラー", fg="#dc3545")
    
    def reset_positions(self):
        for motor in self.motors:
            self.sliders[motor].set(0)
    
    def sync_sliders(self):
        if not self.running:
            return
        try:
            obs = self.robot.get_observation()
            for motor in self.motors:
                key = f"{motor}.pos"
                if key in obs:
                    self.sliders[motor].set(obs[key])
        except Exception as e:
            self.status_label.config(text=f"同期エラー", fg="#dc3545")
    
    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
    
    def on_closing(self):
        if self.running:
            self.stop_monitoring()
        self.root.destroy()

if __name__ == "__main__":
    app = SO101ControlPanel()
    app.run()
