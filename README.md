# Rongyuan Config Patcher PoC

This repository contains a Proof of Concept (PoC) script to bypass the limitations of the official Rongyuan keyboard driver software.

## The Issue
The default Electron-based driver restricts users from assigning certain multimedia functions (e.g., Play/Pause) to standard keys like the `Pause` button. The UI blocks the interaction, but the underlying hardware (`iot_service.exe` and the MCU) is perfectly capable of handling it.

## How it works
This script bypasses the restricted UI layer and talks directly to the local gRPC server (`iot_service.exe`). 
1. It dynamically resolves the active USB Device Interface path from the Windows Registry.
2. It constructs a raw 64-byte HID feature report, patching the Multimedia Flag (`0x03`) and the Play/Pause Keycode (`0xCD`).
3. It wraps the HID payload in Protobuf, applies the gRPC frame headers, and injects it into the local service, permanently saving the configuration to the keyboard's memory.

## Usage
**Prerequisites:** Windows OS, Python 3.x, and the official driver running in the background.

```bash
git clone [https://github.com/demirichu/rongyuan-grpc-patcher-poc.git](https://github.com/demirichu/rongyuan-grpc-patcher-poc.git)
cd rongyuan-grpc-patcher-poc
pip install -r requirements.txt
python rongyuan_patcher.py
```
