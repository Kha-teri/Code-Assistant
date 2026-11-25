import json


def p(d, f):
    r = []
    for x in d:
        if x[2] > 86400:
            try:
                r.append((x[0], x[1] * 1.23))
            except:
                pass
    with open(f, "w") as h:
        json.dump(r, h)
    return len(r)
