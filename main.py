import subprocess
import time
import json

print("Starting gen.py...")
gen_process = subprocess.Popen(["python3", "gen.py"])

print("Starting statusbot.py...")
gen_process = subprocess.Popen(["python3", "statusbot.py"])

print("Both bots have been started. The main script will remain active.")
print("Press Ctrl+C to stop.")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nStopping bots...")
    gen_process.terminate()
    backup_process.terminate()
    print("Bots have been stopped.")
