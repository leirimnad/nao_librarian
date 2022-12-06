# coding=utf-8
import functools


class NAOLibrarian(object):
    def __init__(self, app):
        super(NAOLibrarian, self).__init__()

        # Get the services ALMemory, ALTextToSpeech.
        self.id = None
        app.start()
        session = app.session
        self.memory_service = session.service("ALMemory")
        self.tts = session.service("ALTextToSpeech")
        self.touch = self.memory_service.subscriber("TouchChanged")

    def run(self):
        self.wait_for_starting_touch()

    def wait_for_starting_touch(self):
        self.id = self.touch.signal.connect(self.on_starting_touch)

    def on_starting_touch(self, value):
        self.touch.signal.disconnect(self.id)

        for p in value:
            if p[1] and "Head/Touch" in p[0]:
                self.tts.say("Starting the script!")
                self.start_script()
                break

    def start_script(self):
        pass

