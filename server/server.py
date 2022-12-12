from http.server import HTTPServer, BaseHTTPRequestHandler
import cgi
import os
import easyocr
import json
import datetime
from pprint import pprint
import requests
from datetime import datetime
    
class FileUploadHandler(BaseHTTPRequestHandler):
    reader = easyocr.Reader(['en', 'cs'],gpu=True)

    def get_polygon_area(self,polygon):
        """Calculate the area of a polygon."""
        area = 0
        for i in range(len(polygon)):
            j = (i + 1) % len(polygon)
            area += polygon[i][0] * polygon[j][1]
            area -= polygon[i][1] * polygon[j][0]
        area = abs(area) / 2.0
        return area
    def get_text(self,img_path):
        time = datetime.now()
        alnum = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ '
        result = self.reader.readtext(img_path, allowlist=alnum, batch_size=200,workers=4, decoder="wordbeamsearch")
        print(f"Request took {datetime.now() - time}")
        result = list(map(lambda x: [x[1], self.get_polygon_area([x[0][0], x[0][1], x[0][2], x[0][3]])], result))
        result.sort(key=lambda x: x[1], reverse=True)
        pprint(result)
        return result[0][0]

    def process_image(self,img_path):
        time = datetime.now()
        alnum = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ '
        result = self.reader.readtext(img_path, allowlist=alnum, batch_size=200,workers=4, decoder="wordbeamsearch")
        print(f"Request took {datetime.now() - time}")
        result = list(map(lambda x: [x[1], self.get_polygon_area([x[0][0], x[0][1], x[0][2], x[0][3]])], result))
        result.sort(key=lambda x: x[1], reverse=True)
        pprint(result)

        req = requests.get('https://www.googleapis.com/books/v1/volumes',
                        params={'q': str(result[0][0]) + " " + str(result[1][0]), "key": "AIzaSyCL1jiXvWMEBBhu1ulEVSgELE_h84IdpqM"})
        book_id = req.json()['items'][0]['id']

        book = requests.get('https://www.googleapis.com/books/v1/volumes/' + book_id,
                        params={"key": "AIzaSyCL1jiXvWMEBBhu1ulEVSgELE_h84IdpqM"}).json()['volumeInfo']

        print("Title: " + book['title'])

        if 'authors' in book.keys():
            print("Authors: " +", ".join(book['authors']))
        if 'description' in book.keys():
            print("Description: " + book['description'])
        if 'categories' in book.keys():
            print("Categories: " +", ".join(book['categories']))
        if 'imageLinks' in book.keys() and 'thumbnail' in book['imageLinks'].keys():
            print("Image: " + book['imageLinks']['thumbnail'])
        if 'publishedDate' in book.keys():
            print("Published: " + book['publishedDate'])
        if 'pageCount' in book.keys():
            print("Pages: " + str(book['pageCount']))
        if 'averageRating' in book.keys():
            print("Rating: " + str(book['averageRating']))
        if 'language' in book.keys():
            print("Language: " + book['language'])
        return book

    def do_POST(self):
        filename = datetime.now().strftime("%d-%m-%Y %H-%M-%S")+".jpg"
        form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={'REQUEST_METHOD':'POST', 'CONTENT_TYPE':self.headers['Content-Type']})
        file_item = None
        print(self.path)
        if self.path == '/cover':
            print (f"RECOGNISE COVER from {self.client_address[0]}")
            file_item = form['file']
            with open('images/'+filename, 'xb') as f:
                f.write(file_item.file.read())
            book=self.process_image('images/'+filename)
            # Send a response indicating that the file was uploaded successfully
            self.send_response(200)
            self.end_headers()
            json_string = json.loads(json.dumps(book))
            print(json_string)
            json_modified = {"title": json_string["title"], "authors": json_string["authors"], "categories": json_string["categories"]}
            self.wfile.write(json.dumps(json_modified).encode('utf-8'))
        elif self.path == '/category':
            print (f"RECOGNISE CATEGORY from {self.client_address[0]}")
            with open('./images/'+filename, 'wb') as f:
                f.write(form['file'].file.read())
            category=self.get_text('./images/'+filename)
            self.send_response(200)
            self.end_headers()
            print(f"category is {category}")
            self.wfile.write(json.dumps({"category": category}).encode('utf-8'))
        
        else:
            self.send_response(403)
            self.end_headers()

httpd = HTTPServer(('0.0.0.0', 8080), FileUploadHandler)
print("server started")
httpd.serve_forever()
