FROM python:3.9.7

ARG environment
ENV ENVIRONMENT ${environment}

COPY . /opt/app
WORKDIR /opt/app
RUN pip install -r requirements.txt

CMD ["./start.sh"]
