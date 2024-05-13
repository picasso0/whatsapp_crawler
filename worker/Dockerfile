FROM python:3.10
RUN mkdir -p /app
WORKDIR /app


# Install necessary packages
RUN apt-get update && apt-get install -y wget unzip

# Install Google Chrome
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && \
    apt-get install -y google-chrome-stable

# Determine the installed Chrome version
ENV CHROME_VERSION=$(google-chrome --product-version | grep -o "[^\.]*\.[^\.]*\.[^\.]*")

# Download and install the corresponding Chromedriver
RUN CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROME_VERSION") && \
    wget -q --continue -P /chromedriver "https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip" && \
    unzip /chromedriver/chromedriver* -d /usr/local/bin/

# Verify the versions match
RUN google-chrome --version && \
    chromedriver -v


COPY requirements.txt /
RUN pip install -r /requirements.txt

COPY . /app

# CMD ["tail","-f","/dev/null"]

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
#CMD ["uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "80"]
