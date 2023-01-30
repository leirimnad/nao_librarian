# PR-BI-ZIVS-2022-NAO-knihovnik 

## Getting the project
```sh
#this will install the packages into system we, however suggest creating separate virtual enviroment for server and client
#clone project
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
/opt/robots/bin/python-naov6 run.py --ip 10.10.48.223 --port 9559 --ocr http://10.10.48.223:8080 --rec tcp://10.10.48.91:9999
# named robot with default (9559) port
/opt/robots/bin/python-naov6 run.py --robot Albert  --ocr http://10.10.48.223:8080 --rec tcp://10.10.48.91:9999
```
`ocr` - server side address \
`rec` - NAOqi recognition server address

### Server
```sh
CUDA_VISIBLE_DEVICES=1 python3 server.py
```
