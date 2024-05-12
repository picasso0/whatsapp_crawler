FROM python:3.10
RUN mkdir -p /app
WORKDIR /app

COPY requirements.txt /
RUN pip install -r /requirements.txt

COPY . /app

# CMD ["tail","-f","/dev/null"]

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8888" ]
#CMD ["uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "80"]
