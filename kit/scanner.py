import os
import json
import storage
import utility
from sets import Set


# Utility functions for scanning include statements.
def has_pound(s):
    return s[0:1] == '#'


def has_kit(s):
    return s.find('<kit/') >= 0


def is_dependency(s):
    return has_pound(s) and has_kit(s)


# Parses kit include statement (as follows).
# '#include <kit/module/file.h>'  =>  'base/module/file.h'
# '#include <kit/file.h>'         =>  'base/file/file.h'
def extract_reference(s):
    main = s[s.find('kit/') + 4: s.find('>')]
    if main.count('/') == 0:
        main = main[0:main.find('.')] + '/' + main
    return main


# Extracts paths included in format: #include <kit/module/file.h>, which
# becomes "module/file.h".
def text_references(text):
    lines = text.split('\n')
    includes = filter(is_dependency, lines)
    return Set(map(extract_reference, includes))

# Wrapper for above.
def file_references(path):
    with open(path, 'r') as f:
        return text_references(f.read())

# Scans project sources and their dependencies recursively, returning
# a set of kit modules to include.
def directory_references(root):
    refs = Set()
    for path in utility.sources_under(root):
        refs |= file_references(path)
    return refs

# Wrapper for above, but with a locally indexed module.
def module_references(name):
    path = storage.module_path(name)
    return directory_references(path)

# Given references to files in the Kit module index, returns
# a set of required modules.
def deps_from_references(refs):
    ret = Set()
    for ref in refs:
        ret.add(ref.split('/')[0])
    return ret

# Shallow dependencies of kit project with root path.
def directory_dependencies(path):
    refs = directory_references(path)
    return deps_from_references(refs)

# Shallow dependencies of kit module in index with name.
def module_dependencies(name):
    path = storage.module_path(name)
    return directory_dependencies(path)


# Parses kit.meta without injecting defaults.
def directory_metafile_contents(path):
    path += '/kit.meta'
    if os.path.exists(path):
        f = open(path, 'r')
        text = f.read()
        try:
            return json.loads(text)
        except:
            print utility.color(" - ERROR: couldn't parse kit.meta", 'red')
            exit(1)
        f.close()
    else:
        return ''


# Checks for c++ files.
def contains_cpp(root):
    for path in utility.files_under(root):
        if path.endswith(('.cpp', '.cc', '.hh', '.cxx')):
            return True
    return False


# Scans kit.meta for json data. Required fields are set to their
# defaults if not otherwise specified.
def directory_metadata(path):
    data = {
        "author": 'unknown',
        "flags": '',
        "language": 'C',
        "commands": []
    }
    if contains_cpp(path):
        data['language'] += ' CXX'
    meta = directory_metafile_contents(path)
    data.update(meta)
    return data


# Current directory...
def metadata():
    return directory_metadata('.')


def has_main(root):
    for ext in ['c', 'cc', 'cpp', 'cxx']:
        if os.path.exists(root + '/sources/main.' + ext):
            return True
    return False


def recursive_module_dependencies(mod):
    path = storage.module_path(mod)
    return recursive_dependencies(path)


def recursive_dependencies(path):
    s1 = Set()
    s2 = Set(directory_dependencies(path))
    while len(s1) != len(s2):
        s1 = s2
        s2 = Set()
        for dep in s1:
            s2.add(dep)
            s2 |= recursive_module_dependencies(dep)
    return s2



