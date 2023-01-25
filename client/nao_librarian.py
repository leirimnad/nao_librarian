# coding=utf-8
from __future__ import division, print_function, unicode_literals
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
from random import shuffle
from time import sleep


class NAOLibrarian(object):
    """Main class for the Librarian application"""
    def __init__(self, app, ocr_server_address, rec_server_address):
        super(NAOLibrarian, self).__init__()

        logging.info("Initializing NAO Librarian")

        self.box_step = 30.0 / 100.0
        self.foot_len = 8.0 / 100.0

        self.ocr_server_address = ocr_server_address

        # Get the services ALMemory, ALTextToSpeech.
        self.id = None
        app.start()
        session = app.session
        self.memory_service = session.service("ALMemory")
        self.tts = session.service("ALTextToSpeech")
        #self.tts.setLanguage("English")
        self.tts.setLanguage("Czech")
        self.tts.setVolume(0.2)
        self.motion = session.service("ALMotion")
        self.video_device = session.service("ALVideoDevice")
        self.tracker = session.service("ALTracker")
        self.posture = session.service("ALRobotPosture")
        self.leds = session.service("ALLeds")
        self.visual_compass = session.service("ALVisualCompass")
        self.visual_compass.setCurrentImageAsReference()
        self.blink_flag = False
        session.service("ALNavigation")
        self.rec_server_address = rec_server_address
        self.position_history = []  # list[tuple[float, float, float]]
        self.posture.goToPosture("Stand", 0.2)
        self.touch = self.memory_service.subscriber("TouchChanged")
        self.ocr_request = None
        self.mock_recognition = (rec_server_address == "")
        self.book_threshold = 0.017

        logging.info("Initialization finished")
        self.tts.say("Jdeme na to, dotkni se mojí hlavy.")


        self.run()



    def run(self):
        self.wait_for_starting_touch()

    def wait_for_starting_touch(self):
        """Will run the on_starting_touch method when the head is touched"""
        self.id = self.touch.signal.connect(self.on_starting_touch)
        logging.info("Waiting for starting touch")

    def on_starting_touch(self, value):

        logging.info("Touch detected")

        for p in value:
            if p[1] and "Head/Touch" in p[0]:
                self.touch.signal.disconnect(self.id)
                logging.info("Head touch detected, starting the script")
                logging.info("Starting position: {}".format(self.motion.getRobotPosition(True)))
                self.tts.say("Spouštím skript !")
                self.start_script()
                break

    def start_script(self):
        # type: () -> None

        try:
            image_book = self.look_for_book()
            if image_book is None:
                self.on_book_not_found()
                return

            book = Book(image_book)

            self.book_found_decorations(book)

            self.run_book_scenario(book)
        except Exception, e:
            logging.error("Error: " + str(e))
            raise

    def run_book_scenario(self, book):
        # type: (Book) -> None

        logging.info("Running book scenario")

        self.go_to_book(book)
        photo_path = self.take_book_photo()

        book_info = self.send_photo_to_server(photo_path)

        if book_info is None:
            self.on_book_info_not_found()
            self.go_to_position(*self.position_history[0])
            self.wait_for_starting_touch()
            self.tts.say("Pokud mám hledat dál, dotkni se mojí hlavy.")
            return

        self.say_book_info(book_info)

        self.moveTo(-0.2, 0, 0)
        self.go_to_box_area()

        box_category = self.find_box(book_info)

        logging.info("Playing decorations for boxes")
        if box_category is not None:
            self.box_found_decorations(book_info, box_category)
        else:
            self.box_not_found_decorations(book_info)

        self.go_to_position(*self.position_history[0])
        self.tts.say("Hotovo ! Pokud mám hledat dál, dotkni se mojí hlavy.")
        self.wait_for_starting_touch()

    def blink(self):
        if self.blink_flag:
            self.leds.fadeRgb('FaceLeds', '#E5FFCC', 0.5)
        else:
            self.leds.fadeRgb('FaceLeds', '#7F00FF', 0.5)
        self.blink_flag = not self.blink_flag

    def look_for_book(self):
        # type: () -> ImageBook
        """
        Scans the area around the robot and tries to find a book
        :return: ImageBook
        """

        logging.info("Starting looking for books")

        resolution = "1280*960"

        img = self.take_photo(resolution=resolution, return_numpy=False)

        book = self.find_book_mock(img) if self.mock_recognition else self.find_book(img)
        while book in [None, -1, 1]:

            logging.info("Book search result: {}".format(book))

            angle = np.pi / 6
            if book == -1:
                angle = np.pi / 12
                self.tts.say("Je kniha vlevo ?")
            elif book == 1:
                angle = -np.pi / 12
                self.tts.say("Je kniha vpravo ?")

            for i in range(0, 2):
                # self.blink()
                logging.info("Moving {} deg left".format(round(angle*180/np.pi)))
                self.moveTo(0, 0, angle)
                img = self.take_photo(resolution=resolution, return_numpy=False)
                book = self.find_book(img)
                if book not in [None, -1, 1]:
                    return book

            logging.info("Book not found, resetting position")

            # reset position
            self.moveTo(0, 0, -angle*2)

            logging.info("Book search result was: {}".format(book))

            angle = np.pi / 6
            if book == -1:
                angle = np.pi / 12
                self.tts.say("Je kniha vlevo ?")
            elif book == 1:
                angle = -np.pi / 12
                self.tts.say("Je kniha vpravo ?")


            for i in range(0, 2):
                # self.blink()
                logging.info("Moving {} deg left".format(round(angle*180/np.pi)))
                self.moveTo(0, 0, angle)
                img = self.take_photo(resolution=resolution, return_numpy=False)
                book = self.find_book(img)
                if book not in [None, -1, 1]:
                    return book

            logging.info("Book not found, moving again")
            self.moveTo(0, 0, -angle*2)
            self.moveTo(0, 0.5, 0)
            book = self.find_book(img)

            logging.warn("Book still not found, redoing the cycle")

        if book not in [None, -1, 1]:
            logging.info("Book found: " + str(book))
        return book

    def find_book_mock(self, img, threshold=0.2):
        logging.info("MOCK object detection used")
        filename = "./logs/"+datetime.now().strftime("%d-%m-%Y %H-%M-%S")+".jpg"
        save_image(img, filename)
        logging.info("Image saved to {}".format(filename))
        img_width = img[0]
        img_height = img[1]
        return ImageBook(nparr_from_image(img), int(img_width*0.4), int(img_width*0.6), int(img_height*0.7), int(img_height*0.8))

    def find_book(self, img, threshold=None):
        """
        Tries to find a book in the image
        :param img: image to search in
        :param threshold: threshold for the detection
        :return: ImageBook if found, None otherwise, -1 if book is slightly visible on the left, 1 on the right
        """
        if threshold is None:
            threshold = self.book_threshold
        logging.info("Object detection requested with threshold {}".format(threshold))

        # ALIMDetection
        self.rec_server = qi.Session()
        self.rec_server.connect(self.rec_server_address)
        self.im_detect = self.rec_server.service("ALIMDetection")

        res = self.im_detect.detect(img, None)

        logging.info("Object detection finished")
        logging.debug("Object detection result: \n{}".format(pprint.pformat(res)))

        res = list(filter(lambda o: o[2] > threshold, res))
        res = list(filter(lambda o: o[0].lower() == "book", res))
        res.sort(key=lambda o: o[2], reverse=True)

        filename = "./logs/"+datetime.now().strftime("%d-%m-%Y %H-%M-%S")+".jpg"
        save_image(img, filename)
        logging.info("Image saved to {}".format(filename))

        logging.debug("Filtered object detection result: \n{}".format(pprint.pformat(res)))
        if len(res) == 0:
            logging.info("No book found")
            return None

        res = res[0]

        if int(res[3][1]) < 20:
            logging.info("Book is on the left side, returning -1")
            return -1

        if int(res[3][3]) > img[0] - 20:
            logging.info("Book is on the right side, returning 1")
            return 1

        return ImageBook(nparr_from_image(img), res[3][1], res[3][3], res[3][0], res[3][2])

    def on_book_not_found(self):
        # type: () -> None
        self.tts.say("Knihu jsem nenašel !")

    def book_found_decorations(self, book):
        # type: (Book) -> None
        x = round(book.image_book.vertical_distance/100, 4)
        y = round(book.image_book.horizontal_distance/100, 4)
        logging.info("Book in absolute position: x={} y={}".format(x, y))
