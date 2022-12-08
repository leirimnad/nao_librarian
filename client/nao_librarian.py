# coding=utf-8
import copy
from book import Book, BookInfo
import numpy as np
import cv2
import requests


class NAOLibrarian(object):
    def __init__(self, app, ocr_server_address):
        super(NAOLibrarian, self).__init__()
        self.box_step = 30.0 / 100.0
        self.foot_len = 3.0 / 100.0

        self.ocr_server_address = ocr_server_address

        # Get the services ALMemory, ALTextToSpeech.
        self.id = None
        app.start()
        session = app.session
        self.memory_service = session.service("ALMemory")
        self.tts = session.service("ALTextToSpeech")
        self.motion = session.service("ALMotion")
        self.video_device = session.service("ALVideoDevice")
        self.tracker = session.service("ALTracker")
        self.posture = session.service("ALRobotPosture")
        session.service("ALNavigation")

        self.position_history = []  # type: list[tuple[float, float, float]]
        self.posture.goToPosture("Stand", 0.5)
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
        # type: () -> None

        book = self.look_for_book()
        if book is None:
            self.on_book_not_found()
            return

        self.book_found_decorations(book)

        self.run_book_scenario(book)

    def run_book_scenario(self, book):
        # type: (Book) -> None

        self.go_to_book(book)
        photo_path = self.take_book_photo(book)

        # TODO: async call
        book_info = self.send_photo_to_server(photo_path)

        if book_info is None:
            self.on_book_info_not_found()
            return

        self.say_book_info(book_info)

        self.go_to_box_area()

        box_category = self.find_box(book_info)

        if box_category is not None:
            self.box_found_decorations(book_info, box_category)
        else:
            self.box_not_found_decorations(book_info)

        self.go_to_position(*self.position_history[0])

    def look_for_book(self):
        # type: () -> Book
        pass

    def on_book_not_found(self):
        # type: () -> None
        self.tts.say("Book not found!")

    def book_found_decorations(self, book):
        # type: (Book) -> None
        self.tts.say("Book found!")
        self.tracker.pointAt("RArm", [book.image_book.x, book.image_book.y, 0], 1, 0.1)

    def go_to_book(self, book):
        # type: (Book) -> None
        self.move_with_stops(book, self.look_for_book)
        self.change_posture_for_photo()

    def move_to_book(self, book):
        # type: (NAOLibrarian, Book) -> None

        print("Moving to book: " + str(book))

        self.moveTo(
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

        self.moveTo(
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

    def moveTo(self, x, y, theta):
        # type: (float, float, float) -> None
        self.position_history.append(self.motion.getRobotPosition(True))
        self.motion.moveTo(x, y, theta)

    def change_posture_for_photo(self):
        # type: () -> None
        self.motion.setStiffnesses("Head", 1.0)
        self.motion.setAngles("HeadPitch", 0.0, 0.1)
        self.motion.setAngles("HeadYaw", 0.0, 0.1)

    def take_book_photo(self, book):
        # type: (Book) -> str
        file_path = "./run/cover.png"

        rgb_image_ = self.take_photo()
        rgb_image = rgb_image_[6]
        np_arr = np.fromstring(rgb_image, np.uint8)
        np_arr = np_arr.reshape(960, 1280, 3)
        cv2.imwrite(file_path, np_arr)
        return file_path

    def take_photo(self):
        resolutions = {
            "1280*960": 3,
            "640*480": 2,
            "320*240": 1
        }
        color_space = 11  # BGR=13, RGB=11

        lower_camera = self.video_device.subscribeCamera("kBottomCamera", 1, resolutions["1280*960"], color_space,
                                                         fps=30)
        image = self.video_device.getImageRemote(lower_camera)
        self.video_device.unsubscribe(lower_camera)
        return image

    def send_photo_to_server(self, photo_path):
        # type: (str) -> BookInfo or None

        response = requests.post(self.ocr_server_address, files={"book": open(photo_path, "rb")})
        if response.status_code != 200:
            return None

        return BookInfo.from_json(response.json())

    def on_book_info_not_found(self):
        # type: () -> None
        self.tts.say("I did not find the book info")

    def say_book_info(self, book_info):
        # type: (BookInfo) -> None
        self.tts.say("The book is called: " + book_info.title)
        self.tts.say("The author is: " + book_info.author)

    def go_to_box_area(self):
        # type: () -> None
        position_history_copy = copy.copy(self.position_history)
        for position in reversed(position_history_copy):
            self.go_to_position(*position, mirror_theta=True)

    def go_to_position(self, x, y, theta, mirror_theta=False):
        # type: (float, float, float, bool) -> None
        current_position = self.motion.getRobotPosition(True)
        if mirror_theta:
            theta = theta + 3.1415 if theta <= 0 else theta - 3.1415
        self.moveTo(
            x - current_position[0],
            y - current_position[1],
            theta - current_position[2]
        )

    def find_box(self, book_info):
        # type: (BookInfo) -> str or None
        text = self.get_text_from_image(self.take_photo())
        if text is None or not text.startswith("NAOBox:"):
            self.tts.say("I did not find the box in the box area")
            return None

        if book_info.aligns_with_category(text):
            return text[7:]
        else:
            self.move_to_next_box()
            self.find_box(book_info)

    def move_to_next_box(self):
        # type: () -> None
        self.moveTo(0, self.box_step, 0)

    def get_text_from_image(self, image_path):
        # type: (str) -> ...
        response = requests.post(self.ocr_server_address, files={"image": open(image_path, "rb")})
        if response.status_code != 200:
            return None
        return response.json()["text"]

    def box_found_decorations(self, book_info, box_category):
        # type: (BookInfo, str) -> None
        self.tts.say("This is the right box to put this book in, it is called: " + box_category)

    def box_not_found_decorations(self, book_info):
        # type: (BookInfo) -> None
        self.tts.say("I did not find the right box to put this book in")
        self.tts.say("There are no boxes for categories like: " + ", ".join(book_info.categories))
