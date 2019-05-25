docker-compose -f docker/docker-compose.yml up
docker-compose -f docker/docker-compose.yml run preprocess python3 run.py
docker-compose -f docker/docker-compose.yml run check python3 run.py