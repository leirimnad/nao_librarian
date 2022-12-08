from http.server import HTTPServer, BaseHTTPRequestHandler
import cgi
import os

class FileUploadHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={'REQUEST_METHOD':'POST', 'CONTENT_TYPE':self.headers['Content-Type']})
        file_item = form['file']
        if file_item.filename:
            file_name = os.path.basename(file_item.filename)
            with open('./images/img.png', 'wb') as f:
                f.write(file_item.file.read())

        # Send a response indicating that the file was uploaded successfully
        self.send_response(200)
        self.end_headers()

httpd = HTTPServer(('0.0.0.0', 8080), FileUploadHandler)
httpd.serve_forever()
