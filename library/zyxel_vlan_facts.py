#!/usr/bin/env python3
from ansible.module_utils.basic import AnsibleModule
import re
import collections

def port_list_expand(a):
    l=[]
    r=re.compile('^(\d+)-(\d+)$')
    for i in a.split(','):
        ft=r.match(i)
        if ft:
            l=l+range(int(ft.group(1)),int(ft.group(2))+1)
        else:
            l.append(i)
    return l


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


def main():
    module = AnsibleModule(argument_spec=dict(
        config=dict(type='str', aliases=['data'], no_log=True, required=True),))

    config=module.params['config']

    props={"vlans":{},"ports":{}}
    ports={}

    global_matches = [
        # vlan name
        ("vlan (\d+) name \"?(.*?)\"?",
            lambda e: {"vlans":{str(e.group(1)):e.group(2)}}),
        # gvrp vlan
        ("vlan (\d+) normal ([\d,-]+)",
            lambda e: {"ports":{str(x):
                {"vlan":{"dot1q_gvrp":[str(e.group(1))]}}
                for x in port_list_expand(e.group(2))}} ),
        # fixed vlan
        ("vlan (\d+) fixed ([\d,-]+)",
            lambda e: {"ports":{str(x):
                {"vlan":{"dot1q":[str(e.group(1))]}}
                for x in port_list_expand(e.group(2))}} ),
        # potential untagged vlan
        ("vlan (\d+) untagged ([\d,-]+)",
            lambda e: {"ports":{str(x):
                {"vlan":{"pvid_potential":[str(e.group(1))]}}
                for x in port_list_expand(e.group(2))}} ),
#        ("vlan (\d+) ip address default-management ([\d.]+) ([\d.]+)", ), #TODO
#        ("vlan (\d+) ip address ([\d.]+) ([\d.]+)", ), #TODO
#        ("vlan (\d+) ip address default-gateway ([\d.]+) ([\d.]+)", ), #TODO
        # vlan PVID
        ("interface port-channel (\d+) pvid (\d+)",
            lambda e: {"ports":{str(e.group(1)):
                {"vlan":{"pvid":str(e.group(2))}}}}),
        # vlan GVRP
        ("interface port-channel (\d+) gvrp",
            lambda e: {"ports":{str(e.group(1)): {"vlan":{"gvrp":True}}}}),
        ("interface port-channel (\d+) name \"?(.*?)\"?",
            lambda e: {"ports":{str(e.group(1)): {"name":e.group(2)}}}),
        ("vlan1q gvrp", lambda e: {"gvrp_enabled": True}),
        ]
    # TODO: frame-type tagged (in aos6 module too)
    # interface ... vlan-trunking?
    # lldp
    # dhcp snooping trust

    state_matches = [
            ("vlan (\d+)",1),
            ("interface port-channel (\d+)",1),
            ("interface vlan (\d+)",1),
            ("exit",-1),]

    global_matches_c=[(re.compile(r"^\s*"+i+"\s*$"),j) \
            for (i,j) in global_matches]

    state_matches_c=[(re.compile(r"^\s*"+i+"\s*$"),j) \
            for (i,j) in state_matches]

    prefixes=[]
    for l in config.splitlines():
        for (m,t) in state_matches_c:
            if m.match(l):
                if t>0:
                    prefixes.append(l.strip())
                elif t<0:
                    prefixes.pop()
                break
        else:
            for (m,f) in global_matches_c:
                e = m.match((" ".join(prefixes)+" "+l.strip()).strip())
                if e:
                    deep_update(props,f(e))

    ports=props['ports']
    props['ports']=None
    module.exit_json(ansible_facts={"switch_config":{"ports":ports,
        "props":props}})


if __name__ == '__main__':
    main()
