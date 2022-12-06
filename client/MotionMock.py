# -*- encoding: UTF-8 -*- 
import sys
import motion
import time
from naoqi import ALProxy

app = qi.Application()
app.start()

session = app.session


server = qi.Session()
server.connect("tcp://10.10.48.91:9999")

def blink(proxy,flag):
    if(flag):
        proxy.fadeRgb(eyes,'#E5FFCC',0.5)
    else:
        proxy.fadeRgb(eyes,'#7F00FF',0.5)
    flag = not flag

def findBooks(img,server,threshold=0.2):
    return False #mock
    imdetect = server.service("ALIMDetection")

    res = imdetect.detect(img, None)

    res = list(filter(lambda o: o[2] > threshold, res))

    if len(res) > 0:
        objects = list(map(lambda o: o[0], res))
        objects = list(set(objects))
        return objects
    return null

def takePicture(session):
    vd = session.service("ALVideoDevice")

    cam = vd.subscribeCamera("cam", 0, 2, 13, 1)

    rimg = vd.getImageRemote(cam)

    im = rimg[6]
    nparr = np.frombuffer(im, np.uint8)
    nparr = nparr.reshape(480, 640, 3)

    #cv2.imwrite(expanduser("~") + "/zivs/zivs-task01/cam.png", nparr)
    return nparr

motionProxy = session.service("ALMotion")
flag = True
img = takePicture(session)
while(findBooks(img,server) == null):
    for i in range(0,2):#lean 2x30 deg = 60 deg right
       blink(proxy,flag)
        motionProxy.post.moveTo(0, 0, Math.PI/6)
        img = takePicture(session)
        if(findBooks(img,server)):
            break
     #reset position   
     motionProxy.post.moveTo(0,0,2/6*Math.PI)
     
     for i in range(0,2):
        blink(proxy,flag)
        motionProxy.post.moveTo(0, 0, Math.PI/6)
        img = takePicture(session)
        if(findBooks(img,server)):
            break
    motionProxy.post.moveTo(0,0,-2/6*Math.PI)
    motionProxy.post.MoveTo(0,0.5,0)

    
