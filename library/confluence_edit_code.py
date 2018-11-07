#!/usr/bin/env python3
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url, url_argument_spec

import json
import re

def replace_content(c,insert,start_pattern,end_pattern):
    code_start=re.search(start_pattern,c,re.MULTILINE)
    if not code_start:
        return False
    code_end=re.search(end_pattern,c[code_start.end():],re.MULTILINE)
    if not code_end:
        return False
    return c[:code_start.end()]+insert+c[code_end.start()+code_start.end():]


def main():
    arg_spec = url_argument_spec()
    arg_spec.update(dict(
        url=dict(required=True),
        url_username=dict(type='str', aliases=['user']),
        url_password=dict(type='str', aliases=['password'], no_log=True),
        re_start=dict(type='str',required=True),
        re_end=dict(type='str',required=True),
        # maybe default="<ac:plain-text-body><![CDATA[!" and "^]]>" ?
        page_id=dict(type='str',required=True),
        ignore_whitespace=dict(type='bool', default=False),
        msg=dict(type='str',
            default="Beep. Auto update by thotos Ansible module. Boop."),
        data=dict(type='str'),
        ))
    module = AnsibleModule(argument_spec=arg_spec,supports_check_mode=True)
    changed = False

    code_diff=(lambda x, y: re.sub('[ \n\t]','',x) != re.sub('[ \n\t]','',y)) \
            if module.params['ignore_whitespace'] else \
            (lambda x, y: x != y)

    base_url = "%s/rest/api/content/%s"%(module.params['url'],
            module.params['page_id'])
    if 'user' in module.params:
        module.params['force_basic_auth']=True
    resp, info = fetch_url(module,base_url+"?expand=body.storage,version",
            method="GET")

    if info['status']!=200:
        module.fail_json(msg="could not find content")

    try:
        res = resp.read()
    except AttributeError:
        res = info.pop('body', '')

    try:
        a = json.loads(res)
        b = a['body']['storage']['value']
    except:
        module.fail_json(msg="invalid response from API")

    data=module.params['data'] \
        if 'data' in module.params and module.params['data'] \
        else 'foo'

    c = replace_content(b, data, module.params['re_start'],
            module.params['re_end'])

    if not c:
        module.fail_json(msg="section could not be found")

    if code_diff(c, b):
        changed = True

    if code_diff(c, b) and not module.check_mode:
        p_body = json.dumps({
            'id': module.params['page_id'], 'title': a['title'], 'type': 'page',
            "body":{"storage":{"value":c,"representation":"storage"},},
            "version":{"number": a['version']['number']+1,
                "message": module.params['msg']}
            })

        p_resp,p_info = fetch_url(module, base_url, method="PUT",
            data=p_body, headers={'Content-Type':"application/json"})

        if info['status'] != 200:
            module.fail_json(msg="update content failed. status:"+str(
                info['status']), info=info, resp=resp)

    module.exit_json(msg=c,changed=changed)


if __name__ == '__main__':
    main()
