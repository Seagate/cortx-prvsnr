s3server:
{% if "physical" in grains['virtual'] %}
    no_of_inst: 11
{% else %}
    no_of_inst: 1
{% endif %}
