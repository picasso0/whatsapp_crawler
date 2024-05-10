FROM python:3.10
RUN mkdir -p /app
WORKDIR /app

COPY requirements.txt /
RUN pip install -r /requirements.txt

COPY . /app

# CMD ["tail","-f","/dev/null"]

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8787" ,"--workers","1"]
#CMD ["uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "80"]
