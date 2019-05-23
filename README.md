# scientific project

## SatFTA solver for the computation of MCSs in FTA

### quick start
```
cd docker
docker-compose up -d
docker-compose run preprocess python3 run.py
```

### file

|文件名|功能|
|-|-|
|tools.py|辅助函数|
|simplifier.py|化简|
|find_modules.py|找模块|
|run.py|批量化简脚本|
|data/raw/|输入文件|
|data/result|输出结果|

### todo

nus9601, das9701, elf9601, edf9206的化简

### pickle demo

```python
import pickle

data_file = open("pickle_data", "rb")
data = pickle.load(data_file)
```