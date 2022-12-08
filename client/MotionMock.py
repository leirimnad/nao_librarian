# -*- encoding: UTF-8 -*- 
import sys
import time
import numpy as np
from naoqi import ALProxy


def blink(proxy, flag):
    if (flag):
        proxy.fadeRgb('FaceLeds', '#E5FFCC', 0.5)
    else:
        proxy.fadeRgb('FaceLeds', '#7F00FF', 0.5)
    flag = not flag


def findBooks(img, server, threshold=0.2):
    return False  # mock
    imdetect = server.service("ALIMDetection")

    res = imdetect.detect(img, None)

    res = list(filter(lambda o: o[2] > threshold, res))

    if len(res) > 0:
        objects = list(map(lambda o: o[0], res))
        objects = list(set(objects))
        return objects
    return None


def takePicture(session):
    vd = session.service("ALVideoDevice")

    cam = vd.subscribeCamera("cam", 0, 2, 13, 1)

    rimg = vd.getImageRemote(cam)

    im = rimg[6]
    nparr = np.frombuffer(im, np.uint8)
    nparr = nparr.reshape(480, 640, 3)

    # cv2.imwrite(expanduser("~") + "/zivs/zivs-task01/cam.png", nparr)
    return nparr


def look_for_book():
    books = findBooks(img, server)
    while (books == None):
        for i in range(0, 2):  # lean 2x30 deg = 60 deg right
            blink(led_proxy, flag)
            motionProxy.post.moveTo(0, 0, np.pi / 6)
            img = takePicture(session)
            books = findBooks(img, server)
            if (books):
                return books
        # reset position
        motionProxy.post.moveTo(0, 0, 2 / 6 * np.pi)

        for i in range(0, 2):
            blink(led_proxy, flag)
            motionProxy.post.moveTo(0, 0, np.pi / 6)
            img = takePicture(session)
            books = findBooks(img, server)
            if (books):
                return books
        motionProxy.post.moveTo(0, 0, -2 / 6 * np.pi)
        motionProxy.post.MoveTo(0, 0.5, 0)
        books = findBooks(img, server)
    return books


app = qi.Application()
app.start()

session = app.session

SERVER_CONNECT_STRING = "tcp://10.10.48.91:9999"
server = qi.Session()
server.connect(SERVER_CONNECT_STRING)

motionProxy = session.service("ALMotion")
led_proxy = session.service("ALLeds")
flag = True
img = takePicture(session)
