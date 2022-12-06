
# -*- encoding: UTF-8 -*- 

'''Walk: Small example to make Nao walk'''
import sys
import motion
import time
from naoqi import ALProxy




def findBook():
    return False
 motionProxy = ALProxy("ALMotion", robotIP, 9559)
flag = True
while(not findBook):
    for i in range(0,2):
        if(flag):
            proxy.fadeRgb(eyes,'#123456',0.5)
            flag=not flag
        else:
            proxy.fadeRgb(eyes,'#145756',0.5)
            flag=not flag
        motionProxy.post.moveTo(0, 0, Math.PI/6)
        
     motionProxy.post.moveTo(0,0,2/6*Math.PI)
     
     for i in range(0,5):
        if(flag):
            proxy.fadeRgb(eyes,'E5FFCC',0.5)
            flag=not flag
        else:
            proxy.fadeRgb(eyes,'#7F00FF',0.5)
            flag=not flag
        motionProxy.post.moveTo(0, 0, Math.PI/6)
    motionProxy.post.moveTo(0,0,-2/6*Math.PI)
    motionProxy.post.MoveTo(0,0.5,0)
