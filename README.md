# swcfg2confluence

## Description

This Ansible playbook pushes Alcatel Lucent AOS Release 6 (and later ZyXEL
GS1920) configuration to Atlassian Confluence.

## How-To

* put some configuration file in `files/`
* write an inventory file like described below
* fill your host vars like below
* put your Confluence credentials in `vars/private.yml` (ideally being a Vault)

`play.yml` is an example how putting stuff into confluence would work.

### inventory example

```
localhost ansible_connection=local
foo-sw01
foo-sw02
bar-sw01

[alcatel_switches]
foo-sw01
foo-sw02
bar-sw01
```

### hostvars example

```
jumphost: localhost
swname: foo-sw01
confluence_page: 13374223
```

### private.yml example

```
confluence:
  url: "https://localhost/confluence"
  user: maxmuster
  password: passw0rd
```

## TODO

* make `confluence_edit_code` idempotent and note changes
* change example playbooks to run on ansible connection of network type
