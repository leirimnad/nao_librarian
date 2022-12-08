# PR-BI-ZIVS-2022-NAO-knihovnik



## Running the project

```sh
opt/robots/bin/python-naov6 run.py --ip 10.10.48.XXX --port 9559 --ocr 147.32.77.128:8080 --rec tcp://10.10.48.91:9999
```


## Robots

Name | IP
---|---
Albert | 10.10.48.220
Nikola	| 10.10.48.221
Ervin |	10.10.48.222
Alan	| 10.10.48.223
Karel	| 10.10.48.224
Thomas	| 10.10.48.225

## ALIMDetection response:

```json
[
  ['Vehicle', '/m/07yv9', 0.004575617611408234, [0L, 0L, 843L, 914L], None],
  ['Category', 'code', 0.004575617611408234, [y1L, x1L, y2L, x2L], None]
]
```