import ctypes

from config import BYTES_PER_GIB, JAVA_RAM_MIN_GB, JAVA_RAM_RATIO


def get_total_ram_gb():
    class MEMORYSTATUSEX(ctypes.Structure):
        _fields_ = [
            ("dwLength", ctypes.c_ulong),
            ("dwMemoryLoad", ctypes.c_ulong),
            ("ullTotalPhys", ctypes.c_ulonglong),
            ("ullAvailPhys", ctypes.c_ulonglong),
            ("ullTotalPageFile", ctypes.c_ulonglong),
            ("ullAvailPageFile", ctypes.c_ulonglong),
            ("ullTotalVirtual", ctypes.c_ulonglong),
            ("ullAvailVirtual", ctypes.c_ulonglong),
            ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
        ]

    memory_status = MEMORYSTATUSEX()
    memory_status.dwLength = ctypes.sizeof(MEMORYSTATUSEX)

    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory_status))

    # 🔥 IMPORTANT : division FLOAT + round
    return round(memory_status.ullTotalPhys / BYTES_PER_GIB)


def calculate_ram_plan(total: int, ratio: float = JAVA_RAM_RATIO) -> tuple[int, int, int]:
    """Return (minimum, recommended, maximum) for a physical RAM amount."""
    total = max(1, int(total))
    maximum = max(2, total - 2)
    minimum = min(JAVA_RAM_MIN_GB, maximum)
    recommended = int(total * max(0.1, min(0.9, float(ratio))))
    return minimum, max(minimum, min(maximum, recommended)), maximum


def get_ram_limits() -> tuple[int, int]:
    """Return usable slider bounds while always keeping 2 GiB for Windows."""
    minimum, _recommended, maximum = calculate_ram_plan(get_total_ram_gb())
    return minimum, maximum


def get_recommended_ram_gb(ratio: float = JAVA_RAM_RATIO):
    # int() inside calculate_ram_plan deliberately rounds down: 16 * .65 = 10.
    return calculate_ram_plan(get_total_ram_gb(), ratio)[1]


def build_java_args(ram_gb: int | None = None):
    minimum, maximum = get_ram_limits()
    ram_gb = get_recommended_ram_gb() if ram_gb is None else int(ram_gb)
    ram_gb = max(minimum, min(maximum, ram_gb))

    return (
        f"-Xmx{ram_gb}G "
        "-XX:+UnlockExperimentalVMOptions "
        "-XX:+UseG1GC "
        "-XX:G1NewSizePercent=20 "
        "-XX:G1ReservePercent=20 "
        "-XX:MaxGCPauseMillis=50 "
        "-XX:G1HeapRegionSize=32M"
    )
