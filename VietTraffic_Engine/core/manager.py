import multiprocessing
import time

class ProcessManager:
    def __init__(self):
        self.manager = multiprocessing.Manager()
        self.shared_status = self.manager.dict()
        self.processes = {}  # {name: (process_obj, collector_obj)}

    def add_collector(self, collector_instance):
        name = collector_instance.name
        self.shared_status[name] = {
            "status": "Ready",
            "last_run": "Never",
            "total_mb": 0,
            "count": 0
        }
        self.processes[name] = {"instance": collector_instance, "process": None}

    def start_collector(self, name):
        if name in self.processes and self.processes[name]["process"] is None:
            collector = self.processes[name]["instance"]
            p = multiprocessing.Process(target=collector.run, args=(self.shared_status,))
            p.start()
            self.processes[name]["process"] = p
            print(f"[+] Đã khởi động tiến trình: {name}")

    def stop_collector(self, name):
        if name in self.processes and self.processes[name]["process"] is not None:
            self.processes[name]["process"].terminate()
            self.processes[name]["process"] = None
            # Cập nhật trạng thái
            status = self.shared_status[name]
            status["status"] = "Stopped"
            self.shared_status[name] = status
            print(f"[-] Đã dừng tiến trình: {name}")

    def get_all_status(self):
        return dict(self.shared_status)

    def stop_all(self):
        for name in list(self.processes.keys()):
            self.stop_collector(name)
