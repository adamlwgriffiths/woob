import csv
import re
from typing import Set, List, Dict, Tuple

def flatten_dict(d):
    def _flatten(d, path=''):
        for key, value in d.items():
            if isinstance(value, dict):
                yield from _flatten(value, f'{path}{key}.')
            else:
                yield f'{path}{key}', value
    return dict(_flatten(d))

def relative_merge(l1, l2):
    '''Merge 2 lists, preserving the relative order,

    Eg:
        ([1, 2, 3, 4], [1, 2, 5]) -> [1, 2, 3, 5, 4]
        ([1, 2, 3, 4], [1, 2, 5, 3, 4]) -> [1, 2, 5, 3, 4]
    '''
    s1 = set(l1)
    s2 = set(l2)
    out = []

    def take_both(l1, l2):
        out.append(l1[0])
        l1.pop(0)
        l2.pop(0)
    def take_left(l1, l2):
        out.append(l1[0])
        l1.pop(0)
    def take_right(l1, l2):
        out.append(l2[0])
        l2.pop(0)

    while l1 and l2:
        v1, v2 = l1[0], l2[0]

        # both match
        if v1 == v2:
            # add to list
            # trim both
            take_both(l1, l2)
        # v1 and v2 are divergent
        elif v1 in s2:
            # v1 is in l2
            # v2 is the new value
            take_right(l1, l2)
        elif v2 in s1:
            # v2 is in l1
            # v1 is the new value
            take_left(l1, l2)
        else:
            # neither are common
            take_left(l1, l2)
            take_right(l1, l2)

    if l1:
        out.extend(l1)
    if l2:
        out.extend(l2)

    return out

assert relative_merge([1, 2, 3, 4], [1, 2, 5]) == [1, 2, 3, 5, 4]
assert relative_merge([1, 2, 3, 4], [1, 2, 5, 3, 4]) == [1, 2, 5, 3, 4]

def to_table(data: List[Dict]) -> Tuple[List, List]:
    if not isinstance(data, list):
        data = [data]

    # get the full fieldnames
    fieldnames = []
    for obj in data:
        fieldnames = relative_merge(fieldnames, list(obj.keys()))

    # recreate the objects so they have all the fields
    rebuilt_data = []
    for obj in data:
        new_obj = {}
        for field in fieldnames:
            new_obj[field] = obj.get(field, None)
        rebuilt_data.append(new_obj)

    return fieldnames, rebuilt_data


def create_field_regex(fieldname_whitelist):
    def to_regex(fieldname):
        # x.y.z -> x\.y\.z
        fieldname = fieldname.replace('.', r'\.')
        # x\.y\.* -> x\.y\..*
        fieldname = fieldname.replace('*', r'.*')
        return fieldname

    # convert our whitelist into a regex
    field_re_str = '|'.join([to_regex(fieldname) for fieldname in fieldname_whitelist])
    field_re = re.compile(field_re_str)
    return field_re

def apply_field_regex(regex, obj: dict, whitelist=True) -> dict:
    obj = {**obj}
    for key in list(obj.keys()):
        if whitelist:
            if not regex.fullmatch(key):
                del obj[key]
        else:
            if regex.fullmatch(key):
                del obj[key]
    return obj
