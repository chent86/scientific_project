INPUT_DIR = "data/input"
OUTPUT_DIR = "data/output"

import os
os.system("docker-compose -f docker/docker-compose.yml up && \
           docker-compose -f docker/docker-compose.yml run -e INPUT_DIR="+INPUT_DIR+" -e OUTPUT_DIR="+OUTPUT_DIR+" preprocess python3 run.py")