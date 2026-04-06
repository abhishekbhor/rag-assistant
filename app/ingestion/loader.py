# This module is responsible for loading documents from a specified path. It reads the content of the file and returns it as a string. The default path is set to "data/docs.txt", but it can be modified to load documents from a different location if needed.
def load_documents(path="data/docs.txt"):
    with open(path, "r") as f:
        return f.read()