"""给MyETcp调用，储存节点报错的警告"""
import time

__DICT_UDP_TYPE = {"m": 0, "w": 1, "e": 2}


class EMessage:
    def __init__(self, str_jb, int_jb_id):
        global __DICT_UDP_TYPE
        self.int_jb = __DICT_UDP_TYPE[str_jb]
        self.int_jb_id = int_jb_id
        self.double_time = time.time()
