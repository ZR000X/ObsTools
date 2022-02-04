def get_mapping_from_json(job):
    o = dict()
    for name, links in job.items():
        valid_link_names = set()
        for link in links:
            if link in job:
                valid_link_names.add(link)
        o[name] = valid_link_names
    return o

def reduce_to_cycles(dictionary, cont=True):
    """
    Reduces the dictionary object to be only those items that are involved in cycles
    
    cont: remove self-referencing
    """
    def helper(d):
        if type(d) is dict:
            d1 = deepcopy(d)
            o = False
            for key, values in d.items():
                if len(values) == 0:
                    for key0, values0 in d1.items():
                        if key in values0:
                            values0.remove(key)
                    d1.pop(key)
                    o = True
            return [d1,o]
        elif type(d) is list:
            return helper(d[0])
    dictionary = helper(dictionary)
    while dictionary[1]:
        dictionary = helper(dictionary)
    dictionary = dictionary[0]
    if not cont:
        return dictionary
    for key, values in dictionary.items():
        if key in values:
            values.remove(key)
    return reduce_to_cycles(dictionary, False)