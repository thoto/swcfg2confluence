#!/usr/bin/env python3
from ansible.module_utils.basic import AnsibleModule
import re
import collections

def deep_update(o, n):
    for k in n.keys():
        if isinstance(n[k], collections.Mapping) and \
                k in o and isinstance(o[k], collections.Mapping):
            o[k]=deep_update(o.get(k,{}), n[k])
        elif isinstance(n[k], collections.Sequence) and \
                k in o and isinstance(o[k], collections.Sequence):
            o[k]=o[k]+n[k]
        else:
            o[k]=n[k]
    return o

def push_port(ports,port,data):
    if str(port) not in ports:
        ports[str(port)]={}
#        ports[str(port)]={"name":"",
#                "vlan": {"pvid": 1, "dot1q":[], "gvrp": False}}
    deep_update(ports[str(port)],data)
    # ports={**ports,**{str(port):data}}

def main():
    module = AnsibleModule(argument_spec=dict(
        config=dict(type='str', aliases=['data'], required=True),))

    config=module.params['config']

    props={"vlans":{}}
    ports={}

    per_port_matches = [
        # port name
        ("interfaces (\d/\d+) alias \"(.*)\"",
            lambda e: (e.group(1),{"name":e.group(2)})),
        # vlan dot1q tag
        ("vlan (\d+) 802.1q (\d/\d+)",
            lambda e: (e.group(2),{"vlan":{"dot1q":[str(e.group(1))]}})),
        # vlan PVID
        ("vlan (\d+) port default (\d/\d+)",
            lambda e: (e.group(2),{"vlan":{"pvid":str(e.group(1))}})),
        # vlan PVID
        ("gvrp port (\d/\d+)",
            lambda e: (e.group(1),{"vlan":{"gvrp":True}})),
        ]

    global_matches = [
        # vlan name
        ("vlan (\d+) enable name \"(.*)\"",
            lambda e: {"vlans":{str(e.group(1)):e.group(2)}}),
        ("bridge mode flat",
            lambda e: {"gvrp_stp": True}),
        ("vlan registration-mode gvrp",
            lambda e: {"gvrp_reg": True}),
        ("gvrp",
            lambda e: {"gvrp_enabled":True}),
        ]

    per_port_matches_c=[(re.compile(r"^\s*"+i+""),j) \
            for (i,j) in per_port_matches]
    global_matches_c=[(re.compile(r"^\s*"+i+"\s*$"),j) \
            for (i,j) in global_matches]

    for l in config.splitlines():
        for (m,f) in per_port_matches_c:
            e = m.match(l)
            if e:
                push_port(*((ports,)+f(e)))
        for (m,f) in global_matches_c:
            e = m.match(l)
            if e:
                deep_update(props,f(e))

    module.exit_json(ansible_facts={"switch_config":{"ports":ports,
        "props":props}})


if __name__ == '__main__':
    main()
