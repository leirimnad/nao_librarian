# coding=utf-8
from tools import get_distance


class ImageBook(object):
    """Class to represent a book position in the image"""
    def __init__(self, image, xl, xr, yt, yb):
        self.image = image
        self.xl = xl
        self.xr = xr
        self.yt = yt
        self.yb = yb
        self.vertical_distance, self.horizontal_distance, self.distance, self.rotation = \
            get_distance((xl + xr) / 2, (yt + yb) / 2, image)

    def get_same_book(self, books):
        # type: (list) -> ImageBook
        """Return the book in the list that is the closest to be this one"""

        sorted_books = sorted(books, key=lambda book: abs(book.distance - self.distance))
        return sorted_books[0]

    def __str__(self):
        return "ImageBook with x: ({}, {}), y: ({}, {}), distance: v{} h{} d{} r{}" \
            .format(
                self.xl, self.xr, self.yt, self.yb,
                round(self.vertical_distance, 2), round(self.horizontal_distance, 2),
                round(self.distance, 2), round(self.rotation, 2)
            )


class Book(object):
    """Class to represent a book in the real world"""
    def __init__(self, image_book):
        self.info = None
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
    """Class to represent a book info, with title, authors and categories"""
    def __init__(self, title, authors, categories):
        super(BookInfo, self).__init__()
        self.title = title
        self.authors = authors
        self.categories = categories

    def __str__(self):
        return "BookInfo: {} by {}, categories: {}".format(
            self.title or "Untitled",
            ", ".join(self.authors or ["No authors"]),
            ", ".join(self.categories or "No categories")
            )

    def aligns_with_category(self, category):
        if category.lower() == "uncategorized":
            return True
        elif self.categories is None:
            return False

        for cat in self.categories:
            if category.lower() in cat.lower():
                return True
        return False

    @classmethod
    def from_json(cls, json_text):
        return cls(json_text.get('title'), json_text.get('authors'), json_text.get('categories'))
