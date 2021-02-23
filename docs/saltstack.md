# SaltStack Guidelines

## Overview

SaltStack is currently a primary SCM tool used by Provsioner and thus engines
the configuration routine for the whole CORTX.

The following documentation makes sense to check at first place:
- [SaltStack Introduction](https://docs.saltproject.io/en/latest/topics/index.html)
- [SaltStack Overview](https://docs.saltproject.io/en/master/topics/development/architecture.html)
- [SaltSTack Components Overview](https://docs.saltproject.io/en/getstarted/overview.html)

## SaltStack in Provisioner

TODO

## Tips & Tricks

### Jinja macros - Sharing the logic in SLS


From [Jinja docs](https://jinja.palletsprojects.com/en/2.11.x/templates/#macros):

> Macros are comparable with functions in regular programming languages.
> They are useful to put often used idioms into reusable functions to not repeat yourself (“DRY”).


Example:

`_macros.sls`
```yaml
{% macro pkg_installed(pkg_name, pkg_version=latest, refresh=True) %}

{{ pkg_name }}:
  pkg.installed:
    - version: {{ pkg_version }}
    - refresh: {{ refresh }}

{% endmacro %}
```

`editors/install.sls`
```yaml
{% from '../_macros.sls' import pkg_installed with context %}

{{ pkg_installed('vim') }}

{{ pkg_installed('emacs', '1.2.3') }}

{{ pkg_installed('nano', refresh=False) }}

{% endmacro %}
```
