import os, re, time
import threading
from datetime import datetime
import MyPrintE

"""
检查 ota_dir_name 变量指定的文件夹下的节点编译文件，根据节点代码中定义的 OTA_SERVER_FIND_TAG 在编译后的数据判断对应使用该代码的节点是否需要更新。

"""


# ok_bin_name = re.compile("\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}-.+.bin")
re_bin_data = re.compile(
    "__DATE__([a-zA-Z\d]{3} \d{2} \d{4})__TIME__([:\d]{8})__FILE__(.+)"
)


# __DATE__Feb 24 2024__TIME__15:01:00__FILE__new_temperature.ino
def make_dir_path(str_path) -> bool:
    if os.path.exists(str_path) == False:
        os.makedirs(str_path)
    elif os.path.isdir(str_path) == False:
        MyPrintE.log_print(
            "error 无法创建{str_path}", line=MyPrintE.get_line().f_lineno, file_name=__file__
        )
        return False
    return True


def move_file_to_dir(file_name, dir_name):
    if os.path.exists(file_name) == False:
        print(f"error {file_name} 文件不存在")
        return False
    if os.path.exists(dir_name) == False and make_dir_path(dir_name) == False:
        print(f"error {dir_name} 新建失败")
        return False
    if os.path.exists(dir_name) and os.path.isdir(dir_name):
        file_name_list = os.path.split(file_name)
        out_file_name = os.path.join(dir_name, file_name_list[1])
        if os.path.exists(out_file_name):
            print(f"error {out_file_name} 文件已经存在")
            return False
        os.replace(file_name, out_file_name)
        return os.path.exists(out_file_name)
    MyPrintE.log_print(
        f"error {dir_name} 目录不是个文件夹", line=MyPrintE.get_line().f_lineno, file_name=__file__
    )
    return False


class ReadOTABin:
    def __init__(self, file_name, ok_path=None) -> None:
        self.ok_file_name = None
        if ok_path == None:
            self.read_ok_name(file_name)
            return
        self.ok_file_name = os.path.split(file_name)[1]
        self.ok_path = file_name
        self.file_size = os.path.getsize(self.ok_path)

    def is_bin(self)->bool:
        return self.ok_file_name != None

    def read_ok_name(self, file_name):
        global re_bin_data
        f = open(file_name, "rb")
        bytes1 = f.read()
        f.close()
        self.file_size = len(bytes1)
        start_id = bytes1.find("__DATE__".encode())
        if start_id < 1:
            return
        end_id = bytes1.find("__END__".encode(), start_id)
        bytes_data = bytes1[start_id:end_id]
        # __DATE__Feb 24 2024__TIME__15:01:00__FILE__new_temperature.ino
        str_data = bytes_data.decode()
        end = re_bin_data.findall(str_data)
        if end == None or len(end) == 0:
            return
        end = end[0]
        if end != None and len(end) == 3:
            datetime1 = datetime.strptime(end[0], "%b %d %Y")
            str_datetime = datetime1.strftime("%Y-%m-%d")
            str_time = end[1].replace(":", "-")
            self.e_type_name = end[2]
            self.ok_file_name = f"{str_datetime}-{str_time}-{self.e_type_name}.bin"
            self.ok_path = os.path.join(os.path.split(file_name)[0], self.ok_file_name)

    def get_bin_bytes(self):
        # 一个bin才333kb
        f = open(self.ok_path, "rb")
        bytes1 = f.read()
        f.close()
        return bytes1
    def __str__(self) -> str:
        if self.is_bin():
            return  f"{self.__class__}(bin={self.ok_path}) "
        return super().__str__() 
    def __repr__(self) -> str:
        if self.is_bin():
            return  f"{self.__class__}(bin={self.ok_path}) "
        return super().__repr__() 
    


ota_dir_name = "./OTAFile"
ota_e_tag = ["esp8266", "test"]
__dict_tag = dict()


class Thread_init_ota(threading.Thread):
    # def __init__(self):
    def run(self):
        init_ota()


def thread_init_ota():
    a = Thread_init_ota()
    a.start()
    return a


def init_ota():
    try:
        flush_ota_dir()
        while os.system("""inotifywait -r -e "close_write,create,delete" ./OTAFile """) == 0:
            time.sleep(1)
            flush_ota_dir()
    except KeyboardInterrupt as e:
        pass


