FROM python:3.9

WORKDIR /app
COPY . .

ENV DB_USER=zadac
ENV DB_PASSWORD=password
ENV DB_HOST=192.168.56.101
ENV DB_PORT=5432
ENV DB_NAME=postgres

RUN pip install -r lib.txt 
CMD ["python", "main.py"]
