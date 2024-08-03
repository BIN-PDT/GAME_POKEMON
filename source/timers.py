from pygame.time import get_ticks


class Timer:
    def __init__(self, duration, repeat=False, autostart=False, command=None):
        self.duration = duration
        self.start_time = 0
        self.repeat = repeat
        self.is_active = False
        self.command = command
        if autostart:
            self.activate()

    def activate(self):
        self.is_active = True
        self.start_time = get_ticks()

    def deactivate(self):
        self.is_active = False
        self.start_time = 0
        if self.repeat:
            self.activate()

    def update(self):
        if self.is_active:
            if get_ticks() - self.start_time >= self.duration:
                if self.command:
                    self.command()
                self.deactivate()
