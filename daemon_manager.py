import sys
import subprocess as sp
import time
from datetime import datetime

usage_message = """
Usage: {} <script.py>

where <script.py> is a python script to be kept alive
"""

crash_message = """
Daemon crashed:
Uptime: {}
Waiting a moment before restarting..."""

if len(sys.argv) < 2:
    print(usage_message.format(sys.argv[0]))
    exit(1)

child_name = sys.argv[1]
print("Running {} as a daemon\n".format(child_name))


def pretty_time(t):
    if t >= 3600:
        return "{}h {}m {}s".format(
            int(t//3600),
            int(t//60)%60,
            format(t%60, "0.0f")
        )
    elif t >= 60:
        return "{}m {}s".format(
            int(t//60)%60,
            format(t%60, "0.1f")
        )
    else:
        return "{}s".format(format(t%60, "0.2f"))

while True:
    start = time.time()
    process = sp.Popen(["python", child_name])
    process.wait()
    if process.returncode == 0:
        # The child returned happily
        print("Daemon quit successfully, stopping.")
        break
    print("")
    print(crash_message.format(pretty_time(time.time() - start)))
    with open("log.txt", "a+") as logFile:
        logFile.write("{uptime}, {timeAndDate}\n".format(uptime = pretty_time(time.time() - start), timeAndDate = str(datetime.now())))
	#Close the file:
        logFile.close()
    time.sleep(3)
    print("Restarting...")
