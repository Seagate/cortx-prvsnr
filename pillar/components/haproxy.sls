haproxy:
    backend:
        s3authserver:
            ssl_enabled: true
        s3server:
            ssl_enabled: false
    frontend:
        s3authserver:
            ssl_enabled: true
        s3server:
            ssl_enabled: true
    nbproc: 4
