# coding=utf-8
from tools import get_distance


class ImageBook(object):
    def __init__(self, image, xl, xr, yt, yb):
        self.image = image
        self.xl = xl
        self.xr = xr
        self.yt = yt
        self.yb = yb
        self.vertical_distance, self.horizontal_distance, self.distance, self.rotation = \
            get_distance((xl + xr) / 2, (yt + yb) / 2, image)

    def get_similar_books(self, books):
        # type: (ImageBook, list) -> ImageBook
        # TODO: Implement this
        sorted_books = sorted(books, key=lambda book: abs(book.distance-self.distance))
        return sorted_books[0]

class Book(object):
    def __init__(self, image_book):
        self.image_book = image_book
        self.x = image_book.vertical_distance
        self.y = image_book.horizontal_distance
        self.rotation = image_book.rotation
        self.distance = image_book.distance

    def add_info(self, info):
        self.info = info

    def __str__(self):
        return "Book at ({}, {})".format(self.x, self.y)


class BookInfo(object):
    def __init__(self, title, author):
        super(BookInfo, self).__init__()
        self.title = title
        self.author = author

    def __str__(self):
        return "BookInfo: {} by {}".format(self.title, self.author)

    @classmethod
    def from_json(cls, json_text):
        return cls(json_text['title'], json_text['author'])
