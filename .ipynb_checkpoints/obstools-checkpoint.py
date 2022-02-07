import json, os, sys
from pathlib import Path
# import networkx as nx
from copy import deepcopy
import datetime

def printd(dictionary: dict) -> None:
    for key, value in dictionary.items():
        print(str(key)+":",value)

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

def get_names_to_paths(inp) -> dict:
    """    
    Returns a dictionary that maps each .md filename to its paths,
    since there exists the possibility of collisions within the vault,
    i.e. different paths with the same .md filename.
    
    Note: filenames contain their suffixes.
    
    @param inp: either string vault directory or all_paths dictionary
    if string, then get_all_paths method will be used.
    """
    if type(inp) is str:
        inp = get_all_paths(inp)
    # now inp must be all_paths dictionary
    out = dict()
    for p in inp:
        if p.suffix == ".md":
            try: 
                out[p.name].add(p)
            except KeyError:
                out[p.name] = set([p])
    return out

def get_note_content(note_path):
    pass

def get_names_to_links(inp, errors = "replace", non_md_filetypes={".jpg", ".png", ".css"}) -> list:
    """
    Returns a pair
    - out[0] is a dict which maps each filename to its own dictionary d, 
    and d maps the filenames of the links present within the file to their display texts. 
    - out[1] is a list of filenames where errors occurred when trying to call file.read()
    
    Note: links 
    
    @param inp: either a string vault directory or a names_to_paths dictionary
    if a string, get_names_to_paths method will be used.
    
    @param errors: option to pass to open(., errors = ...) to handle errors when reading
    """
    if type(inp) is str:
        inp = get_names_to_paths(inp) 
    # now inp must be names_to_paths dictionary
    out = dict()
    err = dict()
    for key, values in inp.items():
        path = Path(list(values)[0])
        read_path = False
        try:
            with open(path, 'r', errors=errors) as ofile:
                text = ofile.read()
            d = dict()
            for i in text.split("[["):
                if "]]" in i:
                    i = i[:i.find("]]")]
                    if "|" in i: # then we used display text
                        k = i.split("|") # now k is a list of link args, the first should
                        # be the filename, the second the display text, the third etc.? nevermind them
                        suffix = k[0][::-1][:k[0][::-1].find(".")+1][::-1]
                        try:
                            if suffix == "":
                                d[k[0] + ".md" if not suffix in non_md_filetypes else ""].add(k[1])
                        except KeyError: 
                            d[k[0] + ".md" if not suffix in non_md_filetypes else ""] = set([k[1]])
                    elif not i in d: # then we didn't use display text, and the filename isn't in our
                        # dictionary yet, so we can put it in (if it was in, we do nothing)
                        suffix = i[::-1][:i[::-1].find(".")+1][::-1]
                        d[i + ".md" if not suffix in non_md_filetypes else ""] = set()
            out[key] = d
        except Exception as e:
            err[key] = e
    return [out,err]

def get_all_md_filenames(inp) -> list:
    """
    Returns a list of all filenames that end in .md
    
    @param inp: either a string vault directory or a all_paths dictionary
    if a string, get_all_paths method will be used.
    """
    if type(inp) is str:
        inp = get_all_paths(inp)
    out = list()
    for p in inp:
        if str(p).count(".md") == 1 and p.suffix == ".md":
            out.append(p)
    return out

def convert_dict_of_sets_to_dict_of_lists(dictionary):
    """
    Returns the same dictionary, but the values being sets are now lists
    
    @param dictionary: {key: set(), ...}
    """
    out = dict()
    for key, setvalue in dictionary:
        out[key] = list(setvalue)
    return out

def produce_json_of_vault(vault_dir, json_filename="", do_dump = False) -> dict:
    """
    Returns a triple
    - out[0] is the json-valid dictionary for us
    - out[1] is any errors during the get_names_to_links method, i.e., when file-reading
    - out[2] is any error while dumping, is None if no error or no dumping
    
    @param vault_dir: string vault dictionary
    @param json_filename (optional): string filename to do the dumping in
    @param do_dump (optional): bool option to do json.dump
    
    Note: if json_filename is not given, then do_dump is forcefully set to False
    """
    names_to_links_pair = get_names_to_links(vault_dir)
    errors = names_to_links_pair[1]
    names_to_links = names_to_links_pair[0] # names_to_links dictionary
    out = dict()
    error_when_dumping = None
    # convert all sets to lists for json compatibility
    for filename, dict_of_links_to_aliases in names_to_links.items():
        out[filename] = convert_dict_of_sets_to_dict_of_lists(dict_of_links_to_aliases)
    if json_filename == "":
        do_dump = False
    if do_dump:
        try:
            with open(json_filename, 'w') as ofile:
                json.dump(out, ofile)
        except Exception as e:
            error_when_dumping = e
    return [out,errors,error_when_dumping]

def get_names_to_aliases(inp) -> dict:
    """
    Returns pair,
    - out[0] = dictionary of names to sets of aliases
    - out[1] = erros when calling names_to_links, i.e., when file-reading
    
    @param inp: string vault directory or names_to_links dictionary
    if string then get_names_to_links method is used
    """
    if type(inp) is str:
        inp = get_names_to_links(inp)
    # now inp must be names_to_links_pair
    out = dict()
    for filename, dict_links_to_aliases in inp[0].items():
        for link_filename, set_of_aliases in dict_links_to_aliases.items():
            try:
                out[link_filename].update(set_of_aliases)
            except KeyError:
                out[link_filename] = set(set_of_aliases)
    return [out,inp[1]]    

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

def walk_around(dictionary: dict) -> list:
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