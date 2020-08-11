FROM centos:8.2.2004

COPY setup_fpm.sh /tmp/
RUN bash /tmp/setup_fpm.sh \
    && rm -f /tmp/setup_fpm.sh

ENTRYPOINT [ "fpm" ]
CMD [ "--help" ]
