INPUT_DIR = "data/input"
OUTPUT_DIR = "data/output"
RECREATE = 0  # 0 已存在的文件不重新处理 1 强制重新生成 

import os
os.system("docker-compose -f docker/docker-compose.yml up -d && "
          f"docker-compose -f docker/docker-compose.yml run -e INPUT_DIR={INPUT_DIR} -e OUTPUT_DIR={OUTPUT_DIR} -e RECREATE={RECREATE} preprocess python3 run.py")