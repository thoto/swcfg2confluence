def sort_by_port(d):
    s={}
    x=[]
    for k,v in d.iteritems():
        stack,port=k.split('/',1)
        if int(stack) not in s:
            s[int(stack)]={}
        s[int(stack)][int(port)]=(k,v)

    for i in sorted(s.keys()):
        for j in sorted(s[i].keys()):
            x.append(s[i][j])
    return x


class FilterModule(object):
    def filters(self):
        return { 'sort_by_port' : sort_by_port }
