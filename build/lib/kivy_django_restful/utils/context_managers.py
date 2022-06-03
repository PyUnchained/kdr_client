class KDRBusyContext():
    def __init__(self, applet):
        self.applet = applet
        if not getattr(self.applet, 'busy_contexts', None):
            self.applet.busy_contexts = []
        self.applet.working = True

    def __enter__(self):
        self.applet.busy_contexts.append(self)
        return None

    def __exit__(self, type, value, traceback):
        self.applet.busy_contexts.remove(self)
        if self.applet.busy_contexts == []:
            self.applet.working = False