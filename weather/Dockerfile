FROM python:3.9.7
COPY . /opt/app
WORKDIR /opt/app
RUN pip install -r requirements.txt
ADD main.py .
CMD ["python", "-u", "main.py"]
