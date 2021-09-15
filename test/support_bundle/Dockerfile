FROM centos:7.9.2009

RUN yum install -y python3

RUN mkdir -p /app

WORKDIR /app

COPY support_bundle.py  sb_config.py /app/

ENTRYPOINT ["python3", "/app/support_bundle.py"]

