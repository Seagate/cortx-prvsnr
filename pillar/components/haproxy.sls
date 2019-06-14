haproxy:
    nbproc: 4
    frontend:
        s3server:
            ssl_enabled: true
        s3authserver:
            ssl_enabled: true
    backend:
        s3server:
            ssl_enabled: false
        s3authserver:
            ssl_enabled: true
