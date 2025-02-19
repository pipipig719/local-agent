from apscheduler.schedulers.background import BackgroundScheduler
import threading
import atexit


class Scheduler:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if not cls._instance:
                cls._instance = super().__new__(cls)
                cls._instance._init_scheduler()
            return cls._instance

    def _init_scheduler(self):
        self.scheduler = BackgroundScheduler(
            daemon=True,
        )
        self._job_lock = threading.RLock()
        atexit.register(self.shutdown)
        print("后台调度器初始化完成")

    def add_job(self, func, trigger, args):
        with self._job_lock:
            self.scheduler.add_job(
                func,
                trigger,
                misfire_grace_time=60,
                args=args
            )

    def start(self):
        with self._job_lock:
            if not self.scheduler.running:
                self.scheduler.start()
                print("调度器已启动")

    def shutdown(self):
        with self._job_lock:
            if self.scheduler.running:
                self.scheduler.shutdown(wait=False)
                print("调度器已关闭")
