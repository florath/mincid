#
# Class that holds a (raw) string and has a method
# to convert the string to one that can be used in a filesystem.
#

class RFSString(object):

    def __init__(self, s):
        self.__str = s

    def raw(self):
        return self.__str

    def fs(self):
        return self.__str.replace("/", "_").replace(":", "_")
    
