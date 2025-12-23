# Minimal SO101 Control

Simple standalone Python scripts for SO101 robot arm control.

## Requirements
- Python 3.10+
- uv

## Installation
```bash
uv sync
```

## Usage

### 1. Find Port
```bash
uv run so101-find-port
```

### 2. Setup Motors
```bash
uv run so101-setup-motors --port /dev/tty.usbmodem5AB90678311
```

### 3. Calibrate
```bash
uv run so101-calibrate --port /dev/tty.usbmodem5AB90678311 --robot_id my_first_follower_arm
```

### 4. Control Panel
```bash
uv run so101-control-panel /dev/tty.usbmodem5AB90678311
```

## Complete Workflow
```bash
# Install dependencies
uv sync

# Find the USB port
uv run so101-find-port

# Setup motor IDs (connect motors one by one as prompted)
uv run so101-setup-motors --port /dev/tty.usbmodem5AB90678311

# Calibrate the robot arm
uv run so101-calibrate --port /dev/tty.usbmodem5AB90678311 --robot_id my_first_follower_arm

# Launch control panel GUI
uv run so101-control-panel /dev/tty.usbmodem5AB90678311
```
