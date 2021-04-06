# Vendor SaltStack formulas

The directory is intedened to be used as a fileroot for SaltStack community formulas
like ones from [SaltStack Formulas](https://github.com/saltstack-formulas) repository.

Usually such 3rd party formulas are considered to be installed as described in
[SALT FORMULAS](https://docs.saltproject.io/en/latest/topics/development/conventions/formulas.html)
doc.

You may follow the doc or just put a formula here using the fileroot as a common
location for all 3rd party formulas.

Example for [consul-formula](https://github.com/saltstack-formulas/consul-formula):

```bash
SW=consul; curl -L https://github.com/saltstack-formulas/"$SW"-formula/archive/master.tar.gz \
    | tar -xzf - --strip-components=1 "$SW"-formula-master/"$SW"
```
