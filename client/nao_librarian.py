# coding=utf-8
import copy
from book import Book, BookInfo


class NAOLibrarian(object):
    def __init__(self, app):
        super(NAOLibrarian, self).__init__()
        self.foot_len = 3.0 / 100.0

        # Get the services ALMemory, ALTextToSpeech.
        self.id = None
        app.start()
        session = app.session
        self.memory_service = session.service("ALMemory")
        self.tts = session.service("ALTextToSpeech")
        self.motion = session.service("ALMotion")
        session.service("ALNavigation")
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
        # type: (NAOLibrarian) -> None

        book = self.look_for_book()
        if book is None:
            self.on_book_not_found()
            return

        self.book_found_decorations(book)

        self.run_book_scenario(book)

    def run_book_scenario(self, book):
        # type: (NAOLibrarian, Book) -> None

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
        # type: (NAOLibrarian) -> None
        pass

    def book_found_decorations(self, book):
        # type: (NAOLibrarian, Book) -> None
        pass

    def go_to_book(self, book):
        # type: (NAOLibrarian, Book) -> None
        self.move_with_stops(book, self.look_for_book)

    def move_to_book(self, book):
        # type: (NAOLibrarian, Book) -> None

        print("Moving to book: " + str(book))

        self.motion.moveTo(
            book.image_book.vertical_distance / 100 - self.foot_len,
            (-1) * book.image_book.horizontal_distance / 100 - self.foot_len,
            -1 * book.image_book.angle
        )

    def move_with_stops(self, book, book_func, stops=None, safe_distance=50, min_step_distance=30):
        # type: (NAOLibrarian, Book, callable, int, int, int) -> None
        image_book = book.image_book
        distance_with_stops = max(0, book.distance - safe_distance)

        if stops is None:
            stops = int(distance_with_stops / min_step_distance)

        if stops != 0 and distance_with_stops / stops < min_step_distance:
            stops = int(distance_with_stops / min_step_distance)
            print("Too many stops, reducing to: " + str(stops))

        if stops == 0:
            self.move_to_book(book)
            return

        safe_point_mult = distance_with_stops / image_book.distance
        part_mult = 1.0 / stops
        stop_mult = safe_point_mult * part_mult

        print("Moving to book: " + str(book) + ", stops left:" + str(stops))

        self.motion.moveTo(
            (image_book.vertical_distance / 100 - self.foot_len) * stop_mult,
            ((-1) * image_book.horizontal_distance / 100 - self.foot_len) * stop_mult,
            (-1 * image_book.angle) * stop_mult
        )

        if stops <= 0:
            return

        ideal_image_book = copy.copy(image_book)
        ideal_image_book.distance = image_book.distance * (1 - stop_mult)
        ideal_image_book.vertical_distance = image_book.vertical_distance * (1 - stop_mult)
        ideal_image_book.horizontal_distance = image_book.horizontal_distance * (1 - stop_mult)

        same_book = ideal_image_book.get_same_book(book_func())
        if same_book is None:
            print("Did not find the same book, stopping")
            return

        return self.move_with_stops(
            book=same_book,
            book_func=book_func,
            stops=stops - 1,
            safe_distance=safe_distance,
            min_step_distance=min_step_distance
        )

    def take_book_photo(self, book):
        # type: (NAOLibrarian, Book) -> str
        pass

    def send_photo_to_server(self, photo_path):
        # type: (NAOLibrarian, str) -> BookInfo
        pass

    def on_book_info_not_found(self):
        # type: (NAOLibrarian) -> None
        pass

    def say_book_info(self, book_info):
        # type: (NAOLibrarian, BookInfo) -> None
        pass

    def go_to_box_area(self):
        # type: (NAOLibrarian) -> None
        pass

    def go_to_box(self, book_info):
        # type: (NAOLibrarian, BookInfo) -> None
        pass

    def box_found_decorations(self, book_info):
        # type: (NAOLibrarian, BookInfo) -> None
        pass
