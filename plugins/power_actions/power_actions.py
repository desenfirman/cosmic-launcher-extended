#!/usr/bin/env python3
import json
import os
import subprocess
import sys

ACTIONS = [
    ("Power off", "Shut down the system", ["systemctl", "poweroff"]),
    ("Reboot", "Restart the system", ["systemctl", "reboot"]),
    ("Suspend", "Suspend the system", ["systemctl", "suspend"]),
    ("Lock", "Lock the session", ["loginctl", "lock-session", "self"]),
    ("Log out", "End the current session", ["loginctl", "terminate-session", None]),
]


def send(value):
    sys.stdout.write(json.dumps(value) + "\n")
    sys.stdout.flush()


def main():
    while line := sys.stdin.readline():
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            continue
        if "Search" in request:
            query = request["Search"].casefold().removeprefix("power").strip()
            for index, (name, description, _) in enumerate(ACTIONS):
                if query in (name + " " + description).casefold():
                    send({"Append": {"id": index, "name": name, "description": description, "icon": {"Name": "system-shutdown"}}})
            send("Finished")
        elif "Activate" in request:
            index = request["Activate"]
            if 0 <= index < len(ACTIONS):
                command = ACTIONS[index][2][:]
                if command[-1] is None:
                    command[-1] = os.environ.get("XDG_SESSION_ID", "self")
                try:
                    subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
                except OSError:
                    pass
            send("Close")
            return
        elif "Exit" in request:
            return


if __name__ == "__main__":
    main()
