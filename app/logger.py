log_queue = None

def progress(value: int):
    if log_queue:
        log_queue.put(("progress", value))


def stage(key: str, message: str):
    if log_queue:
        log_queue.put(("stage", key, message))


def stage_done(key: str, message: str):
    if log_queue:
        log_queue.put(("stage_done", key, message))


def stage_skipped(key: str, message: str):
    if log_queue:
        log_queue.put(("stage_skipped", key, message))


def download(name: str, received: int, total: int | None, speed: float):
    if log_queue:
        log_queue.put(("download", name, received, total, speed))


def total_size(value: int):
    if log_queue:
        log_queue.put(("size_total", value))

def _send(msg: str, tag: str = "default"):
    if log_queue:
        log_queue.put(("log", msg, tag))
    else:
        print(msg)


def info(message: str) -> None:
    _send(f"ℹ️  {message}", "cyan")


def success(message: str) -> None:
    _send(f"✅ {message}", "green")


def error(message: str) -> None:
    _send(f"❌ {message}", "red")


def step(message: str) -> None:
    width = 80
    text = f" {message} "
    line = text.center(width, "─")

    _send(line, "magenta")
def fabric(message: str) -> None:
    _send(f"[⛩️] {message}", "yellow")


def neoforge(message: str) -> None:
    _send(f"[NEOFORGE] {message}", "yellow")


def mods(message: str) -> None:
    _send(f"[🧬] {message}", "yellow")


def uptodate(message: str) -> None:
    _send(f"  • 🎐 {message}", "green")


def outdated(message: str) -> None:
    _send(f"  • 💤 {message}", "magenta")


def missing(message: str) -> None:
    _send(f"  • 🏮 {message}", "red")


def extra(message: str) -> None:
    _send(f"  • 🔅 {message}", "cyan")


def txtp(message: str) -> None:
    _send(f"[🗻] {message}", "yellow")


def shader(message: str) -> None:
    _send(f"[🌌] {message}", "yellow")
