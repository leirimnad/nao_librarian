# coding=utf-8

import qi
import argparse
import sys
from nao_librarian import NAOLibrarian

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", type=str, help="Robot IP address.", required=True)
    parser.add_argument("--port", type=int, help="Naoqi port number", required=True)
    parser.add_argument("--ocr", type=str, help="OCR server address", required=True)
    parser.add_argument("--rec", type=str, help="Object recognition server address", required=False, default="")

    args = parser.parse_args()
    try:
        connection_url = "tcp://" + args.ip + ":" + str(args.port)
        app = qi.Application(["Librarian", "--qi-url=" + connection_url])
    except RuntimeError:
        print ("Can't connect to Naoqi at ip \"" + args.ip + "\" on port " + str(args.port) + ".\n" +
               "Please check your script arguments. Run with -h option for help.")
        sys.exit(1)
    react_to_touch = NAOLibrarian(app, args.ocr, args.rec)
    app.run()
