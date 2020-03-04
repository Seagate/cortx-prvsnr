haproxy:
    backend:
        s3authserver:
            ssl_enabled: false
        s3server:
            ssl_enabled: false
    frontend:
        s3authserver:
            ssl_enabled: true
        s3server:
            ssl_enabled: true
{% if "physical" in grains['virtual'] %}
    nbproc: 12
{% else %}
    nbproc: 2
{% endif %}