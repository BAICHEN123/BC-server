import time
import traceback


def e_print(e, str1=None, tuple_data=None):
    print(
        time.strftime("%Y-%m-%d %H:%M:%S  error  ", time.localtime()),
        " file=",
        e.__traceback__.tb_frame.f_globals["__file__"],  # 出现异常的代码文件
        " line=",
        e.__traceback__.tb_lineno,  # 出现异常的代码的行数
        " line=",
        e.__traceback__.tb_lineno,  # 出现异常的代码的行数
        end="",
    )
    if str1 != None:
        print("	", str1, "	", end="")
    if tuple_data != None:
        print(tuple_data, end="")
    print(e, e.with_traceback, traceback.format_exc())  # except obj  # except obj.name


def log_print(str1=None, tuple_data=None):
    print(time.strftime("%Y-%m-%d %H:%M:%S  mylog  ", time.localtime()), end=" ")
    if str1 != None:
        print("	", str1, "	", end="")
    if tuple_data != None:
        print(tuple_data, end="")
    print("")
