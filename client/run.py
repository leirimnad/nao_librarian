# coding=utf-8

import qi
import argparse
import sys
from nao_librarian import NAOLibrarian
import logging
from datetime import datetime
import re

def find_robot(name):
    ips = {
        'Albert':'10.10.48.220',
        'Nikola':'10.10.48.221',
        'Ervin':'10.10.48.222',
        'Alan':'10.10.48.223',
        'Karel':'10.10.48.224',
        'Thomas':'10.10.48.225'
           }
    return ips.get(name,'')

if __name__ == "__main__":

    logging.basicConfig(
        format='%(asctime)s %(message)s',
        datefmt='%H:%M:%S',
        filename="logs/"+datetime.now().strftime("%d-%m-%Y %H-%M-%S") + '.log',
        level=logging.DEBUG
    )
    logging.getLogger().addHandler(logging.StreamHandler())

    parser = argparse.ArgumentParser()
    parser.add_argument("--robot", type=str, help="Robot Name or address.", required=True)
    parser.add_argument("--port", type=int, help="Naoqi port number", required=True)
    parser.add_argument("--ocr", type=str, help="OCR server address", required=True)
    parser.add_argument("--rec", type=str, help="Object recognition server address", required=False, default="")

    args = parser.parse_args()
    pat = re.compile("^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$")

    if not pat.match(str(args.robot)):
        ip=find_robot(str(args.robot))
        if ip == '':
            print("Robot {} was not found.".format(str(args.robot)))
            sys.exit(1)
        else:
            print('The script will run on {} ip {}'.format(args.robot, ip))
    else:
        print('The script will run on unnamed robot with ip {}'.format(args.robot))
        ip = str(args.robot)
    try:
        connection_url = "tcp://" + ip + ":" + str(args.port)
        logging.info("Connection url: {}".format(connection_url))
        app = qi.Application(["Librarian", "--qi-url=" + connection_url])
    except RuntimeError:
        print ("Can't connect to Naoqi at ip \"" + args.ip + "\" on port " + str(args.port) + ".\n" +
               "Please check your script arguments. Run with -h option for help.")
        sys.exit(1)

    librarian = NAOLibrarian(app, args.ocr, args.rec)
    app.run()
    