def is_need_updata(tag, OTA_SERVER_FIND_TAG):
    if tag not in __dict_tag:
        return None
    # __DATE__Feb 24 2024__TIME__15:01:00__FILE__new_temperature.ino
    str_data = OTA_SERVER_FIND_TAG
    if str_data.endswith("__END__"):
        str_data = str_data[: -(len("__END__"))]
    end = re_bin_data.findall(str_data)
    if end == None or len(end) == 0:
        return None
    end = end[0]
    if end == None or len(end) != 3:
        return None

    datetime1 = datetime.strptime(end[0], "%b %d %Y")
    str_datetime = datetime1.strftime("%Y-%m-%d")
    str_time = end[1].replace(":", "-")
    e_type_name = end[2]
    if e_type_name not in __dict_tag[tag]:
        return None
    ok_file_name = f"{str_datetime}-{str_time}.bin"
    file_obj = __dict_tag[tag][e_type_name]
    assert type(file_obj) == ReadOTABin
    if ok_file_name > file_obj.ok_file_name:
        return None
    return file_obj


def file_e_type_re(e_type, file_name):
    ok_bin_name = re.compile("\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}-" + e_type + ".bin")
    return ok_bin_name.match(file_name) != None

def get_e_type_dir_dict(e_type_path,e_type,mode=None) -> dict:
    dict_all_bin = dict() 
    list_e_type_dir = os.listdir(e_type_path)
    for e_type_file in list_e_type_dir:
        e_type_file_full = os.path.join(e_type_path, e_type_file)
        # print(e_type_file_full)
        if mode == None and file_e_type_re(e_type, e_type_file):
            a = ReadOTABin(e_type_file_full, e_type_file_full)
            dict_all_bin[a.ok_file_name] = a
            continue
        a = ReadOTABin(e_type_file_full)
        if a.is_bin() == False:
            MyPrintE.log_print(
                f"{e_type_file_full} 文件无法正常读取",
                line=MyPrintE.get_line().f_lineno,
                file_name=__file__,
            )
            continue
        if a.e_type_name != e_type:
            MyPrintE.log_print(
                f"{e_type_file_full} 文件位置错误,rm ,e_type{e_type} e_type_name{a.e_type_name}",
                line=MyPrintE.get_line().f_lineno,
                file_name=__file__,
            )
            os.remove(e_type_file_full)
            continue

        MyPrintE.log_print(
            f"mv {e_type_file_full} {a.ok_path}",
            line=MyPrintE.get_line().f_lineno,
            file_name=__file__,
        )
        if a.ok_path == e_type_file_full:
            continue
        elif os.path.exists(a.ok_path):
            MyPrintE.log_print(
                f"{a.ok_path} 编译日期相同，删掉改过名的",
                line=MyPrintE.get_line().f_lineno,
                file_name=__file__,
            )
            os.remove(a.ok_path)
        os.replace(e_type_file_full, a.ok_path)
        dict_all_bin[a.ok_file_name] = a 
    return dict_all_bin


def flush_ota_dir(mode=None):
    if os.path.exists(ota_dir_name) == False:
        make_dir_path(ota_dir_name)
    elif os.path.isdir(ota_dir_name) == False:
        MyPrintE.log_print(
            f"{ota_dir_name}存在且不是文件夹,程序结束",
            line=MyPrintE.get_line().f_lineno,
            file_name=__file__,
        )
        exit(1)

    for item in ota_e_tag:
        e_tag_path = os.path.join(ota_dir_name, item)
        if os.path.exists(e_tag_path) == False:
            make_dir_path(e_tag_path)
        elif os.path.isdir(e_tag_path) == False:
            MyPrintE.log_print(
                f"{e_tag_path}存在且不是文件夹,需要删除",
                line=MyPrintE.get_line().f_lineno,
                file_name=__file__,
            )
            continue
        # 允许向e_type目录下直接放bin文件，并根据bin文件内容放到对应位置
        list_dir1 = os.listdir(e_tag_path) 
        for e_type in list_dir1:
            e_type_path = os.path.join(e_tag_path, e_type)
            if os.path.isfile(e_type_path) == False:
                continue 
            a = ReadOTABin(e_type_path)
            if a.is_bin() == False:
                continue 
            #先改名，后创建对应的目录
            os.replace(e_type_path, a.ok_path)
            mv_to_dir = os.path.join(e_tag_path,a.e_type_name)
            move_file_to_dir(a.ok_path,mv_to_dir)
            a.ok_path = os.path.join(mv_to_dir,a.ok_file_name) 
        list_dir1 = os.listdir(e_tag_path) 
        dict_new_bin = dict()
        for e_type in list_dir1:
            e_type_path = os.path.join(e_tag_path, e_type)
            if os.path.isdir(e_type_path) == True: 
                dict_all_bin = get_e_type_dir_dict(e_type_path,e_type,mode)
                if len(dict_all_bin) == 0:
                    continue
                list_end = list(dict_all_bin.keys())
                list_end.sort()
                new_bin = dict_all_bin[list_end[-1]]
                dict_new_bin[e_type] = new_bin
        __dict_tag[item] = dict_new_bin
    print(__dict_tag)


if __name__ == "__main__":
    init_ota()
