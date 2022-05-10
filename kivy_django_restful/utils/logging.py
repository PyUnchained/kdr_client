from functools import partial
import io, time
from pickle_storage.utils.logging import write_to_log as original_write_to_log

write_to_log = partial(original_write_to_log, log_tag='Kivy Django Restful')

class TerminalNotificationStream(io.StringIO):
    __doc__ = " Redirects stdout/stderr output and makes it visible to the user\n    through the applet's notification system. "

    def __init__(self, applet, *args, timeout=10, **kwargs):
        self.applet = applet
        self.timeout = timeout
        (super().__init__)(*args, **kwargs)

    def write(self, s):
        self.applet.notification_manager.debug_message(s,
            timeout=self.timeout)

class TimedContext():

    def __enter__(self):
        """Start a new timer as a context manager"""
        self.start()
        return self

    def __exit__(self, *exc_info):
        """Stop the context manager timer"""
        self.stop()

    def __init__(self, name = None):
        if name:
            self.name = f' ({name})'
        else:
            self.name = ''
        self._start_time = None

    def start(self):
        """Start a new timer"""
        self._start_time = time.perf_counter()


    def stop(self):
        """Stop the timer, and report the elapsed time"""
        elapsed_time = time.perf_counter() - self._start_time
        self._start_time = None
        write_to_log(f"Elapsed time{self.name}: {elapsed_time} seconds")

def log_async_errors(f):
    def wrapped_f(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except:
            write_to_log(f"Exception occured in {f}", level='error')
    return wrapped_f