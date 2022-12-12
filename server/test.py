import requests
with open('./images/img.png', 'rb') as f:
    r = requests.post('http://147.32.77.128:8080/cover', files={'file': f})
    print(r)
    print(r.json())
#with open('./clasic.jpg', 'rb') as f:
#    r = requests.post('http://147.32.77.128:8080', files={'text': f})
#    print(r)
#    print(r.json())

#with open('./textbook.jpg', 'rb') as f:
#    r = requests.post('http://147.32.77.128:8080', files={'text': f})
#    print(r)
#    print(r.json())

#with open('./childrens_books.jpg', 'rb') as f:
#    r = requests.post('http://147.32.77.128:8080', files={'text': f})
#    print(r)
#    print(r.json())

#with open('./thriler.jpg', 'rb') as f:
#    r = requests.post('http://147.32.77.128:8080', files={'text': f})
#    print(r)
#    print(r.json())

with open('./detective.jpg', 'rb') as f:
    r = requests.post('http://147.32.77.128:8080/category', files={'text': f})
    print(r)
    print(r.json())
