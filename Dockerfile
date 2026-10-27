FROM python:3.12-slim

RUN pip install --no-cache-dir kazoo==2.10.0
WORKDIR /app
COPY coordinator.py /app/coordinator.py
CMD ["python", "-u", "/app/coordinator.py"]

