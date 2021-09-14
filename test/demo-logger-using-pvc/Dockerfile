FROM centos:7.9.2009

RUN yum install -y python3

RUN mkdir -p /opt/demoLogger /var/log/demoLogger

COPY ./logger.py /opt/demoLogger

ENTRYPOINT ["python3", "/opt/demoLogger/logger.py"]
