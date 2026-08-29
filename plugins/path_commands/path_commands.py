#!/usr/bin/env python3
import json
import os
import subprocess
import sys


def commands_from_path():
    commands = {}
    for directory in os.environ.get("PATH", "").split(os.pathsep):
        if not directory:
            continue
        try:
            entries = os.scandir(directory)
        except OSError:
            continue
        with entries:
            for entry in entries:
                name = entry.name
                if name in commands or not name or "/" in name:
                    continue
                try:
                    if not entry.is_file(follow_symlinks=True) or not os.access(entry.path, os.X_OK):
                        continue
                    name.encode("utf-8")
                except (OSError, UnicodeError):
                    continue
                commands[name] = os.path.realpath(entry.path)
    return sorted(commands.items(), key=lambda item: item[0].casefold())


def send(message):
    sys.stdout.write(json.dumps(message, ensure_ascii=True) + "\n")
    sys.stdout.flush()


def main():
    commands = commands_from_path()
    current_results = []
    while True:
        line = sys.stdin.readline()
        if not line:
            return
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            continue

        if "Search" in request:
            query = request["Search"].casefold().strip()
            current_results = (
                commands
                if not query
                else [command for command in commands if query in command[0].casefold()]
            )
            for command_id, (name, path) in enumerate(current_results):
                send(
                    {
                        "Append": {
                            "id": command_id,
                            "name": name,
                            "description": path,
                            "exec": path,
                        }
                    }
                )
            send("Finished")
        elif "Activate" in request:
            command_id = request["Activate"]
            if 0 <= command_id < len(current_results):
                try:
                    subprocess.Popen(
                        [current_results[command_id][1]],
                        stdin=subprocess.DEVNULL,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        start_new_session=True,
                    )
                except OSError:
                    pass
            send("Close")
            return
        elif "Exit" in request:
            return


if __name__ == "__main__":
    main()
