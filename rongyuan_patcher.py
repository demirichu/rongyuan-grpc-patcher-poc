#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Rongyuan Keyboard Media Key Patcher PoC
Bypasses the UI limitations by communicating directly with the local gRPC service.
"""

import base64
import struct
import winreg
import requests
import time
import urllib3
import argparse
import sys

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TARGET_URL_BASE = "http://127.0.0.1:3814/driver.DriverGrpc/"
TARGET_VID = "3151"
TARGET_PID = "502D"
TARGET_MI = "02"

HEADERS = {
    "Host": "127.0.0.1:3814",
    "Connection": "keep-alive",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) GamingKeyboardDriver/2.1.89 Chrome/108.0.5359.215 Electron/22.3.15 Safari/537.36",
    "Content-Type": "application/grpc-web-text",
    "Accept": "application/grpc-web-text",
    "X-Grpc-Web": "1",
    "Sec-Fetch-Site": "cross-site",
    "Sec-Fetch-Mode": "cors"
}

def get_device_paths():
    """Scans the Windows Registry for the target HID device interfaces."""
    paths = []
    hid_guid = "{4d1e55b2-f16f-11cf-88cb-001111000030}"
    reg_path = fr"SYSTEM\CurrentControlSet\Control\DeviceClasses\{hid_guid}"
    
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path, 0, winreg.KEY_READ)
        num_subkeys = winreg.QueryInfoKey(key)[0]
        
        for i in range(num_subkeys):
            name = winreg.EnumKey(key, i)
            if f"VID_{TARGET_VID}" in name and f"PID_{TARGET_PID}" in name and f"MI_{TARGET_MI}" in name:
                paths.append(name.replace("##?#", "\\\\?\\"))
    except Exception as e:
        print(f"[-] Registry error: {e}")
    return paths

def build_payload(device_path: str) -> str:
    """Builds the dynamic gRPC/Protobuf payload for the HID feature report."""
    # 64-byte HID Feature Report
    hid = bytearray(64)
    hid[0] = 0x0A
    hid[1] = 0x00
    hid[2] = 0x5A
    hid[5] = 0x01
    
    # --- PATCH CORE ---
    hid[8] = 0x03  # Flag: Multimedia
    hid[10] = 0xCD # Keycode: Play/Pause
    
    # Protobuf packaging
    path_bytes = device_path.encode('utf-8')
    field1 = b'\x0A' + bytes([len(path_bytes)]) + path_bytes
    field2 = b'\x12\x40' + hid
    
    proto_payload = field1 + field2
    grpc_header = struct.pack(">B I", 0x00, len(proto_payload))
    
    final_bytes = grpc_header + proto_payload
    return base64.b64encode(final_bytes).decode('utf-8')

def inject_payload(sequence):
    """Executes the sequence against the local gRPC server."""
    session = requests.Session()
    session.headers.update(HEADERS)
    
    success_count = 0
    total = len(sequence)
    
    for method, payload in sequence:
        target_url = TARGET_URL_BASE + method
        
        try:
            res = session.post(target_url, data=payload, verify=False, timeout=3)
            if res.status_code == 200:
                success_count += 1
            else:
                print(f"    [-] Server rejected payload. HTTP {res.status_code}")
                break
            time.sleep(0.05) 
        except requests.exceptions.RequestException:
            print("    [-] Connection refused. Is iot_service.exe running?")
            break
            
    return success_count == total

def main():
    parser = argparse.ArgumentParser(description="PoC for patching Rongyuan Keyboard configurations via local gRPC.")
    parser.parse_args()

    print("[*] Rongyuan Configuration Patcher PoC")
    print("[*] Scanning Registry for target interfaces...")
    
    device_paths = get_device_paths()
    if not device_paths:
        print(f"[!] Target device (VID_{TARGET_VID}&PID_{TARGET_PID}) not found in Registry.")
        sys.exit(1)

    print(f"[+] Found {len(device_paths)} potential interface(s). Initiating payload sequence...")

    for path in device_paths:
        print(f"[*] Targeting: {path}")
        patched_b64 = build_payload(path)
        
        sequence = [
            ('sendMsg', patched_b64),
            ('changeWirelessLoopStatus', 'AAAAAAA='),
        ]
        
        if inject_payload(sequence):
            print("    [+] Payload successfully injected.")
        else:
            print("    [-] Injection failed for this interface.")

    print("[*] Operation complete. Test your hardware keys.")

if __name__ == "__main__":
    main()
