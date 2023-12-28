#!/usr/bin/python3
import ctypes
import os, platform

__dir, __file = os.path.split(os.path.realpath(__file__))
if platform.system() == "Linux":
    dll1 = ctypes.cdll.LoadLibrary(__dir + "/libkeyer.so")
else:
    dll1 = ctypes.CDLL(__dir + "\\keyer.dll")

del __dir
del __file


def keyer_str_get_bytes(str_key, str_data1):
    bytes_data1 = str_data1.encode()
    char_p = ctypes.create_string_buffer(bytes_data1, len(bytes_data1))
    bytes_key_char_p = str_key.encode()
    # chars='bb bbbbbbbb'.encode()#为 char* 变量 指向的容器填充/为字符数组赋值
    # print(id(chars))
    ret1 = dll1.my_dll2(
        char_p, len(char_p), bytes_key_char_p, len(bytes_key_char_p)
    )  # 调用dll里的函数
    if ret1 == len(char_p.raw):
        # print("成功")
        # print(char_p.raw)
        return char_p.raw
    else:
        print("keyer.dll加密失败", ret1)
        print(char_p.raw)
        return 0


def keyer_bytes_get_str(str_key, bytes_data1):
    # print(bytes_data1)
    char_p = ctypes.create_string_buffer(
        bytes_data1, len(bytes_data1)
    )  # 新建一个C语言的 char* 变量
    bytes_key = str_key.encode()
    ret1 = dll1.my_dll2(char_p, len(char_p), bytes_key, len(bytes_key))  # 调用dll里的函数
    if ret1 == len(bytes_data1):
        # print("成功")
        # print(char_p.raw)
        # print(char_p.raw.decode())
        try:
            return char_p.raw.decode()
        except UnicodeDecodeError:
            try:
                return char_p.raw.decode("gbk")
            except UnicodeDecodeError:
                return 0
    else:
        # print("失败")
        print("keyer.dll解密失败", ret1)
        print(bytes_data1)
        return 0
