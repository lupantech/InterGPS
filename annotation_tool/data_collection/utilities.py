import os

def listdir_(path):
    return [f for f in sorted(os.listdir(path), reverse=True) if not f.startswith('.')]

def find_num(name, data_path):
    dir = os.path.join(data_path)
    dirs = listdir_(dir)

    if name in dirs:
        return len(dirs)-dirs.index(name)
    else:
        return -1
