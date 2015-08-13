import os
import logging

class MLogger(object):

    def __init__(self, name, filename, log_dir):
        try:
            os.makedirs(log_dir)
        except FileExistsError:
            pass
        self.__logger = logging.getLogger(name)
        self.__logger.setLevel(logging.DEBUG)
        self.__log_handler = logging.FileHandler(os.path.join(log_dir, filename + ".log"))
        self.__log_formatter = logging.Formatter(
            '%(asctime)s;%(name)s;%(levelname)s;%(message)s')
        self.__log_handler.setFormatter(self.__log_formatter)
        self.__logger.addHandler(self.__log_handler)

    def __del__(self):
        self.__logger.removeHandler(self.__log_handler)

    def debug(self, msg):
        return self.__logger.debug(msg)

    def info(self, msg):
        return self.__logger.info(msg)

    def warning(self, msg):
        return self.__logger.warning(msg)

    def error(self, msg):
        return self.__logger.error(msg)
