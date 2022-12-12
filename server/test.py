#import requests
#with open('./images/img.png', 'rb') as f:
#    r = requests.post('http://localhost:8080/cover', files={'file': f})
#``    print(r)
#    print(r.json())


#with open('./detective.jpg', 'rb') as f:
#    r = requests.post('localhost:8080/category', files={'file': f})
#    print(r)
#    print(r.json())














# coding=utf-8
from __future__ import division, print_function, unicode_literals
import copy
#from book import Book, BookInfo, ImageBook
import numpy as np
import cv2
import requests
#import qi
from datetime import datetime
import pprint
#from tools import *
#from perspective_warp import get_warped_image
from random import shuffle
from time import sleep



class BookInfo(object):
    def __init__(self, title, authors, categories):
        super(BookInfo, self).__init__()
        self.title = title
        self.authors = authors
        self.categories = categories
        
    @classmethod
    def from_json(cls, json_text):
        return cls(json_text.get('title'), json_text.get('authors'), json_text.get('categories'))


class NAOLibrarian(object):
    def __init__(self):
        self.ocr_server_address = 'http://localhost:8080'

    def send_photo_to_server(self, photo_path):
        # type: (str) -> BookInfo or None

        #print("Sending photo to server")

        with open(photo_path, "rb") as f:
            self.ocr_request = requests.post(self.ocr_server_address+"/cover", files={"file": f})
        response = self.ocr_request

        if response.status_code != 200:
            #print("Server returned status code: {}, text: {}".format(response.status_code, response.text))
            return None

        #print("Server returned: \n{}".format(pprint.pformat(response.json())))

        return BookInfo.from_json(response.json())

    
    def get_text_from_image(self, image_path):
        # type: (str) -> ...
        #print("Requesting OCR for image {}".format(image_path))
        with open(image_path, "rb") as f:
            response = requests.post(self.ocr_server_address+'/category', files={"file": f})
        if response.status_code != 200:
            #print("Server returned status code: {}, text: {}".format(response.status_code, response.text))
            return None
        #print("Server returned: \n{}".format(pprint.pformat(response.json())))
        return response.json()["category"]
    
nao = NAOLibrarian()


tmp = nao.send_photo_to_server('./img.png')
print('\n\n\n\n')
print(tmp.title,tmp.authors,tmp.categories[0])
tmp=nao.get_text_from_image('./detective.jpg')
print('\n\n\n\n')
print(tmp)

