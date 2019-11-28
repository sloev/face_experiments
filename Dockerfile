FROM python:latest

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

ADD requirements.txt .
RUN pip install -r requirements.txt
ADD server.py .
ADD python_drawing.py .

EXPOSE 80
CMD ["python", "server.py"]