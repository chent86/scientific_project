import os
os.system("docker-compose -f docker/docker-compose.yml up && \
           docker-compose -f docker/docker-compose.yml run check python3 run.py")