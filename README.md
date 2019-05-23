# scientific project

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

### environment

```
Docker version 18.09.2
docker-compose version 1.23.2
```
