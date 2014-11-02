import subprocess as sp
import time

while True:
    process = sp.Popen(["python", "bot.py"])
    process.wait()
    if process.returncode == 0:
        # The child returned happily
        print("Daemon quit successfully, stopping.")
        break
    print("")
    print("Daemon crashed. Waiting a moment...")
    time.sleep(5)
    print("Restarting...")
