# coding=utf-8
import copy
from book import Book, BookInfo, ImageBook
import numpy as np
import cv2
import requests
import qi
import logging
from datetime import datetime
import pprint
from tools import *
from perspective_warp import get_warped_image

logging.basicConfig(
    format='%(asctime)s %(message)s',
    datefmt='%H:%M:%S',
    filename="logs/"+datetime.now().strftime("%d-%m-%Y %H-%M-%S") + '.log',
    level=logging.DEBUG
)
logging.getLogger().addHandler(logging.StreamHandler())


class NAOLibrarian(object):
    def __init__(self, app, ocr_server_address, rec_server_address):
        super(NAOLibrarian, self).__init__()

        logging.info("Initializing NAO Librarian")

        self.box_step = 30.0 / 100.0
        self.foot_len = 3.0 / 100.0

        self.ocr_server_address = ocr_server_address

        # Get the services ALMemory, ALTextToSpeech.
        self.id = None
        app.start()
        session = app.session
        self.memory_service = session.service("ALMemory")
        self.tts = session.service("ALTextToSpeech")
        self.tts.setLanguage("English")
        self.tts.setVolume(0.2)
        self.motion = session.service("ALMotion")
        self.video_device = session.service("ALVideoDevice")
        self.tracker = session.service("ALTracker")
        self.posture = session.service("ALRobotPosture")
        self.leds = session.service("ALLeds")
        self.blink_flag = False

        # ALIMDetection
        self.rec_server = qi.Session()
        self.rec_server.connect(rec_server_address)
        self.im_detect = self.rec_server.service("ALIMDetection")

        session.service("ALNavigation")

        self.position_history = []  # type: list[tuple[float, float, float]]
        self.posture.goToPosture("Stand", 0.5)
        self.touch = self.memory_service.subscriber("TouchChanged")
        self.tts.say("Ready for work! Touch my head to start.")

        logging.info("Initialization finished")
        self.run()

    def run(self):
        self.wait_for_starting_touch()

    def wait_for_starting_touch(self):
        self.id = self.touch.signal.connect(self.on_starting_touch)
        logging.info("Waiting for starting touch")

    def on_starting_touch(self, value):

        logging.info("Touch detected")

        self.touch.signal.disconnect(self.id)

        for p in value:
            if p[1] and "Head/Touch" in p[0]:
                logging.info("Head touch detected, starting the script")
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

        logging.info("Running book scenario")

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

        logging.info("Playing decorations for boxes")
        if box_category is not None:
            self.box_found_decorations(book_info, box_category)
        else:
            self.box_not_found_decorations(book_info)

        self.go_to_position(*self.position_history[0])

    def blink(self):
        if self.blink_flag:
            self.leds.fadeRgb('FaceLeds', '#E5FFCC', 0.5)
        else:
            self.leds.fadeRgb('FaceLeds', '#7F00FF', 0.5)
        self.blink_flag = not self.blink_flag

    def look_for_book(self):
        # type: () -> ImageBook

        logging.info("Starting looking for books")

        img = self.take_photo(resolution="640*480", return_numpy=False)
        book = self.find_book(img)
        while book is None:

            logging.info("Book not found")

            for i in range(0, 2):  # lean 2x30 deg = 60 deg right
                # self.blink()
                logging.info("Moving 30 deg right")
                self.moveTo(0, 0, np.pi / 6)
                img = self.take_photo(resolution="640*480", return_numpy=False)
                book = self.find_book(img)
                if book:
                    return book

            logging.info("Book not found, resetting position")

            # reset position
            self.moveTo(0, 0, 2 / 6 * np.pi)

            for i in range(0, 2):
                # self.blink()
                logging.info("Moving 30 deg right")
                self.moveTo(0, 0, np.pi / 6)
                img = self.take_photo(resolution="640*480", return_numpy=False)
                book = self.find_book(img)
                if book:
                    return book

            logging.info("Book not found, moving again")
            self.moveTo(0, 0, -2 / 6 * np.pi)
            self.moveTo(0, 0.5, 0)
            book = self.find_book(img)

            logging.warn("Book still not found, redoing the cycle")
        return book

    def find_book(self, img, threshold=0.2):
        logging.info("Object detection requested")

        res = self.im_detect.detect(img, None)

        logging.info("Object detection finished")
        logging.debug("Object detection result: \n{}".format(pprint.pformat(res)))

        res = list(filter(lambda o: o[2] > threshold, res))
        res = list(filter(lambda o: o[0].lower() == "book", res))
        res.sort(key=lambda o: o[2], reverse=True)

        logging.debug("Filtered object detection result: \n{}".format(pprint.pformat(res)))
        if len(res) == 0:
            logging.info("No book found")

        filename = datetime.now().strftime("%d-%m-%Y %H-%M-%S")+".jpg"
        save_image(img, filename)
        logging.info("Image saved to {}".format(filename))

        return None if len(res) == 0 else ImageBook(img, res[3][1], res[3][3], res[3][0], res[3][2])

    def on_book_not_found(self):
        # type: () -> None
        self.tts.say("Book not found!")

    def book_found_decorations(self, book):
        # type: (Book) -> None
        self.tts.say("Book found!")
        self.tracker.pointAt("RArm", [book.image_book.x, book.image_book.y, 0], 1, 0.1)

    def go_to_book(self, book):
        # type: (Book) -> None
        logging.info("Going to book")
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

        logging.info("Moving with stops to book: {}".format(image_book))

        if stops is None:
            stops = int(distance_with_stops / min_step_distance)

        if stops != 0 and distance_with_stops / stops < min_step_distance:
            old_stops = stops
            stops = int(distance_with_stops / min_step_distance)
            logging.info("Too many stops ({}), reducing to {}".format(old_stops, stops))

        if stops == 0:
            self.move_to_book(book)
            return

        safe_point_mult = distance_with_stops / image_book.distance
        part_mult = 1.0 / stops
        stop_mult = safe_point_mult * part_mult

        logging.info("Moving to book: " + str(book) + ", stops left:" + str(stops))

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

        logging.debug("Ideal book: " + str(ideal_image_book))
        same_book = ideal_image_book.get_same_book(book_func())
        if same_book is None:
            logging.warn("Did not find the same book, stopping")
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
        logging.debug("Moving to: x={}, y={}, theta={}".format(x, y, theta))
        self.position_history.append(self.motion.getRobotPosition(True))
        self.motion.moveTo(x, y, theta)

    def change_posture_for_photo(self):
        # type: () -> None
        logging.info("Changing posture for photo")
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
        warped_image = get_warped_image(np_arr)
        result = warped_image if warped_image is not None else np_arr
        cv2.imwrite(file_path, result)
        logging.info("Book photo saved to {}".format(file_path))
        return file_path

    def take_photo(self, resolution="1280*960", return_numpy=False):

        resolutions = {
            "1280*960": 3,
            "640*480": 2,
            "320*240": 1
        }

        resolution = "320*240" if resolution not in resolutions else resolution

        color_space = 11  # BGR=13, RGB=11

        lower_camera = self.video_device.subscribeCamera("kBottomCamera", 1, resolutions[resolution], color_space, 30)
        image = self.video_device.getImageRemote(lower_camera)
        im = image[6]
        nparr = np.frombuffer(im, np.uint8)
        nparr = nparr.reshape(480, 640, 3)
        self.video_device.unsubscribe(lower_camera)
        return nparr if return_numpy else image

    def send_photo_to_server(self, photo_path):
        # type: (str) -> BookInfo or None

        logging.info("Sending photo to server")

        response = requests.post(self.ocr_server_address, files={"book": open(photo_path, "rb")})
        if response.status_code != 200:
            logging.error("Server returned status code: {}, text: {}".format(response.status_code, response.text))
            return None

        logging.debug("Server returned: \n{}".format(pprint.pformat(response.json())))

        return BookInfo.from_json(response.json())

    def on_book_info_not_found(self):
        # type: () -> None
        logging.info("Playing on book info not found")
        self.tts.say("I did not find the book info")

    def say_book_info(self, book_info):
        # type: (BookInfo) -> None
        logging.info("Playing book info")
        self.tts.say("The book is called: " + book_info.title)
        self.tts.say("The author is: " + book_info.author)

    def go_to_box_area(self):
        # type: () -> None
        logging.info("Going to box area")
        logging.debug("Position history: \n{}".format(pprint.pformat(self.position_history)))
        position_history_copy = copy.copy(self.position_history)
        for position in reversed(position_history_copy):
            self.go_to_position(*position, mirror_theta=True)

    def go_to_position(self, x, y, theta, mirror_theta=False):
        # type: (float, float, float, bool) -> None
        logging.debug("Going to position: x={}, y={}, theta={}, mirror_theta={}".format(x, y, theta, mirror_theta))
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

        logging.info("Checking if in front is the box for book: " + str(book_info))

        text = self.get_text_from_image(self.take_photo())
        logging.info("Text from image: " + text)
        if text is None or not text.startswith("NAOBox:"):
            logging.warn("Text is None or does not start with NAOBox:")
            self.tts.say("I did not find the box in the box area")
            return None

        if book_info.aligns_with_category(text):
            logging.info("Book aligns with category")
            return text[7:]
        else:
            logging.info("Book does not align with category")
            self.move_to_next_box()
            self.find_box(book_info)

    def move_to_next_box(self):
        # type: () -> None
        logging.info("Moving to next box")
        self.moveTo(0, self.box_step, 0)

    def get_text_from_image(self, image_path):
        # type: (str) -> ...
        logging.info("Requesting OCR for image {}".format(image_path))
        response = requests.post(self.ocr_server_address, files={"image": open(image_path, "rb")})
        if response.status_code != 200:
            logging.error("Server returned status code: {}, text: {}".format(response.status_code, response.text))
            return None
        logging.debug("Server returned: \n{}".format(pprint.pformat(response.json())))
        return response.json()["text"]

    def box_found_decorations(self, book_info, box_category):
        # type: (BookInfo, str) -> None
        self.tts.say("This is the right box to put this book in, it is called: " + box_category)

    def box_not_found_decorations(self, book_info):
        # type: (BookInfo) -> None
        self.tts.say("I did not find the right box to put this book in")
        self.tts.say("There are no boxes for categories like: " + ", ".join(book_info.categories))
