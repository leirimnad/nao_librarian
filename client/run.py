# coding=utf-8

import qi
import argparse
import functools
import sys
from nao_librarian import NAOLibrarian

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", type=str, help="Robot IP address.", required=True)
    parser.add_argument("--port", type=int, help="Naoqi port number", required=True)
    parser.add_argument("--ocr", type=str, help="OCR server address", required=True)

    args = parser.parse_args()
    try:
        connection_url = "tcp://" + args.ip + ":" + str(args.port)
        app = qi.Application(["ReactToTouch", "--qi-url=" + connection_url])
    except RuntimeError:
        print ("Can't connect to Naoqi at ip \"" + args.ip + "\" on port " + str(args.port) + ".\n"
                                                                                              "Please check your script arguments. Run with -h option for help.")
        sys.exit(1)
    react_to_touch = NAOLibrarian(app, args.ocr)
    app.run()
