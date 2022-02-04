import json, os, sys
from pathlib import Path
import networkx as nx
from copy import deepcopy
import datetime

def journal_make_days(date0: datetime.date, date1: datetime.date) -> None:
    """
    From date0 to date1, will build each date's file with just the built text.
    """
    day = datetime.timedelta(days=1)
    date = date0
    
    # make every day's file
    while date <= date1:
        # validate file name
        filename = str(date)[:4]+"/"+str(date)[:-3]+"/"+str(date)+".md"
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        # build file's initial text
        text = "# "+str(date)+"\n"
        text += "[["+str(date-day)+"|Yesterday]] and [["+str(date+day)+"|Tomorrow]]"+"\n"
        # text += "\n"+"[[120 Avenues of Support|SUPPORT THE SITE <3]]" 
        # print file and next loop
        print(text,file=open(filename,'w'))
        date = date + day
 
def get_all_paths(vault_dir) -> list:
    """
    Packages: pathlib
    
    Returns a list of all pathlib.Path's in a given directory. Uses recursion. 
    """
    try:
        vault_dir = Path(vault_dir)
    except:
        return "Invalid path given: " + str(vault_dir)
    if vault_dir.is_file():
        return vault_dir    
    o = list()
    it = vault_dir.iterdir()
    if it is not None:
        for i in it:
            if i.is_file():
                o.append(Path(i))
            else:
                ex = get_all_paths(i)
                if ex is not None:
                    for e in ex:
                        o.append(Path(e))
    return o

def get_names_to_paths(all_paths) -> dict:
    """
    Packages: pathlib.Path
    
    Returns a dictionary that maps each .md filename to its paths.
    
    all_paths: list of Path's
    """
    o = dict()
    for p in all_paths:
        p = Path(p)
        if p.suffix == ".md":
            try: 
                o[p.name].add(p)
            except KeyError:
                o[p.name] = set([p])
    return o

def get_names_to_links(names_to_paths) -> list:
    """
    Returns a pair [o,e]
    o is a dict which maps each filename to its own dictionary d, and d maps the filenames of the links present within the file to their display texts. 
    e is a list of filenames where errors occurred when trying to call file.read()
    """
    o = dict()
    e = dict()
    for key, values in names_to_paths.items():
        path = Path(list(values)[0])
        read_path = False
        try:
            with open(path, 'r', errors='replace') as ofile:
                text = ofile.read()
            d = dict()
            for i in text.split("[["):
                if "]]" in i:
                    i = i[:i.find("]]")]
                    if "|" in i:
                        k = i.split("|")
                        try: d[k[0]+".md"].add(k[1])
                        except KeyError: d[k[0]+".md"] = set([k[1]])
                    elif not i in d:
                        d[i+".md"] = set()
            o[key] = d
        except Exception as err:
            e[key] = err
    return [o,e]

def get_all_notes(all_paths) -> list:
    o = list()
    for p in all_paths:
        if str(p).count(".md") == 1 and p.suffix == ".md":
            o.append(p)
    return o

def produce_json_of_vault(vault_dir, json_filename) -> dict:    
    all_paths = get_all_paths(vault_dir)
    names_to_paths = get_names_to_paths(all_paths)
    names_to_links = get_names_to_links(names_to_paths)
    errors = names_to_links[1]
    diction = names_to_links[0]
    o = dict()
    for i, d in diction.items():
        p = dict()
        for j, s in d.items():
            p[j] = list(s)
        o[i] = p
    with open(json_filename, 'w') as ofile:
        json.dump(o, ofile)
    return errors

def get_names_to_valid_links_from_file(json_filename):
    with open(json_filename, 'r') as ofile:
        names_to_links = json.load(ofile)
    o = dict()
    for name, links in names_to_links.items():
        valid_link_names = set()
        for link in links:
            if link in names_to_links:
                valid_link_names.add(link)
        o[name] = valid_link_names
    return o

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

def get_backlinks(dictionary):
    """
    Returns a reversed self-mapped dictionary
    
    @param dictionary: the forwardlinks
    """
    o = dict()
    for key, values in dictionary.items():
        try:
            for v in values:
                try:
                    o[v].add(key)
                except KeyError:
                    o[v] = {key}
        except TypeError as te:
            try:
                o[values].add(key)
            except KeyError:
                o[values] = {key}        
    return o

def is_self_mapping_dict(dictionary) -> bool:
    """
    Is the mathematical definition of a self mapping dictionary
    """
    for key, values in dictionary.items():
        for i in values:
            if not i in dictionary:
                return False
    return True

def force_dict_to_be_self_mapping(dictionary, copy=True) -> dict:
    """
    Will reduce the dictionary minimally to ensure it is self-mapping
    """
    if copy:
        o = dict()
        for key, values in dictionary.items():
            for value in values:
                if value in dictionary:
                    try:
                        o[key].add(value)
                    except KeyError:
                        o[key] = {value}
        return o
    new_dict = deepcopy(dictionary) # makes a fresh, separate copy
    for key, values in new_dict.items(): # iterate through the copy
        for value in values:
            if not value in new_dict:
                dictionary.pop(key) # pop it from the original dictionary
    return new_dict

def walk_around(dictionary: dict):
    """
    Will produce a list of paths in the entire digraph-as-dict that either terminate as a cycle or
    when a leaf (no links) is reached.
    """
    def update_walks(dictionary: dict, walks: list) -> list:
        """
        Given a mapping dict, will update all given walks to their next position,
        as well as creating the new walks if a walk can go multiple ways
        """
        o = walks[:]
        for walk in walks:
            if len(dictionary[walk[-1]]) > 0:
                for next_step in dictionary[walk[-1]]:
                    o.append(walk[:]+[next_step])
                o.remove(walk)
        return o
    initial_walks = list() # build initial walks [[1], [2], ...] 
    for key in dictionary:
        initial_walks.append([key])
    busy_walking = update_walks(dictionary, initial_walks) # [[1,d1], [2,d2] ...]]
    final_walks = list() # will store walks that have terminated
    expected_length = 2 # after next update, will be 3
    walks_to_end = list() # will store walks for 
    while len(busy_walking) > 0:
        for walk in busy_walking:
            if len(walk) < expected_length or walk[-1] in walk[:-1]: # then it reached a leaf
                walks_to_end.append(walk)
        for walk in walks_to_end:
            final_walks.append(walk)
            busy_walking.remove(walk)
        walks_to_end = list()
        busy_walking = update_walks(dictionary, busy_walking)
        expected_length += 1
    return final_walks