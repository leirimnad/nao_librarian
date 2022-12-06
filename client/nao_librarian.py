# coding=utf-8
import functools
from book import Book, BookInfo


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
        book = self.look_for_book()
        if book is None:
            self.on_book_not_found()
            return

        self.book_found_decorations(book)

        self.run_book_scenario(book)

    def run_book_scenario(self, book):
        self.go_to_book(book)
        photo_path = self.take_book_photo(book)

        # TODO: async call
        book_info = self.send_photo_to_server(photo_path)

        if book_info is None:
            self.on_book_info_not_found()
            return

        self.say_book_info(book_info)

        self.go_to_box_area()

        self.go_to_box(book_info)

        self.box_found_decorations(book_info)

    def look_for_book(self):
        # type: (NAOLibrarian) -> Book
        pass

    def on_book_not_found(self):
        pass

    def book_found_decorations(self, book):
        pass

    def go_to_book(self, book):
        pass

    def take_book_photo(self, book):
        # type: (NAOLibrarian, Book) -> str
        pass

    def send_photo_to_server(self, photo_path):
        # type: (NAOLibrarian, str) -> BookInfo
        pass

    def on_book_info_not_found(self):
        pass

    def say_book_info(self, book_info):
        pass

    def go_to_box_area(self):
        pass

    def go_to_box(self, book_info):
        pass

    def box_found_decorations(self, book_info):
        pass