#        logging.info("Robot position: {}".format(self.motion.getRobotPosition(True)))
#        x, y, _ = self.get_position_relative_to_robot(x, y, 0)
#        logging.info("Book in relative position: x={} y={}".format(x, y))
        point_to = [x, y, 0.08]
        point_arm = "RArm" if y >= 0 else "LArm"
        logging.debug("Pointing {} to {}".format(point_arm, point_to))
        self.tracker.pointAt(point_arm, point_to, 2, 0.1)
        self.tts.say("Kniha nalezena !")

    def go_to_book(self, book):
        # type: (Book) -> None
        logging.info("Going to book")
        self.move_with_stops(book.image_book, lambda: [self.look_for_book()])
        self.change_posture_for_photo()

    def move_to_book(self, image_book):
        # type: (NAOLibrarian, ImageBook) -> None

        logging.info("Moving to book: " + str(image_book))

        vertical_part = abs(image_book.vertical_distance)/(abs(image_book.vertical_distance) + abs(image_book.horizontal_distance))
        horizontal_part = abs(image_book.horizontal_distance)/(abs(image_book.vertical_distance) + abs(image_book.horizontal_distance))

        self.moveTo(
            image_book.vertical_distance / 100 - self.foot_len * vertical_part,
            (-1) * image_book.horizontal_distance / 100 - self.foot_len * horizontal_part,
            -image_book.rotation
        )

    def move_with_stops(self, image_book, book_func, stops=None, safe_distance=50, min_step_distance=30):
        # type: (NAOLibrarian, ImageBook, callable, int, int, int) -> None
        """
        Moves to the book with several stops to correct the position
        :param image_book: ImageBook to move to
        :param book_func: function to call to get the ImageBooks list on the stop
        :param stops: preferred number of stops
        :param safe_distance: minimum distance to stop before the book
        :param min_step_distance: minimum distance to move before the next stop
        """
        distance_with_stops = max(0, image_book.distance - safe_distance)

        logging.info("Moving with stops to book: {}".format(image_book))

        if stops is None:
            stops = int(distance_with_stops / min_step_distance)

        if stops != 0 and distance_with_stops / stops < min_step_distance:
            old_stops = stops
            stops = int(distance_with_stops / min_step_distance)
            logging.info("Too many stops ({}), reducing to {}".format(old_stops, stops))

        if stops == 0:
            self.move_to_book(image_book)
            return

        safe_point_mult = distance_with_stops / image_book.distance
        part_mult = 1.0 / stops
        stop_mult = safe_point_mult * part_mult

        logging.info("Moving to book: " + str(image_book) + ", stops left:" + str(stops))

        self.moveTo(
            (image_book.vertical_distance / 100) * stop_mult,
            ((-1) * image_book.horizontal_distance / 100) * stop_mult,
            (-1 * image_book.rotation) * stop_mult
        )

        if stops <= 0:
            return

        ideal_image_book = copy.copy(image_book)  # type: ImageBook
        ideal_image_book.distance = image_book.distance * (1 - stop_mult)
        ideal_image_book.vertical_distance = image_book.vertical_distance * (1 - stop_mult)
        ideal_image_book.horizontal_distance = image_book.horizontal_distance * (1 - stop_mult)

        logging.debug("Ideal book: " + str(ideal_image_book))
        same_book = ideal_image_book.get_same_book(book_func())
        if same_book is None:
            logging.warn("Did not find the same book, stopping")
            return

        return self.move_with_stops(
            image_book=same_book,
            book_func=book_func,
            stops=stops - 1,
            safe_distance=safe_distance,
            min_step_distance=min_step_distance
        )

    def reset_theta(self, max_tries=4):
        """Turns the robot to reset the theta angle to 0"""
        logging.debug("Resetting theta")
        x, y, theta = self.motion.getRobotPosition(True)
        self.moveTo(0, 0, -theta)
        x, y, theta = self.motion.getRobotPosition(True)
        tries = 0
        while abs(theta) > 0.05 and tries < max_tries:
            logging.debug("Not enough")
            self.moveTo(0, 0, -theta)
            x, y, theta = self.motion.getRobotPosition(True)
            tries += 1
        logging.debug("Theta reset finished")

    def moveTo(self, x, y, theta):
        """Moves the robot to the given position relative to the robot's, saves the previous position to the memory"""
        # type: (float, float, float) -> None
        x, y, theta = round(x, 4), round(y, 4), round(theta, 4)
        logging.debug("Moving relative: x={}, y={}, theta={}".format(x, y, theta))
        self.position_history.append(self.motion.getRobotPosition(True))
        self.motion.moveTo(x, y, theta)

    def get_position_relative_to_robot(self, x, y, theta):
        """Returns the position relative to the robot's position"""
        cx, cy, ct = self.motion.getRobotPosition(True)
        th = ct+theta
        pi = 3.14159
        if th > pi:
            th -= 2*pi
        elif th < -pi:
            th += 2*pi
        return cx+x, cy+y, th

    def change_posture_for_photo(self):
        # type: () -> None
        logging.info("Changing posture for photo")
        self.posture.goToPosture("Crouch", 1)
        self.motion.setStiffnesses("Head", 1.0)
        self.motion.setAngles("HeadPitch", 0.4, 0.1)
        self.motion.setAngles("HeadYaw", 0.0, 0.1)
        sleep(0.5)

    def take_book_photo(self):
        # type: () -> str
        """Takes a photo of the book, tries to warp it, and returns the path to the photo"""
        file_path = "./run/cover.png"

        logging.info("Taking book photo")
        np_arr = self.take_photo(return_numpy=True)

        log_path_cover = "./logs/"+datetime.now().strftime("%d-%m-%Y %H-%M-%S")+"-cover.jpg"
        cv2.imwrite(log_path_cover, np_arr)
        logging.info("Book log photo saved to {}".format(log_path_cover))


        logging.info("Trying to warp image")
        warped_image = get_warped_image(np_arr)
        logging.info("Warp {}succesfull".format("un" if warped_image is None else ""))

        if warped_image is not None:
            log_path_warped = "./logs/"+datetime.now().strftime("%d-%m-%Y %H-%M-%S")+"-warped.jpg"
            cv2.imwrite(log_path_warped, warped_image)
            logging.info("Warped book photo saved to {}".format(log_path_warped))
            cv2.imwrite(file_path, warped_image)
            logging.info("Run book photo saved WARPED to {}".format(file_path))
        else:
            cv2.imwrite(file_path, np_arr)
            logging.info("Run book photo saved UNWARPED to {}".format(file_path))

        sleep(0.3)
        self.motion.setAngles("HeadPitch", 0, 0.1)

        return file_path

    def take_photo(self, resolution="1280*960", return_numpy=False, save_to=None):

        resolutions = {
            "1280*960": (3,1280,960),
            "640*480": (2,640,480),
            "320*240": (1,320,240)
        }

        resolution = (1,320,240) if resolution not in resolutions else resolution

        color_space = 13 # BGR=13, RGB=11

        lower_camera = self.video_device.subscribeCamera("kBottomCamera", 1, resolutions[resolution][0], color_space, 30)
        image = self.video_device.getImageRemote(lower_camera)
        self.video_device.unsubscribe(lower_camera)
        if save_to is not None:
            cv2.imwrite(save_to, nparr_from_image(image))
            logging.info("Photo saved to {}".format(save_to))
            return save_to
        return nparr_from_image(image) if return_numpy else image

    def send_photo_to_server(self, photo_path):
        # type: (str) -> BookInfo or None
        """Sends the photo to the server and returns the book info"""

        logging.info("Sending photo to server")

        def decorate_sending_photo(ctx):
            phrases = [
                "Hmmm...",
                "Chvíli si to promyslím...",
                "Co je to za knihu ?",
                "To je nejspíš...",
                "Hmm...",
                "Možná to je...",
            ]
            shuffle(phrases)
            it = 0
            while ctx.ocr_request is None:
                logging.info("Decorating sending photo, iteration {}".format(it))
                ctx.tts.say(phrases[it % len(phrases)])
                it += 1
                sleep(3)
            ctx.ocr_request = None

        qi.async(decorate_sending_photo, self)
        with open(photo_path, "rb") as f:
            try:
                self.ocr_request = requests.post(self.ocr_server_address+"/cover", files={"file": f})
            except Exception, e:
                logging.error("Could not get book info from server: {}".format(e))
                self.ocr_request = False
                return None
        response = self.ocr_request

        if response.status_code != 200:
            logging.error("Server returned status code: {}, text: {}".format(response.status_code, response.text))
            return None

        logging.debug("Server returned: \n{}".format(pprint.pformat(response.json())))

        return BookInfo.from_json(response.json())

    def on_book_info_not_found(self):
        # type: () -> None
        logging.info("Playing on book info not found")
        self.tts.say("Nenašel jsem info o knize.")

    def say_book_info(self, book_info):
        # type: (BookInfo) -> None
        logging.info("Playing book info")
        self.tts.say("Kniha se jmenuje: " + book_info.title)
        self.tts.say("Autory jsou: " + ", ".join(book_info.authors))

    def go_to_box_area(self):
        # type: () -> None
        """Moves the robot to the box area using the first position in the position history"""
        logging.info("Going to box area")
        logging.debug("Position history: \n{}".format(pprint.pformat(self.position_history)))
        logging.debug("Current position: {}".format(self.motion.getRobotPosition(True)))
