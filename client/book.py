# coding=utf-8

class Book(object):
    def __init__(self, x, y):
        super(Book, self).__init__()
        self.info = None
        self.x = x
        self.y = y

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