import platform
import psutil

class SystemObserver:
    def get_context(self):
        # Hardware speed assessment
        cpu_load = psutil.cpu_percent(interval=0.5)
        ram = psutil.virtual_memory().percent
        os_info = f"{platform.system()} {platform.release()}"
        speed = "Slow" if cpu_load > 80 else "Fast"
        
        return f"OS: {os_info}, HardwareStatus: {speed} (CPU:{cpu_load}%, RAM:{ram}%)"