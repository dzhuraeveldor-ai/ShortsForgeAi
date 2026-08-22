"""Hardware information utilities."""

import platform
import psutil
import os


def get_hardware_info() -> dict:
    """Get system hardware information."""
    try:
        cpu_count = psutil.cpu_count(logical=True) or 1
        mem = psutil.virtual_memory()
    except Exception:
        cpu_count = 1
        mem = None

    # GPU detection
    gpu_name = None
    gpu_vram_gb = 0

    try:
        import torch
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            gpu_vram_gb = round(
                torch.cuda.get_device_properties(0).total_memory / (1024 ** 3), 1
            )
    except Exception:
        pass

    # Try nvidia-smi as fallback
    if gpu_name is None:
        try:
            import subprocess
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.total",
                 "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                line = result.stdout.strip().split("\n")[0]
                parts = line.split(",")
                if len(parts) >= 2:
                    gpu_name = parts[0].strip()
                    try:
                        gpu_vram_gb = round(float(parts[1].strip()) / 1024, 1)
                    except ValueError:
                        pass
        except Exception:
            pass

    # Disk info
    try:
        disk = psutil.disk_usage("/")
        disk_total_gb = round(disk.total / (1024 ** 3), 1)
        disk_free_gb = round(disk.free / (1024 ** 3), 1)
    except Exception:
        disk_total_gb = 0
        disk_free_gb = 0

    return {
        "os": platform.system(),
        "os_version": platform.version(),
        "python_version": platform.python_version(),
        "cpu": platform.processor() or "Unknown",
        "cpu_cores_logical": cpu_count,
        "cpu_cores_physical": psutil.cpu_count(logical=False) or cpu_count,
        "ram_total_gb": round(mem.total / (1024 ** 3), 1) if mem else 0,
        "ram_available_gb": round(mem.available / (1024 ** 3), 1) if mem else 0,
        "gpu": gpu_name,
        "gpu_vram_gb": gpu_vram_gb,
        "disk_total_gb": disk_total_gb,
        "disk_free_gb": disk_free_gb
    }
