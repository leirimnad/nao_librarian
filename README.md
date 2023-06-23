# PR-BI-ZIVS-2022-NAO-knihovnik 

NAO Librarian project. \
Makes NAO robot look for books around him, search the web for their genres and lead the user to the box that corresponds with a genre. \
For more details on the robot's scenario, see [report](report_zivs_en.pdf) or check out the [video presentation](https://youtu.be/UQr7s4u6YVg).


## Getting the project
```sh
# this will install the packages into the system 
# however, we suggest creating a separate virtual enviroment for a server and a client
# clone project
git clone git@gitlab.fit.cvut.cz:skrbek/pr-bi-zivs-2022-nao-knihovnik.git
cd pr-bi-zivs-2022-nao-knihovnik
cd client
pip2 install -r requirements.txt # requirements for client side
cd ../server
pip3 install -r requirements.txt # requirements for server side
```
## Running the project

### Client
```sh
# unnamed robot on given port
/opt/robots/bin/python-naov6 run.py --ip ROBOT_IP --port ROBOT_PORT --ocr OCR_ADDRESS --rec AL_RECOGNITION_ADDRESS
# named robot with default (9559) port
/opt/robots/bin/python-naov6 run.py --robot ROBOT_NAME  --ocr OCR_ADDRESS --rec AL_RECOGNITION_ADDRESS


# examples with defined variables
/opt/robots/bin/python-naov6 run.py --ip 10.10.48.223 --port 9559 --ocr http://192.168.1.1:8080 --rec tcp://192.168.1.1:9999
/opt/robots/bin/python-naov6 run.py --robot Albert  --ocr http://192.168.1.1:8080 --rec tcp://192.168.1.1:9999
```
**Parameters:** \
`ip`, `port` - robot's address, or `robot` - robot's name (runs with port _9559_) \
`ocr` - address of the EasyOCR server (running the [/server/server.py](./server/server.py) file) \
`rec` - NAOqi recognition server address

### Server
```sh
CUDA_VISIBLE_DEVICES=1 python3 server.py
```
`CUDA_VISIBLE_DEVICES` - id of the GPU to use
