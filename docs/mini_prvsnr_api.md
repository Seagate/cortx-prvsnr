# Provisioner Support for Mini Provisioner API

## Table of Contents

*   [Overview](#overview)

*   [Mini Provisioner Specification](#mini-provisioner-specification)

    *   [Syntax](#syntax)
    *   [Base Hooks](#base-hooks)
    *   [Event Hooks](#event-hooks)
    *   [Constraints](#constraints)
    *   [Templating](#templating)
    *   [Environment variables](#environment-variables)
    *   [Example](#example)

*   [Mini Provisioner Commands](#mini-provisioner-commands)

    *   [Hook Renderer](#hook-renderer)
    *   [Hook Caller](#hook-caller)

## Overview

Provisioner supports mini-provisioner interfaces exposed by CORTX componnents
(including Provisioner itself).

These interfaces are defined using specification files located in
`/opt/seagate/cortx/<component>/conf/setup.yaml`.

The file includes description of commands (hooks) that should be called
in scope CORTX wide flows (like deployment or upgrade) at certain stages.

Please read more about the spec in
[Mini Provisioner Specification](#mini-provisioner-specification).

The following CORTX flows are considered for the moment:

*   deployment
*   online (rolling) upgrade
*   offline upgrade

The hooks might be triggered on multiple levels:

*   cluster: these hooks are called only once per a cluster
*   node: these hooks are called once per a node

Provisioner exposes few commands to support mini-provisioner interfaces:

*   `provisioner mini_api render` to render and verify the specification
*   `provisioner mini_api hook` to trigger a hook

These commands can be used to test the specification along with the hooks
in development environment.

Please read more about the command in
[Mini Provisioner Commands](#mini-provisioner-commands).

## Mini Provisioner Specification

Mini provisioner specification is a [yaml](https://yaml.org/) file
with optional [Jinja](https://jinja.palletsprojects.com/en/3.0.x/) templating.

### Syntax

Top level keys:

*   `<component>`
*   `support_bundle`

### Base Hooks

Under `<component>` the following **base hooks** as a second level keys
are expected:

*   `post_install`
*   `prepare`
*   `config`
*   `init`
*   `test`
*   `upgrade`
*   `reset`
*   `cleanup`
*   `backup`
*   `restore`

Each hook can be defined using the following fields:

*   `cmd`: (optional) A string. A command to call. If not defined - not called.
*   `args`: (optional) A string or a list of strings. Command arguments.
*   `when`: (optional) A boolean. Defines constraints on the context when
    a hook should be called. Usually Jinja expressions come here.
    If not specified the following default constraint is used:
    `level == 'node'`.

### Event Hooks

Each base hook may include also specification for `pre` and `post` **event
hooks**. These hooks have the same format as above with a small difference:
the inherit `cmd` and `args` from base specification: if these fields
are not specified for an event hook base hook value is used as a default one.

Event hooks specifications are optional and the values can be:

*   a dictionary with the same format as for base hooks
*   a string which is equal to "cmd" (as a shortest form of a hook spec)
*   a boolean:
    *   true: call the hook with the same spec as for main one
    *   false: do not call
*   undefined (`null`): do not call

A case when 'cmd' is undefined for the base hook but specified
for an event one is valid.

### Constraints

A hook can be subscribed / unsubscribed to using spec constraints.

A constraint is specified using `when` key and boolean or a Jinja2
expression `{{...}}` that should be resolved to a boolean.

If the constraint is not specified then default constraint `level == node`
is applied.

### Templating

Any Jinja templates can be used with no restrictions.

The following context variables are available:

*   `level`: `cluster` or| `node`
*   `flow`: `deploy` or `upgrade` or `upgrade-offline`

### Environment variables

When called commands from mini provisioner hooks would be supplied with
a set of environment variables:

*   `PRVSNR_MINI_HOOK` - the hook name (e.g. 'prepare', 'post-config', 'pre-test'')
*   `PRVSNR_MINI_FLOW` - active flow
*   `PRVSNR_MINI_LEVEL` - active level

Additional in scope of upgrade flows:

*   `CORTX_VERSION` - current CORTX release
*   `CORTX_UPGRADE_VERSION` - target CORTX release

These environment variable can be used to build a conditional logic inside
the commands.

### Example

```yaml
---

<component>:
  post_install:
    cmd: <component>_setup post_install
    args: --config $URL

  prepare:
    cmd: <component>_setup prepare
    args: --config $URL
    # constraint EXAMPLE
    when: {{ level in ('node', 'cluster') and flow == 'upgrade-offline' }}

  config:
    # different commands EXAMPLE
    {% if level == 'node' %}
    cmd: <component>_setup config-node
    {% else %}
    cmd: <component>_setup config-cluster
    {% endif %}
    when: {{ level in ('node', 'cluster') }}
    args: --config $URL

  init:
    cmd: <component>_setup init
    args: --config $URL

  test:
    cmd: <component>_setup test
    args: --config $URL [--plan (sanity|regression|full|performance|scalibility)]

  upgrade:
    # pre/post hooks EXAMPLES
    pre:
      # a hook is triggered before the 'upgrade' stage for the cluster
      cmd: <component>_setup pre-upgrade
      # but it can be any command actually, e.g.
      # cmd: pkill something
      when: {{ level == 'cluster' and flow == 'upgrade-offline' }}
    post:
      # a hook is triggered after 'upgrade' stage for a node
      cmd: <component>_setup post-upgrade
      when: {{ level == 'node' and flow == 'upgrade' }}

  reset:
    cmd: <component>_setup reset
    args: --config $URL

  cleanup:
    cmd: <component>_setup cleanup
    args: --config $URL

  backup:
    cmd: <component>_setup backup
    args: --location $URL

  restore:
    cmd:  <component>_setup restore
    args: --location $URL

support_bundle:
  - /opt/seagate/cortx/provisioner/cli/provisioner-bundler
```

## Mini Provisioner Commands

Provsiioner provides the following commands to help with hooks
specification and verification.

### Hook Renderer

The command doesn't require any specific environment and
can be used in dev environment. The only requirement is to install
provisioner python API.

```bash
provisioner mini_api render <spec> <flow> <level> [--confstore URL] [--normalize] 
```

Arguments:

*   `spec` - path to a spec file
*   `flow` - one of `{deploy,upgrade,upgrade-offline}`
*   `level` - on of `{cluster,node}`
*   `--confstore` - (optional) ConfStore URL
*   `--normalize` - (optional) normalize the result

By default the command will just render and make the specmore explicit.
With `--normalize` all not active hooks for the current cotext would be removed.

Example:

The following command will output a list of hooks that should be called
in scope of rolling upgrade on the node level:

```bash
provisioner mini_api render ./setup.yaml upgrade node --normalize
```

### Hook Caller

Pre-requieistes:

*   CORTX is deployed

```bash
provisioner mini_api hook <hook> <flow> <level> \
    [--sw [SW [SW ...]]] \
    [--ctx-vars [KEY=VALUE [KEY=VALUE ...]]] \
    [--fail-fast] \
    [--targets STR]
```

Arguments:

*   `hook` - a hook name, one of base hooks (`backup`, `config` ...)
    or event ones (`pre-upgrade`, `post-cleanup` ...)
*   `flow` - one of `{deploy,upgrade,upgrade-offline}`
*   `level` - on of `{cluster,node}`
*   `--sw` - (optional) list of sw (e.g. `--sw csm ha`), all if not specified
*   `--ctx-vars` - (optional) a key-value pairs to pass to hook commands as env variable
    (e.g. `--ctx-vars MYENV1=123 MYENV=test`)
*   `--fail-fast` - (optional) If specified hooks processing will fail on a first hook call error.
    Otheriwse all hooks are called and errors are collected.
*   `--targets` - (optional) Limit hooks execution to only listed nodes. By default - all the nodes.
    (e.g. `--targets srvnode-1`)

Example:

The following command will trigger a `pre-upgrade` hook for Hare and HA
in context of offline upgrade on the cluster level on the second node:

```bash
provisioner mini_api hook pre-upgrade upgrade-offline cluster \
    --sw hare ha --ctx-vars MYENV=somevalue --targets srnode-2
```
