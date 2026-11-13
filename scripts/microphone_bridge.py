"""Manual Realtek microphone bridge for the local Cage Linux guest (Windows)."""
import argparse
import base64
import ctypes
import json
import os
from pathlib import Path
import queue
import shutil
import subprocess
import sys
import threading
import time
import uuid

HERE = Path(__file__).resolve().parent
STATE = HERE.parent / '.local' / 'microphone'
CLEANUP = (HERE / 'microphone-cleanup.sh').read_text(encoding='utf-8')
WATCHDOG = (HERE / 'microphone-watchdog.sh').read_text(encoding='utf-8')
FLAGS = getattr(subprocess, 'CREATE_NO_WINDOW', 0)


class AlreadyRunning(RuntimeError):
    pass


class StopRequested(Exception):
    pass


class InstanceLock:
    def __init__(self, path):
        self.path, self.file = path, None

    def __enter__(self):
        import msvcrt
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.file = self.path.open('a+b')
        if self.path.stat().st_size == 0:
            self.file.write(b'0')
            self.file.flush()
        self.file.seek(0)
        try:
            msvcrt.locking(self.file.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError as exc:
            self.file.close()
            raise AlreadyRunning('Микрофон уже включён. Используйте открытое окно или команду выключения.') from exc
        return self

    def __exit__(self, *args):
        import msvcrt
        self.file.seek(0)
        msvcrt.locking(self.file.fileno(), msvcrt.LK_UNLCK, 1)
        self.file.close()


class ChildJob:
    """Windows closes/kills the capture children even if the UI crashes."""
    def __init__(self):
        from ctypes import wintypes as w
        class Basic(ctypes.Structure):
            _fields_ = [('process_time', ctypes.c_int64), ('job_time', ctypes.c_int64),
                        ('flags', w.DWORD), ('min_ws', ctypes.c_size_t), ('max_ws', ctypes.c_size_t),
                        ('active', w.DWORD), ('affinity', ctypes.c_size_t),
                        ('priority', w.DWORD), ('scheduling', w.DWORD)]
        class IO(ctypes.Structure):
            _fields_ = [(name, ctypes.c_uint64) for name in ('r', 'w', 'o', 'rb', 'wb', 'ob')]
        class Extended(ctypes.Structure):
            _fields_ = [('basic', Basic), ('io', IO), ('process_mem', ctypes.c_size_t),
                        ('job_mem', ctypes.c_size_t), ('peak_process', ctypes.c_size_t),
                        ('peak_job', ctypes.c_size_t)]
        self.api = ctypes.WinDLL('kernel32', use_last_error=True)
        self.api.CreateJobObjectW.argtypes = [ctypes.c_void_p, w.LPCWSTR]
        self.api.CreateJobObjectW.restype = w.HANDLE
        self.api.SetInformationJobObject.argtypes = [w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD]
        self.api.AssignProcessToJobObject.argtypes = [w.HANDLE, w.HANDLE]
        self.api.CloseHandle.argtypes = [w.HANDLE]
        self.handle = self.api.CreateJobObjectW(None, None)
        if not self.handle:
            raise ctypes.WinError(ctypes.get_last_error())
        info = Extended()
        info.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not self.api.SetInformationJobObject(self.handle, 9, ctypes.byref(info), ctypes.sizeof(info)):
            self.close()
            raise ctypes.WinError(ctypes.get_last_error())

    def add(self, process):
        if not self.api.AssignProcessToJobObject(self.handle, int(process._handle)):
            raise ctypes.WinError(ctypes.get_last_error())

    def close(self):
        if self.handle:
            self.api.CloseHandle(self.handle)
            self.handle = None


def encoded_write(text, target):
    data = base64.b64encode(text.encode()).decode()
    return f'echo {data} | base64 -d | sudo tee {target} >/dev/null\n'


def heartbeat_script(owner):
    return ('set -eu\n'
            f'test "$(cat /run/cage-mic-bridge/owner)" = "{owner}"\n'
            'date +%s | sudo tee /run/cage-mic-bridge/lease.new >/dev/null\n'
            'sudo mv /run/cage-mic-bridge/lease.new /run/cage-mic-bridge/lease\n')


def setup_script(owner):
    setup = '''set -eu
test ! -e /run/cage-mic-bridge
test ! -e /run/systemd/system/cage-audio.service.d/90-mic-bridge.conf
test "$(grep -c '^ExecStart=' /etc/systemd/system/cage-audio.service)" = 1
grep -q -- '--file=/etc/claude-cage/audio.pa' /etc/systemd/system/cage-audio.service
sudo install -d -o root -g cage-audio -m 0750 /run/cage-mic-bridge
sudo install -d -o cage -g cage-audio -m 0750 /run/cage-mic-bridge/data
'''
    setup += encoded_write(owner + '\n', '/run/cage-mic-bridge/owner')
    setup += encoded_write(CLEANUP, '/run/cage-mic-bridge/cleanup.sh')
    setup += encoded_write(WATCHDOG, '/run/cage-mic-bridge/watchdog.sh')
    setup += heartbeat_script(owner)
    setup += '''sudo chmod 0700 /run/cage-mic-bridge/cleanup.sh /run/cage-mic-bridge/watchdog.sh
sudo systemd-run --collect --unit=cage-mic-bridge-watchdog --on-active=30s --on-unit-active=30s --timer-property=AccuracySec=1s /bin/sh /run/cage-mic-bridge/watchdog.sh
cat <<'PULSE' | sudo tee /run/cage-mic-bridge/audio.pa >/dev/null
.include /etc/claude-cage/audio.pa
load-module module-pipe-source source_name=cage_realtek file=/run/cage-mic-bridge/data/audio.fifo format=s16le rate=48000 channels=1 source_properties=device.description=Realtek_Bridge
set-default-source cage_realtek
PULSE
sudo install -d -m 0755 /run/systemd/system/cage-audio.service.d
( printf '[Service]\\nExecStart=\\n'; sed -n '/^ExecStart=/p' /etc/systemd/system/cage-audio.service | sed 's|--file=/etc/claude-cage/audio.pa|--file=/run/cage-mic-bridge/audio.pa|' ) | sudo tee /run/systemd/system/cage-audio.service.d/90-mic-bridge.conf >/dev/null
sudo systemctl daemon-reload
sudo systemctl restart cage-audio.service
i=0
until pactl --server=unix:/run/cage-audio/native get-default-source | grep -qx cage_realtek; do
  i=$((i+1)); test "$i" -lt 40; sleep .1
done
'''
    return setup


class Controller:
    def __init__(self, state=STATE, guest=None, notify=lambda value: None, cleanup_allowed=lambda: True):
        self.state, self.notify = state, notify
        self.owner = uuid.uuid4().hex
        self.children = []
        self.job = None
        self.cage = Path(os.environ.get('LOCALAPPDATA', '')) / 'Programs/Cage/resources/cage.exe'
        self.guest = guest or self.run_guest
        self.stop_event = threading.Event()
        self.children_lock = threading.RLock()
        self.cleanup_allowed = cleanup_allowed

    def request_stop(self):
        self.stop_event.set()
        with self.children_lock:
            if self.job is not None:
                self.job.close()

    def run_guest(self, script):
        data = base64.b64encode(script.encode()).decode()
        result = subprocess.run([str(self.cage), 'run', 'sh', '-lc',
                                 'echo ' + data + ' | base64 -d | sh'],
                                capture_output=True, timeout=45, creationflags=FLAGS)
        if result.returncode:
            detail = result.stderr.decode('utf-8', errors='replace')[-2000:]
            raise RuntimeError('Команда Cage не выполнена: ' + detail)
        return result

    def spawn(self, args, **kwargs):
        with self.children_lock:
            if self.stop_event.is_set():
                raise StopRequested()
            process = subprocess.Popen(args, creationflags=FLAGS, **kwargs)
            self.children.append(process)
            self.job.add(process)
            return process

    def stop_children(self):
        for process in self.children:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=3)
        self.children = []

    def preflight(self, ffmpeg):
        # Confirm that Realtek can open before restarting any guest audio service.
        process = self.spawn([ffmpeg, '-hide_banner', '-loglevel', 'error', '-nostdin',
                              '-f', 'dshow', '-i', 'audio=Микрофон (Realtek USB2.0 Audio)',
                              '-t', '0.1', '-f', 'null', '-'],
                             stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        _, error = process.communicate(timeout=8)
        if process in self.children:
            self.children.remove(process)
        if self.stop_event.is_set():
            raise StopRequested()
        if process.returncode:
            raise RuntimeError('Realtek недоступен: ' + error.decode('utf-8', errors='replace')[-1000:])

    def cleanup(self):
        if not self.cleanup_allowed():
            return  # VM stopped or unreachable: /run disappears, or watchdog retries.
        self.guest('set -eu\n'
                   f'if test "$(cat /run/cage-mic-bridge/owner 2>/dev/null)" = "{self.owner}"; then\n'
                   '  if test -f /run/cage-mic-bridge/cleanup.sh; then\n'
                   '    sudo sh /run/cage-mic-bridge/cleanup.sh\n'
                   '  else\n'
                   '    sudo rm -f /run/cage-mic-bridge/owner\n'
                   '    sudo rmdir /run/cage-mic-bridge/data /run/cage-mic-bridge\n'
                   '  fi\n'
                   'fi\n')

    def run(self):
        self.state.mkdir(parents=True, exist_ok=True)
        with InstanceLock(self.state / 'controller.lock'):
            stop_file = self.state / 'stop'
            stop_file.unlink(missing_ok=True)
            ffmpeg = shutil.which('ffmpeg') or r'C:\tools\ffmpeg\bin\ffmpeg.exe'
            if not self.cage.is_file() or not Path(ffmpeg).is_file():
                raise RuntimeError('Не найден Cage или FFmpeg. Сначала установите их и запустите среду Cage.')
            self.job = ChildJob()
            finished = threading.Event()

            def watch_stop():
                while not finished.wait(.1):
                    if stop_file.exists() or self.stop_event.is_set():
                        self.request_stop()
                        return

            monitor = threading.Thread(target=watch_stop, daemon=True)
            monitor.start()
            try:
                if self.stop_event.is_set():
                    raise StopRequested()
                self.notify('starting')
                self.preflight(ffmpeg)
                self.guest(setup_script(self.owner))
                if self.stop_event.is_set() or stop_file.exists():
                    raise StopRequested()
                with (self.state / 'capture.log').open('wb') as capture_log, (self.state / 'transfer.log').open('wb') as transfer_log:
                    self.spawn([str(self.cage), 'run', 'sh', '-lc',
                                'exec parec --device=cage_realtek --raw --format=s16le --rate=48000 --channels=1 > /dev/null'],
                               stdin=subprocess.DEVNULL, stdout=transfer_log, stderr=transfer_log)
                    capture = self.spawn([ffmpeg, '-hide_banner', '-loglevel', 'warning', '-nostdin',
                                          '-f', 'dshow', '-audio_buffer_size', '50',
                                          '-i', 'audio=Микрофон (Realtek USB2.0 Audio)',
                                          '-ac', '1', '-ar', '48000', '-f', 's16le', 'pipe:1'],
                                         stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=capture_log)
                    self.spawn([str(self.cage), 'run', 'sh', '-lc',
                                'exec cat > /run/cage-mic-bridge/data/audio.fifo'],
                               stdin=capture.stdout, stdout=transfer_log, stderr=transfer_log)
                    capture.stdout.close()
                    self.stop_event.wait(2)
                    next_heartbeat = 0
                    announced = False
                    while not self.stop_event.is_set() and not stop_file.exists():
                        if any(child.poll() is not None for child in self.children):
                            if self.stop_event.is_set() or stop_file.exists():
                                break
                            raise RuntimeError('Передача звука прервалась. Проверьте подключение Realtek и работающую среду Cage. Журналы: .local/microphone/')
                        if time.monotonic() >= next_heartbeat:
                            self.guest(heartbeat_script(self.owner))
                            next_heartbeat = time.monotonic() + 20
                        if not announced:
                            self.notify('running')
                            announced = True
                        self.stop_event.wait(.3)
            except StopRequested:
                pass
            finally:
                finished.set()
                monitor.join(timeout=2)
                self.notify('stopping')
                try:
                    self.stop_children()
                finally:
                    with self.children_lock:
                        self.job.close()
                    self.cleanup()
                self.notify('stopped')


class AutomaticBridge:
    def __init__(self, controller_factory, thread_factory=threading.Thread):
        self.factory, self.thread_factory = controller_factory, thread_factory
        self.controller = self.worker = None
        self.retry_at = 0

    def update(self, app_running, guest_ready):
        if self.worker is not None and self.worker.is_alive():
            if not app_running or not guest_ready:
                self.controller.request_stop()
            return
        if self.worker is not None:
            self.retry_at = time.monotonic() + 30
        self.controller = self.worker = None
        if not app_running or not guest_ready:
            self.retry_at = 0
        if app_running and guest_ready and time.monotonic() >= self.retry_at:
            self.controller = self.factory()
            self.worker = self.thread_factory(target=self.controller.run, daemon=False)
            self.worker.start()


def cage_is_running():
    """Match the desktop executable, excluding our own resources/cage.exe commands."""
    from ctypes import wintypes as w
    class Entry(ctypes.Structure):
        _fields_ = [('size', w.DWORD), ('usage', w.DWORD), ('pid', w.DWORD),
                    ('heap', ctypes.c_size_t), ('module', w.DWORD), ('threads', w.DWORD),
                    ('parent', w.DWORD), ('priority', w.LONG), ('flags', w.DWORD),
                    ('exe', w.WCHAR * 260)]
    api = ctypes.WinDLL('kernel32', use_last_error=True)
    api.CreateToolhelp32Snapshot.argtypes = [w.DWORD, w.DWORD]
    api.CreateToolhelp32Snapshot.restype = w.HANDLE
    api.Process32FirstW.argtypes = api.Process32NextW.argtypes = [w.HANDLE, ctypes.POINTER(Entry)]
    api.OpenProcess.argtypes = [w.DWORD, w.BOOL, w.DWORD]
    api.OpenProcess.restype = w.HANDLE
    api.QueryFullProcessImageNameW.argtypes = [w.HANDLE, w.DWORD, w.LPWSTR, ctypes.POINTER(w.DWORD)]
    api.CloseHandle.argtypes = [w.HANDLE]
    expected = str(Path(os.environ['LOCALAPPDATA']) / 'Programs/Cage/Cage.exe').casefold()
    snapshot = api.CreateToolhelp32Snapshot(2, 0)
    if snapshot == ctypes.c_void_p(-1).value:
        return False
    try:
        entry = Entry()
        entry.size = ctypes.sizeof(entry)
        valid = api.Process32FirstW(snapshot, ctypes.byref(entry))
        while valid:
            if entry.exe.casefold() == 'cage.exe':
                handle = api.OpenProcess(0x1000, False, entry.pid)
                if handle:
                    try:
                        path, size = ctypes.create_unicode_buffer(32768), w.DWORD(32768)
                        if api.QueryFullProcessImageNameW(handle, 0, path, ctypes.byref(size)) and path.value.casefold() == expected:
                            return True
                    finally:
                        api.CloseHandle(handle)
            valid = api.Process32NextW(snapshot, ctypes.byref(entry))
        return False
    finally:
        api.CloseHandle(snapshot)


def read_cage_status():
    cage = Path(os.environ['LOCALAPPDATA']) / 'Programs/Cage/resources/cage.exe'
    try:
        result = subprocess.run([str(cage), 'agent', 'call', 'status'],
                                capture_output=True, timeout=5, creationflags=FLAGS)
        return json.loads(result.stdout).get('data', {}) if result.returncode == 0 else {}
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return {}


def watch_cage():
    STATE.mkdir(parents=True, exist_ok=True)

    def report(status, error=None):
        # Store only our state, never the full Cage status (it includes private data).
        entry = {'status': status, 'pid': os.getpid(), 'updated': time.time()}
        if error:
            entry['error'] = str(error)
        temporary = STATE / 'automatic.new'
        temporary.write_text(json.dumps(entry, ensure_ascii=False), encoding='utf-8')
        temporary.replace(STATE / 'automatic.json')

    class BackgroundController(Controller):
        def run(self):
            try:
                super().run()
            except AlreadyRunning:
                report('already_running')
            except Exception as exc:
                report('error', exc)

    with InstanceLock(STATE / 'watcher.lock'):
        auto = AutomaticBridge(lambda: BackgroundController(
            notify=report, cleanup_allowed=lambda: bool(read_cage_status().get('vm_running'))))
        try:
            while True:
                app = cage_is_running()
                status = read_cage_status() if app else {}
                ready = bool(status.get('vm_running') and status.get('ready'))
                auto.update(app, ready)
                if auto.worker is None:
                    report('waiting_for_cage')
                time.sleep(5)
        finally:
            if auto.controller is not None:
                auto.controller.request_stop()
                auto.worker.join(timeout=50)


def show_window():
    import tkinter as tk
    from tkinter import messagebox
    root = tk.Tk()
    root.title('Микрофон Cage — Realtek')
    root.geometry('510x240')
    root.resizable(False, False)
    events = queue.Queue()
    controller = Controller(notify=events.put)
    status = tk.StringVar(value='Подключаю Realtek к Cage…')
    tk.Label(root, textvariable=status, font=('Segoe UI', 13), wraplength=470).pack(pady=(20, 10))
    tk.Label(root, text='Пока окно открыто, микрофон захватывает звук.\nЗапись на диск не сохраняется.\nЕсли Claude не видит микрофон — перезапустите только Claude.',
             font=('Segoe UI', 10), justify='center').pack()
    button = tk.Button(root, text='Выключить микрофон', command=controller.request_stop,
                       font=('Segoe UI', 11), width=26)
    button.pack(pady=15)
    root.protocol('WM_DELETE_WINDOW', controller.request_stop)

    def worker():
        try:
            controller.run()
        except Exception as exc:
            events.put(('error', str(exc)))
        finally:
            events.put('done')

    def poll():
        messages = {'starting': 'Подключаю Realtek к Cage…',
                    'running': '● Микрофон ВКЛЮЧЁН — Realtek',
                    'stopping': 'Отключаю микрофон, восстанавливаю звук…',
                    'stopped': 'Микрофон выключен'}
        while not events.empty():
            event = events.get_nowait()
            if isinstance(event, tuple):
                messagebox.showerror('Микрофон Cage', event[1], parent=root)
            elif event == 'done':
                root.destroy()
                return
            else:
                status.set(messages[event])
                if event == 'stopping':
                    button.configure(state='disabled')
        root.after(150, poll)

    threading.Thread(target=worker, daemon=False).start()
    root.after(150, poll)
    root.mainloop()


def main():
    for stream in (sys.stdout, sys.stderr):
        if stream is not None:
            stream.reconfigure(encoding='utf-8', errors='replace')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stop', action='store_true')
    parser.add_argument('--run', action='store_true', help='Run without a window (diagnostics)')
    parser.add_argument('--watch', action='store_true', help='Automatically connect while Cage and Linux are running')
    args = parser.parse_args()
    if args.stop:
        STATE.mkdir(parents=True, exist_ok=True)
        (STATE / 'stop').touch()
    elif args.watch:
        try:
            watch_cage()
        except AlreadyRunning:
            pass
    elif args.run:
        Controller(notify=lambda state: print(state, flush=True)).run()
    else:
        show_window()


if __name__ == '__main__':
    main()
