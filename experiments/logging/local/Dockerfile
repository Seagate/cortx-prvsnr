FROM centos:7.9.2009

RUN yum install -y python3

RUN mkdir -p /opt/demo-logger

COPY ./logger.py /opt/demo-logger

ENTRYPOINT ["python3", "/opt/demo-logger/logger.py"]
