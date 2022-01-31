from pathlib import Path
from networkx import DiGraph
from copy import deepcopy

## METHODS

def get_all_paths(vd):
    try:
        vd = Path(vd)
    except:
        return "Invalid path given: " + str(vd)
    if vd.is_file():
        return vd    
    o = list()
    it = vd.iterdir()
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

def get_name_collisions(all_paths):
    all_names = list()
    o = list()
    for p in all_paths:
        o.append(p)
        continue
        if p.name in all_names:
            o.append(p.name)
        else:
            all_names.append(p.name)
    return o

def get_all_files_with(all_paths, suffixes):
    if type(suffixes) is str:
        suffixes = [suffixes]
    o = list()
    for p in all_paths:
        add = True
        for e in suffixes:
            if not e in p.suffixes:
                add = False
                break
        if add:
            o.append(p)
    return o

def get_all_notes(all_paths):
    o = list()
    for p in all_paths:
        if str(p).count(".md") == 1 and p.suffix == ".md":
            o.append(p)
    return o

## CLASSES

class ObsNote:
    def __init__(self, path, filt = set()):
        self.path = Path(path)
        self.text = None
        self.read_file = False
        self.filt = filt
        with open(self.path, 'r') as ofile:
            try:
                self.text = ofile.read()
                self.read_file = True
            except:
                pass
        self.links_to_refs = dict()
    
    def get_links_to_refs(self):
        if self.read_file:
            d = dict()
            for i in self.text.split("[["):
                if "]]" in i:
                    i = i[:i.find("]]")]
                    if "|" in i:
                        k = i.split("|")
                        key = k[0]
                        value = k[1]
                        exclude = False
                        for f in self.filt:
                            if key.endswith(f):
                                exclude = True
                                break
                        if not exclude:
                            key += ".md"
                            try: d[key].add(value)
                            except KeyError: d[key] = set([value])
                    elif not i in d:
                        exclude = False
                        for f in self.filt:
                            if i.endswith(f):
                                exclude = True
                                break
                        if not exclude:
                            d[i+".md"] = set()
            self.links_to_refs = d
            return d
        
    def __eq__(self, other):
        return isinstance(other, ObsNote) and self.name == other.name

class Vault:
    def __init__(self, vault_dir, root_filename = None):
        # load simple data
        self.vault_dir = Path(vault_dir)
        self.root_filename = None
        if not root_filename is None:
            self.root_filename = Path(root_filename)
        self.all_paths = get_all_paths(self.vault_dir)
        self.name_collisions = get_name_collisions(self.all_paths)
        self.all_note_paths = get_all_notes(self.all_paths)
        self.valid_content_notes = list()
        self.readable_note_paths = list()
        self.unreadable_note_paths = list()        
        self.names_to_paths = dict()
        self.no_collisions = True
        self.names_to_links = dict()
        self.names_to_names = dict()
        self.graph = DiGraph()

    def calc_readables(self):
        for n in self.all_note_paths:
            if str(n).count(".trash") == 0:
                no = ObsNote(n)
                if no.read_file:
                    self.readable_note_paths.append(n)
                else:
                    self.unreadable_note_paths.append(n)
    
    def calc_name_dict(self):
        for n in self.readable_note_paths:
            try: 
                self.names_to_paths[n.name].update([n])
                self.no_collisions = False
            except KeyError: 
                self.names_to_paths[n.name] = set([n])
    
    def calc_links(self):
        for n in self.readable_note_paths:
            try: 
                o = self.names_to_links[n.name]
            except KeyError:
                o = set()
            for i in ObsNote(n).get_links_to_refs():
                o.add(i)
            self.names_to_links[n.name] = o
    
    def calc_names(self):
        o = deepcopy(self.names_to_links)
        for key, values in self.names_to_links.items():
            for i in values:
                if not i in o:
                    o[key].remove(i)
        self.names_to_names = o     
    
    def load(self):
        self.calc_readables()
        self.calc_name_dict()
        self.calc_links()
        self.calc_names()
        self.graph = DiGraph(self.names_to_names)

# Test Code

# string_of_vault_directory = "insert path of vault"
# string_of_root_filename = "_HOME.md"
# v = Vault(string_of_vault_directory, string_of_root_filename)
# v.load()