#        position_history_copy = copy.copy(self.position_history)
#        for position in reversed(position_history_copy):
#            self.go_to_position(*position, mirror_theta=True)
        x, y, _ = self.motion.getRobotPosition(True)
        self.go_to_position(*self.position_history[0], mirror_theta=False)
        self.rotate()

        logging.info("Going to box area finished")
        self.tts.say("Pojdme najít správnou krabici.")

    def go_to_position(self, x, y, theta, mirror_theta=False, visual_compass=False):
        # type: (float, float, float, bool, bool) -> None
        """Moves the robot to the given position (absolute coordinates)"""
        logging.debug("Going to position: x={}, y={}, theta={}, mirror_theta={}, viscomp={}".format(x, y, theta, mirror_theta, visual_compass))
        current_position = self.motion.getRobotPosition(True)
        cx, cy, ct = current_position
        if mirror_theta:
            theta = theta + 3.1415 if theta <= 0 else theta - 3.1415
            logging.debug("With mirrored theta: x={}, y={}, theta={}".format(x, y, theta))

        while abs(cx - x) > 0.05 or abs(cy - y) > 0.05 or abs(ct - theta) > 0.1:
            logging.debug("Not on the right position yet, current: x={}, y={}, theta={}".format(cx, cy, ct))
            if not visual_compass:
                # make current theta 0
                #self.moveTo(
                #    0,
                #   0 0,
                #    -current_position[2]
                #)

                self.reset_theta()

                logging.debug("Intermediate position: {}".format(self.motion.getRobotPosition(True)))

                # move to x, y
                self.moveTo(
                    x - current_position[0] if abs(x - current_position[0]) > 0.02 else 0,
                    y - current_position[1] if abs(y - current_position[1]) > 0.02 else 0,
                    theta if abs(theta) > 0.05 else 0
                )
            else:
                self.visual_compass.moveTo(
                    x - current_position[0] if abs(x - current_position[0]) > 0.02 else 0,
                    y - current_position[1] if abs(y - current_position[1]) > 0.02 else 0,
                    theta - current_position[2] if abs(theta - current_position[2]) > 0.05 else 0
                )

            current_position = self.motion.getRobotPosition(True)
            cx, cy, ct = current_position


        logging.debug("Going to position finished, current position: {}".format(self.motion.getRobotPosition(True)))

    def rotate(self):
        # type: () -> None
        logging.info("Rotating")
        self.motion.moveTo(0, 0, 3.14156/4.0)
        self.motion.moveTo(0, 0, 3.14156/4.0)
        self.motion.moveTo(0, 0, 3.14156/4.0)
        self.motion.moveTo(0, 0, 3.14156/4.0)
        logging.info("Done rotating")

    def find_box(self, book_info):
        # type: (BookInfo) -> str or None
        """
        Finds the box that matches the given book info.
        Robot moves along the box area and scans the boxes until the matching box or no box is found.
        :param book_info: BookInfo object
        :return: category of the box or None if no box was found
        """

        logging.info("Checking if in front is the box for book: " + str(book_info))

        path = self.take_photo(save_to="./run/box.png")
        text = self.get_text_from_image(path)
        logging.info("Text from image: " + str(text))
        if text is None or not text.lower().startswith("cat:"):
            logging.warn("Text is None or does not start with cat:")
            self.tts.say("Krabici jsem nenašel")
            return None

        category = text[4:].strip()

        if book_info.aligns_with_category(category):
            logging.info("Book aligns with category")
            return category
        else:
            logging.info("Book does not align with category '{}'".format(category))
            self.move_to_next_box()
            self.find_box(book_info)

    def move_to_next_box(self):
        # type: () -> None
        logging.info("Moving to next box")
        self.moveTo(0, self.box_step, 0)

    def get_text_from_image(self, image_path):
        # type: (str) -> ...
        logging.info("Requesting OCR for image {}".format(image_path))
        with open(image_path, "rb") as f:
            response = requests.post(self.ocr_server_address+'/category', files={"file": f})
        if response.status_code != 200:
            logging.error("Server returned status code: {}, text: {}".format(response.status_code, response.text))
            return None
        logging.debug("Server returned: \n{}".format(pprint.pformat(response.json())))
        return response.json()["category"]

    def box_found_decorations(self, book_info, box_category):
        # type: (BookInfo, str) -> None
        if box_category is None:
            self.tts.say("Tohle je správná krabice.")
            return
        self.tts.say("Tohle je správná krabice pro tuhle knihu, je to kategorie " + box_category)

    def box_not_found_decorations(self, book_info):
        # type: (BookInfo) -> None
        self.tts.say("Pro tuhle knihu jsem nenašel správnou krabici.")
        if book_info.categories is None:
            self.tts.say("Nenašel jsem krabici pro nezařazené knihy")
        elif len(book_info.categories) < 5:
            self.tts.say("Pro tyto kategorie nemáme krabice: " + ", ".join(book_info.categories))
        else:
            self.tts.say("Pro tyto a některé další kategorie nemáme krabice " + ", ".join(shuffle(book_info.categories)[:5]))