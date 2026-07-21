import subprocess, sys, os, time, threading
from datetime import datetime

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py")
PYTHON = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".venv312", "Scripts", "python.exe")
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "watchdog.log")

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

log(f"=== Watchdog started ===")
log(f"Python: {PYTHON}")
log(f"Script: {SCRIPT}")

proc = None

def reader(stream, tag):
    try:
        for raw in iter(stream.readline, b""):
            try:
                line = raw.decode("utf-8", errors="replace").rstrip()
            except Exception:
                line = str(raw)
            if line.strip():
                log(f"[{tag}] {line}")
    except Exception:
        pass

try:
    proc = subprocess.Popen(
        [PYTHON, SCRIPT],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.DEVNULL,
    )
    log(f"PID={proc.pid} started")

    t1 = threading.Thread(target=reader, args=(proc.stdout, "OUT"), daemon=True)
    t2 = threading.Thread(target=reader, args=(proc.stderr, "ERR"), daemon=True)
    t1.start(); t2.start()

    log("Waiting for process... (Ctrl+C to stop)")
    exit_code = proc.wait()

    t1.join(timeout=2)
    t2.join(timeout=2)

    log(f"Process exited with code {exit_code}")
    if exit_code != 0 and exit_code != -1073741510:  # -1073741510 = Ctrl+C
        log(f"!!! NON-ZERO EXIT CODE: {exit_code} !!!")

except KeyboardInterrupt:
    log("Watchdog stopped by user (Ctrl+C)")
    if proc and proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
except Exception as e:
    log(f"Watchdog error: {e}")
    import traceback
    log(traceback.format_exc())

log("=== Watchdog stopped ===")
