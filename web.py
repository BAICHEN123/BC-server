#!/usr/bin/python3
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
import socket
import threading
import re
import os
import time
import hashlib
import Mykeyer
import MyPrintE
import Blackip
import MySmtp
from Mymysql import Mymysql
from MySmtp import send_email_yanzhenma, init_email_passwd
from MyETcp import MyETcp
from MyETcp import DictTcp
import json
import sys

get_line = sys._getframe
print(get_line().f_lineno, __file__)
"""
目前问题/想法
//1	sql优化，没必要的链接使用之后就断开？
		连接池做好了，超时断链，需要的时候再连接
//2	tcp改造，关于设备的控制这里，需要长时间的网络请求，所以单线程的http服务器已经不能维持正常工作的，需要开多线程
	算是解决了一半吧，用了另一个类开启了多线程，但是没有线程锁，如果遇到造成过多的线程就尴尬了。
3->14.4	UDP 警报分级
4	防udp  http tcp欺骗包
//5	用户将自己的设备共享给其他用户 此功能实现了
//6	数据库重新封装起来 封装完毕，需要将他从http类中提取出来，单独建一个类，然后去测试

7	硬件清除所有绑定的用户，然后重新绑定
	目前进度：null

//8	用户请求的返回格式统一一下		返回结果和提示 不要再使用状态码做结果码

//9	在发送的指令里面添加随机数？作为验证回复的id
	偶尔出现数据重复的原因就是心跳包的数据是有效内容
	形况模拟：在用户向单片机发送get指令之后，心跳包发送，get返回值发送，导致了心跳包被当作get的数据包被接收，甚至两个包被杂糅在一起
	解决方案：	1、心跳包使用不用的内容
				2、每个指令发送时携带一个随机数用于辨认心跳包和指令结果
	目前进度：//还没搞，只是调整了心跳包的时间间隔，减少重复的出现次数
				2021年5月26日18点09分问题解决。在数据包的开头插入一个字节的数据作为状态的判断，出现了之前的问题，心跳包清除失败了。
		问题分析:recv 只是复制数据存到缓存里，无法区分包是什么时候发过来的，一次发送了多少个字节，这些东西我要自己处理
		解决方案：接收数据之前清除旧数据，新数据从'##'开始读取，非‘##’开头的数据全部舍弃
	又粘包了，初步怀疑是先收到指令包，后收到心跳包，两个包被合在了一起，但是并不是。
	查看日志后代码之后判定，是服务器代码逻辑问题。清除缓存的时候判定了链接是否被占用，导致清理函数里在判定的时候无法正常进入循环清理缓存

//10	dict_TCP 链接修改提取方式，实现并发时的阻塞
	提取的时候不要将 id 连带删除，留下标记变量，在和单片机通讯的函数里实现阻塞，
	2021年5月26日18点09分问题解决，将设备的tcp链接独立出去之后，在单个设备的类里实现函数在发送接受之前的阻塞

//11	把 dict_TCP 的对象单个tcp进行封装，每次修改 dict_TCP 里的存储结构就要重写全部的函数，实在是太累了
	将常用操作方式封装起来


//12	thread_send_email 写到Mysmtp文件里,不要在主文件里凑热闹了

//13	cpu100% 问题，没有找到单独挂起子进程的方法
		目前打算每个进程启动之前发送自己的pid号，然后结束的时候再发一次，看看那个不是一对就知道是那个线程出问题了
		这次查看日志发现 清洗线程 和 cpu100% 几乎同一时刻出现，

//14		节点之间的联动
		操作如下：
			1、节点检测到符合联动的信号
			2、节点对服务器进行 节点发起的通讯，发送联动信号
			3、服务器对联动进行检验，查看联动是否符合权限要求
			4、服务器向联动的另一个节点发送指令

//14.1	节点发起的通讯（节点之间的联动 前置任务1）
		由于服务器是持有很多的tcp链接，如果定时对每个tcp进行扫描延时就受限于服务器的扫描间隔。

		所以我计划如下：
			1、 节点先发 udp ，告知服务器我有话要对你说
			2、	服务器收到 udp 之后查找 udp 中提到的节点，然后 tcp 告知节点 请讲
			3、	节点收到 请讲 之后发送联动指令

//14.2	服务器的联动表
		内容：储存联动关系，用于联动关系的权限校验，指令的发送

//14.3	手机app的添加联动功能
		1、获取所有的设备、获取传感器信号、获取可操作指令
		2、联动页面设计

//14.4	udp 分包
		区别不同内容的udp包
		消息，警告，错误		mesg，warn，erro		m,w,e//只是用第一个字节来表示包的性质
		m:设备之间联动指令
		w:有传感器数据超出范围，给予设备绑定了的用户邮件警告
		e:设备异常，告知用户的同时向服务器留下日志

//14.5	节点之间的通讯
//14.5.1		我需要把 dict_TCP 移动并封装到 MyETcp.py 里，这样才能获取更方便的获取其他节点，并调用。
//14.5.2		迁移好了，直接调用就好了，好耶！！
		
//15		ip地址黑名单，有国外的ip来扫描我端口


自动定时备份数据库？
自动记录程序出错原因并重启程序？
ui或者网页控制台？qt？
"""

# 储存TCP链接的字典
dict_time = dict()
dict_temporary_eid = dict()
dict_class_id = dict()  # 储存所有的芯片名称和对应的id
dict_share_md5 = dict()
dict_u_net_md5 = (
    dict()
)  # 临时储存用户的net_md5，  dict_u_net_md5[uid]="1234561234123123123122312",time.time()
# dict_share_old=dict()
# dict_share_old本来是想在内存条暂时缓存用户的绑定信息的，但是在数据库实现了这个存储功能，所以这个字典就用不到了
# dict_share_old=dict_share_md5[dict_post['share_ma']],time.time()
# 如果要提高正则的效率#用re_get_MAC.group(0)取代findall(str)[0]

# 用正则提取MAC、ip、芯片ID
# re_get_IP = re.compile('CIFSR:STAIP,"((?:[0-9]{1,3}\.){3}[0-9]{1,3})')#此正则无法检验合法性
# re_get_MAC = re.compile('CIFSR:STAMAC,"((?:[0-9a-fA-F]{2}\:){5}[0-9a-fA-F]{2})')
# re_get_STM32F1_ID = re.compile('id=((?:(?:0x[0-9a-fA-F]{8},{0,1})){3})')
#'+CIFSR:STAIP,"192.168.137.54"+CIFSR:STAMAC,"48:3f:da:7e:0d:a5"id=0x38FFD705,0x4D583734,0x29662043'


# UDP接收到数据之后的处理线程
class UDP_data_work_thread(threading.Thread):
    # +EID=20,chip_id=2507829m1,temperature high
    __SELECT_E_IP = "select tcp_ip from she_bei where id=%s"
    re_udp = re.compile("^\+EID=(\d+),chip_id=(\d+)((?:[mwe]\d+)+)$")

    def __init__(self, UDP_data, UDP_IPadd):
        threading.Thread.__init__(self)
        self.UDP_data = UDP_data
        self.IPadd = UDP_IPadd

    def run(self):
        print(
            time.strftime("%Y-%m-%d %H:%M:%S  ", time.localtime()),
            "UDP_IP:	",
            self.IPadd,
            end="",
        )  # 调试用
        try:
            str_UDP_data = self.UDP_data.decode("utf8")
        except UnicodeDecodeError:
            try:
                str_UDP_data = self.UDP_data.decode("gbk")
            except UnicodeDecodeError:
                # 对于总是无法正常解析的数据发送过来的ip给予拉黑处理
                Blackip.add_black_ip(self.IPadd[0])
                print("UDP_data-:	", self.UDP_data)
                return
        print("UDP_data-:	", str_UDP_data)  # 调试用#将收到的内容编码之后输出
        # 从里面解析出eid，不然就从里面解析出stm32的id，然后向数据库查询。
        try:
            list_udp_data = self.re_udp.findall(str_UDP_data)[0]
            int_EID = int(list_udp_data[0])
            int_CHIP_ID = int(list_udp_data[1])
            str_message = list_udp_data[2]  # 取出警告内容
        except ValueError as e:
            MyPrintE.e_print(e, "UDP提取eid出错,数据转换异常")
            Blackip.add_black_ip(self.IPadd[0])
            return
        except IndexError as e:
            MyPrintE.e_print(e, "UDP提取eid出错，未提取到内容")
            Blackip.add_black_ip(self.IPadd[0])
            return
        # 对ip地址进行校验，必须要和tcp 的地址相同
        list_sql_eip = Mymysql().mysql_sql_select(self.__SELECT_E_IP, (int_EID,))
        if list_sql_eip[0][0] != self.IPadd[0]:
            MyPrintE.log_print(
                "UDP_data_work_thread.run()", (list_sql_eip[0][0], self.IPadd[0])
            )
            return
        # 从这里把数据包分开，交给 MyETcp 处理
        myetcp = DictTcp().get_e_tcp(int_EID)
        if type(myetcp) == MyETcp:
            myetcp.do_udp_data(int_EID, int_CHIP_ID, str_message)
        else:
            MyPrintE.log_print("设备在 dict_TCP 中未找到", (int_EID, int_CHIP_ID, str_message))
        return


# TCP接收到数据之后的处理线程
class TCP_link_work_thread(threading.Thread):
    mymysql = Mymysql()
    re_get_UID = re.compile("\+UID:([0-9]+)")
    re_get_IP = re.compile("((?:[0-9]{1,3}\.){3}[0-9]{1,3})$")
    re_get_MAC = re.compile("((?:[0-9a-fA-F]{2}[\:\-]){5}[0-9a-fA-F]{2})$")
    list_data_class_name = ["class_id", "chip_id", "ip", "mac"]

    def __init__(self, TCP_link, IPadd):
        threading.Thread.__init__(self)
        # self.TCP_link socket
        # self.IPadd ('192...' ,9091)
        self.TCP_link = TCP_link
        self.IPadd = IPadd

    def run(self):
        print(
            time.strftime("%Y-%m-%d %H:%M:%S  ", time.localtime()),
            "TCP_add-:	%s" % str(self.IPadd),
            end="",
        )  # 输出监听到的链接的地址
        # 开始接收数据
        self.TCP_link.settimeout(3)
        try:
            bytes_TCP_data = self.TCP_link.recv(1024)  # 接收套接字
        except ConnectionResetError as e:
            # MyPrintE.e_print(e,"TCP 1")
            self.TCP_link.close()
            return
        except BlockingIOError as e:
            # MyPrintE.e_print(e,"TCP 2")
            self.TCP_link.close()
            return
        # except TimeoutError as e:
        # 	self.TCP_link.close()
        # 	return
        except BrokenPipeError as e:
            self.TCP_link.close()
            return
        except socket.timeout as e:
            # MyPrintE.e_print(e)
            self.TCP_link.close()
            return
        except Exception as e:
            MyPrintE.e_print(e)
            self.TCP_link.close()
            return
        self.TCP_link.settimeout(None)
        try:
            str_TCP_data = bytes_TCP_data.decode("gbk")
        except UnicodeDecodeError:
            try:
                str_TCP_data = bytes_TCP_data.decode("utf8")
            except UnicodeDecodeError:
                Blackip.add_black_ip(self.IPadd[0])
                print("TCP_data-:	", bytes_TCP_data)
                self.TCP_link.close()
                return
        print("TCP_data-:	", str_TCP_data)  # 将收到的内容编码之后输出
        binding_user_id = 0
        if str_TCP_data.find("+UID:") >= 0:
            # 如果收到了绑定设备的用户，就储存一下绑定信息。
            # 然后重新接受设备的信息
            binding_user_id = int(self.re_get_UID.findall(str_TCP_data)[0])
            self.TCP_link.settimeout(3)
            try:
                bytes_TCP_data = self.TCP_link.recv(1024)  # 接收套接字
            except socket.timeout as e:
                # MyPrintE.e_print(e)
                Blackip.add_black_ip(self.IPadd[0])
                self.TCP_link.close()
                return
            except Exception as e:
                MyPrintE.e_print(e)
                self.TCP_link.close()
                return
            self.TCP_link.settimeout(None)
            try:
                str_TCP_data = bytes_TCP_data.decode("utf8")
            except UnicodeDecodeError:
                try:
                    str_TCP_data = bytes_TCP_data.decode("gbk")
                except UnicodeDecodeError:
                    Blackip.add_black_ip(self.IPadd[0])
                    print("TCP_data-:	", bytes_TCP_data)
                    self.TCP_link.close()
                    return
            print("TCP_data-:	", str_TCP_data)

        # 将设备的信息和TCP连接储存起来
        dict_tcp_data = dict()
        for data_ in str_TCP_data.split(","):
            list_2 = data_.split("=")
            if len(list_2) == 2:
                dict_tcp_data[list_2[0]] = list_2[1]
            else:
                Blackip.add_black_ip(self.IPadd[0])
                print(str_TCP_data)
                self.TCP_link.close()
                return

        print(dict_tcp_data)
        # 校验所需要的元素是否齐全
        for a in self.list_data_class_name:
            if a not in dict_tcp_data:
                Blackip.add_black_ip(self.IPadd[0])
                self.TCP_link.close()
                return
        # 这里应当对收到的数据进项校验，校验是否合法
        # 数据校验放到下面函数里了
        # 根据设备提供的信息，查询或分配一个eid
        eid = self.dict_TCP_add(
            dict_tcp_data[self.list_data_class_name[3]],  # MAC
            dict_tcp_data[self.list_data_class_name[2]],  # 局域网IP
            self.IPadd[0],  # TCP链接IP
            dict_tcp_data[self.list_data_class_name[1]],  # STM32F1_ID
            dict_tcp_data[self.list_data_class_name[0]],
            self.TCP_link,
        )  # TCP链接
        if eid == 0:
            self.TCP_link.close()
            return
        if binding_user_id != 0:
            # 在这里进行设备用户绑定的入库
            MyPrintE.log_print("用户的id=" + str(binding_user_id) + "设备的id=" + str(eid))
            # 这里是个假插入，实际是个存储过程，执行了不抛出异常就行，不用担心结果
            self.mymysql.mysql_sql_insert(
                self.mymysql.SQL_SELECT_EXIST_EID_AN_UID, (binding_user_id, eid)
            )

        str_heart = time.strftime(DictTcp.STR_TIME, time.localtime())
        # 设置要返回的数据
        msg = "+EID:" + str(eid) + "\r\n" + str_heart  # 将硬件的数据库id返回回去，用于TCP链接的查找
        # 反正这里发的是ASCII数据，编码随意喽
        # 不要关闭TCP链接，TCP链接将会用于用户对设备操作
        self.TCP_link.send(msg.encode("gbk"))
        # 只需要在这里延迟，这里是没有返回数据的
        time.sleep(0.05)
        DictTcp().get_e_tcp(eid).send_jiantin(self.mymysql)

    def dict_TCP_add(
        self, str_MAC, str_lan_IP, str_wan_IP, chip_id, class_id, socket_TCP_link
    ):
        global dict_temporary_eid, dict_class_id
        # 等数据库建好之后使用数据库的 设备ID 作为TCP链接的字典索引
        # 先查询是否已经是库里的
        if re.match(self.re_get_MAC, str_MAC) == None:
            return 0
        if re.match(self.re_get_IP, str_lan_IP) == None:
            return 0
        if re.match(self.re_get_IP, str_wan_IP) == None:
            return 0
        str_MAC = int(str_MAC.replace(":", ""), 16)  # 将MAC地址转换成int数据
        a = self.mymysql.mysql_sql_callproc_1(
            self.mymysql.SQL_CALLPROC_EXICT_EID,
            (
                int(class_id),
                chip_id,
                str_MAC,
                str_lan_IP,
                str_wan_IP,
                time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            ),
        )
        # a=[(19, 'utf-8')]
        if a != None and len(a) == 1 and len(a[0]) == 2:
            eid = a[0][0]
            DictTcp().set_e_tcp(eid, socket_TCP_link, a[0][1])
            dict_temporary_eid[chip_id] = [eid, int(time.time())]
            return eid
        else:
            MyPrintE.log_print(
                "dict_TCP_add sql 返回数据有问题",
                (
                    a,
                    class_id,
                    chip_id,
                    str_MAC,
                    str_lan_IP,
                    str_wan_IP,
                ),
            )
            return 0


# 为每一个TCP链接建立线程
class TCP_thread(threading.Thread):
    def run(self):
        # print("TCP_thread pid=",os.getpid())
        serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # 启动服务器，""本应填充计算机名或者ip地址，""则为使用本机全部的地址，第二个整型为端口号
        serversocket.bind(("", 9999))
        # 设置最大连接数，超过后排队
        serversocket.listen(1000000000)  # 最大值为C语言的long的最大值
        print("TCP-9999服务已经启动")
        while True:
            # 建立客户端连接
            # clientsocket,addr = serversocket.accept()#监听链接
            link, ipadd = serversocket.accept()
            if Blackip.is_black_ip(ipadd[0]):
                link.close()
            else:
                TCP_link_work_thread(link, ipadd).start()


# 为每一个UDP链接建立线程
class UDP_thread(threading.Thread):
    def run(self):
        # print("UDP_thread pid=",os.getpid())
        UDP_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # 启动服务器，""本应填充计算机名或者ip地址，""则为使用本机全部的地址，第二个整型为端口号
        UDP_s.bind(("", 9998))
        print("UDP-9998服务已经启动")
        i = 0
        while True:
            # data1,user_add=UDP_s.recvfrom(1024)#接收套接字
            i = i + 1
            UDP_data, UDP_ip = UDP_s.recvfrom(1024)
            if Blackip.is_black_ip(UDP_ip[0]):
                continue
            UDP_data_work_thread(UDP_data, UDP_ip).start()


def open_TCP_UDP():
    # 新建进程，并开始
    new_thread = UDP_thread()
    new_thread.start()
    new_thread = TCP_thread()
    new_thread.start()


class thread_clear_dict_time(threading.Thread):
    # def __init__(self):
    def run(self):
        dicttcp = DictTcp()
        SLEEP_TIME = 60
        sleep_time = SLEEP_TIME
        # 有必要的话用try把while里的东西包起来
        while 1:
            if sleep_time < 0:
                sleep_time = 0.0001
            time.sleep(sleep_time)
            # 这里有bug，发邮件用时太久导致这里成了负数然后崩溃sleep length must be non-negative。2个修改，这里加非负判断，发邮件放到子线程
            start_time = time.time()
            clear_dict_time()
            dicttcp.clean_dict_TCP_olddata()
            print(f"last sleep_time = {sleep_time} S")
            sleep_time = start_time + SLEEP_TIME - time.time()


def new_a_thread_clear_dict_time():
    # 新建一个下载进程，并开始
    new_thread = thread_clear_dict_time()
    new_thread.start()


def clear_dict_time():
    global dict_time, dict_temporary_eid, dict_share_md5, dict_u_net_md5
    print(time.strftime("%Y-%m-%d %H:%M:%S ", time.localtime()), "清洗执行 ", end="")
    time1 = time.time()
    if len(dict_time) != 0:
        list_dict = list(dict_time.keys())
        # print(dict_time)
        for dict_i in list_dict:
            if (time1 - dict_time[dict_i][1]) > 300:
                # 将超过5分钟的邮箱删除
                dict_time.pop(dict_i)
    print(" dict_time=", list(dict_time.keys()), end="")

    if len(dict_temporary_eid) != 0:
        list_dict = list(dict_temporary_eid.keys())
        for dict_i in list_dict:
            if (time1 - dict_temporary_eid[dict_i][1]) > 300:
                # 将超过5分钟的EID删除
                dict_temporary_eid.pop(dict_i)
    print(" dict_temporary_eid=", list(dict_temporary_eid.keys()), end="")

    if len(dict_share_md5) != 0:
        list_dict = list(dict_share_md5.keys())
        for dict_i in list_dict:
            if (time1 - dict_share_md5[dict_i][2]) > 300:
                dict_share_md5.pop(dict_i)
    print(" dict_share_md5=", list(dict_share_md5.keys()), end="")

    if len(dict_u_net_md5) != 0:
        list_dict = list(dict_u_net_md5.keys())
        for dict_i in list_dict:
            if (time1 - dict_u_net_md5[dict_i][1]) > 1800:
                dict_u_net_md5.pop(dict_i)
    print(" dict_u_net_md5=", list(dict_u_net_md5.keys()), end="")


class RequestHandler(BaseHTTPRequestHandler):
    global dict_time, dict_temporary_eid, dict_share_md5

    re_post_name = re.compile("^/([0-9a-zA-Z%_]+)")
    re_email = re.compile("email=[-_0-9a-zA-Z\u4e00-\u9fa5]+@[a-zA-Z0-9]+[\.]{1}com")
    re_md5head = re.compile("/pic=[0-9a-f]{32}\.[a-zA-z0-9]{1,5}")
    re_special_char = re.compile("^[^`~!@#$%^&*()_\-=:;+\"'?{}\[\]\\\\/<>,.|\s]+$")
    re_do_e_data = re.compile(
        "^(@[^\[:\]]+)\[((?:-?\d{0,30})(\.?\d{0,2}))([^\s\$\]]*)-((?:-?\d{0,30})(\.?\d{0,2}))([^\s\$\]]*)\]:((?:-?\d{0,30})(\.?\d{0,2}))([^\s\$\]]*)$"
    )

    # 			"@20$温度<aaa$@20@开关1:aaa"('20', '温度', '<', '', '', 'aaa', '20', '@开关1', '', 'aaa')
    # 			"@20$温度<99.99$@20@开关1:0"('20', '温度', '<', '99.99', '.99', '', '20', '@开关1', '0', '')
    # 根据匹配到的某些组为空，或者不为空，来判断数据类型
    re_ld_insert_data = re.compile(
        "^@(\d{0,30})\$([^<>=~]{0,50})([<>=~])((?:-?\d{0,30})(\.?\d{0,2}))([^\s\$]*)\$@(\d{0,30})(@(?:[^:\s]{0,49})):(\d{0,30})([^\s]{0,30})$"
    )
    re_ld_updata_data = re.compile(
        "^A(\d{0,30})F(\d{0,30})J(\d{0,30})D(\d{0,30})@(\d{0,30})\$([^<>=~]{0,50})([<>=~])((?:-?\d{0,30})(\.?\d{0,2}))([^\s\$]*)\$@(\d{0,30})(@(?:[^:\s]{0,49})):(\d{0,30})([^\s]{0,30})$"
    )
    mymysql = Mymysql()
    # {'uid': '1', 'email': '2280057905@qq.com', 'password': '123456', 'new_time':'1618328118418', 'share_eid': '19-20-21-'}
    # LIST_FOR_SHARE_NEED = ['uid', 'email', 'password', 'new_time', 'share_eid']
    LIST_FOR_SHARE_NEED = ["uid", "share_eid"]
    # {'uid': '1', 'email': '2280057905@qq.com', 'password': '123456', 'new_time':'1618328118418', 'share_ma': '1cc438227ca4415609444b7d5c85b0a7'}
    # LIST_GET_SHARE_NEED = ['uid', 'email', 'password', 'new_time', 'share_ma']
    LIST_GET_SHARE_NEED = ["uid", "share_ma"]
    # {'uid': '1', 'email': '2280057905@qq.com', 'password': '123456', 'new_time':'1618328118418', 'eid': '19'}
    # {'uid': '1', 'email': '2280057905@qq.com', 'password': '123456', 'new_time':'1618328118418', 'eid': '20'}
    # LIST_USER_HAVE_NODE_NEED = ['uid', 'email', 'password', 'new_time', 'eid']#校验用户是否有权限操作设备需要的信息名称
    LIST_USER_HAVE_NODE_NEED = ["uid", "eid"]  # 校验用户是否有权限操作设备需要的信息名称
    # LIST_USER_HAVE_NODE_NEED1 = ['uid', 'email', 'password', 'new_time', 'eid',"send"]#校验用户是否有权限操作设备需要的信息名称
    LIST_USER_HAVE_NODE_NEED1 = ["uid", "eid", "send"]  # 校验用户是否有权限操作设备需要的信息名称
    # {'uid': '1', 'eid': '21', 'name': '2号机te', 'oldname': '2号机'}
    LIST_RENAME_NODE = ["uid", "eid", "name", "oldname"]
    # 查询所有的联动信息
    # LIST_LD_SELECT = ['uid', 'email', 'password', 'new_time']
    LIST_LD_SELECT = [
        "uid",
    ]
    # 查询所有的联动信息
    # LIST_LD_INSERT = ['uid', 'email', 'password', 'new_time','data']
    LIST_LD_INSERT = ["uid", "data"]

    # 注册数据校验
    LIST_ZHUCE = ["email", "password1", "password2"]

    # 邮箱登录数据校验
    LIST_YOUXIANG_LOGIN = ["email", "password2"]

    # 储存post名字和函数的映射关系
    DICT_POST_NEW = dict()

    def __init__(self, a, b, c):
        # 这里有个先后顺序，先完成自己的init再调用父类的init
        self.__DICT_POST_NEW_init()
        try:
            BaseHTTPRequestHandler.__init__(self, a, b, c)
        except ConnectionResetError as e:
            # MyPrintE.e_print(e,None,(a,b,c))
            return
        except BrokenPipeError as e:
            # MyPrintE.e_print(e,None,(a,b,c))
            return

    def __DICT_POST_NEW_init(self):
        """post不同的名字，调用不同的函数"""
        self.DICT_POST_NEW["rename_equipment"] = self.rename_equipment
        self.DICT_POST_NEW["for_friend"] = self.for_friend
        self.DICT_POST_NEW["get_share"] = self.get_share
        self.DICT_POST_NEW["ld_select"] = self.ld_select
        self.DICT_POST_NEW["ld_insert"] = self.ld_insert
        self.DICT_POST_NEW["ld_delete"] = self.ld_delete
        self.DICT_POST_NEW["ld_updata"] = self.ld_updata
        self.DICT_POST_NEW["update"] = self.update
        self.DICT_POST_NEW["binding_equipment"] = self.binding_equipment
        self.DICT_POST_NEW["get_my_equipment"] = self.get_my_equipment
        self.DICT_POST_NEW["get_equipment_data"] = self.get_equipment_data
        self.DICT_POST_NEW["get_equipment_info"] = self.get_equipment_info
        self.DICT_POST_NEW["set_equipment_data"] = self.set_equipment_data
        self.DICT_POST_NEW["equipment_delete"] = self.equipment_delete
        self.DICT_POST_NEW["pw_login"] = self.pw_login
        # self.DICT_POST_NEW["user_delete"]=self.user_delete
        self.DICT_POST_NEW["pw_updata_send"] = self.pw_updata_send
        self.DICT_POST_NEW["pw_updata"] = self.pw_updata
        self.DICT_POST_NEW["select_old_date"] = self.select_old_date
        return

    def uid_have_eid(self, int_uid, int_eid):
        assert type(int_uid) == int
        assert type(int_eid) == int
        uid_have_eid = self.mymysql.mysql_sql_select(
            self.mymysql.SQL_SELECT_UID_HAVE_EID,
            (
                int_uid,
                int_eid,
            ),
        )
        if (
            type(uid_have_eid) != list
            or len(uid_have_eid) != 1
            or len(uid_have_eid[0]) != 1
            or uid_have_eid[0][0] != int_uid
        ):
            MyPrintE.log_print(
                "SQL_SELECT_UID_HAVE_EID",
                (
                    int_uid,
                    int_eid,
                    uid_have_eid,
                ),
            )
            return False
        return True

    def dict_jiao_yan(self, dict_, list_name):
        if type(dict_) != dict:
            return 0
        if type(list_name) != list:
            return 0
        # 校验长度
        if len(dict_) != len(list_name):
            return 0
        # 校验名字
        for name in list_name:
            if name not in dict_:
                return 0
        return dict_

    def send_content(self, content, code=200):
        # get返回数据封装
        try:
            self.send_response(code)
            # 将数据编码之后发出
            if type(content) == str:
                self.send_header("Content-Type", "text/html")
                bytes1 = content.encode("utf-8")
                self.send_header("Content-Length", str(len(bytes1)))
                self.send_header("Content-Language", "zh-CN,utf-8")
                self.end_headers()
                self.wfile.write(bytes1)
            elif type(content) == bytes:
                self.send_header("Content-Length", str(len(content)))
                self.send_header("Content-Type", "*/*")
                self.end_headers()
                self.wfile.write(content)
        except ConnectionResetError as e:
            # MyPrintE.e_print(e)
            return
        except Exception as e:
            MyPrintE.e_print(e)
            return

    def send_content2(self, content, str_net_md5, code=200):
        if type(content) == dict:
            content = json.dumps(content)
        assert type(content) == str, "send_content2 content 应该是一个 str 类型"
        assert type(str_net_md5) == str, "send_content2 str_net_md5 应该是一个 str 类型"
        assert type(code) == int, "send_content2 code 应该是一个 int 类型"
        # get返回数据封装
        try:
            content = Mykeyer.keyer_str_get_bytes(str_net_md5, content)
            self.send_response(code)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Content-Language", "zh-CN,utf-8")
            self.send_header("Content-Type", "*/*")
            self.end_headers()
            self.wfile.write(content)
        except ConnectionResetError as e:
            # MyPrintE.e_print(e)
            return
        except Exception as e:
            MyPrintE.e_print(e)
            return

    def req_datas_to_string(self, req_datas):
        if type(req_datas) == bytes:
            try:
                str_post_data = req_datas.decode("utf8")
                return str_post_data
            except UnicodeDecodeError:
                try:
                    str_post_data = req_datas.decode("gbk")
                    return str_post_data
                except UnicodeDecodeError:
                    print(
                        time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                        + "	解码错误  1  编码超出范围  ",
                        req_datas,
                    )
                    return 0
        elif type(req_datas) == str:
            str_post_data = req_datas
            return str_post_data
        else:
            print(
                time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                + "	解码错误  2  数据类型超出 type=",
                type(req_datas),
            )
            return 0

    def req_datas_to_string2(self, req_datas, str_path):
        global dict_u_net_md5
        int_uid = int(str_path[str_path.rfind("=") + 1 :])
        str_net_md5 = ""
        try:
            str_net_md5 = dict_u_net_md5[int_uid][0]
            dict_u_net_md5[int_uid] = str_net_md5, time.time()
        except KeyError:
            sql_data = self.mymysql.mysql_sql_select(
                self.mymysql.SEL_U_NET_MD5, (int_uid,)
            )
            if sql_data != None and len(sql_data[0]) == 1:
                str_net_md5 = hashlib.md5(
                    str(sql_data[0][0]).encode("utf-8")
                ).hexdigest()
                dict_u_net_md5[int_uid] = str_net_md5, time.time()
            else:
                return None

        str_post_data = Mykeyer.keyer_bytes_get_str(str_net_md5, req_datas)
        if str_post_data == 0:
            return None
        return (str_post_data, str_net_md5)

    def str_to_dict(self, str_data):
        if str_data == 0:
            return 0
        elif type(str_data) != str:
            print(
                time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                + "	str_to_dict错误 1 数据出错"
            )
            print(str_data)
            raise Exception("str_to_dict  str_data 应该是一个str类型")
        try:
            dict_post = json.loads(str_data)
        except json.decoder.JSONDecodeError as e:
            MyPrintE.e_print(e, str_data)
            return 0
        return dict_post

    def send_data_to_equipment(self, int_eid, str_send_data):
        assert type(int_eid) == int, "send_data_to_equipment type(eid)!=int"
        assert (
            type(str_send_data) == str
        ), "send_data_to_equipment type(str_send_data)!=str"
        dicttcp = DictTcp()
        dict_TCP_i = dicttcp.get_e_tcp(int_eid)
        if type(dict_TCP_i) != MyETcp or dict_TCP_i.is_line_out() == True:
            return "#状态:离线#"
        str_TCP_reutn_data = dict_TCP_i.send_data_to_equipment(
            str_send_data
        )  # 这里的timeout时间控制写的很差，以后再改，3S可能每个步骤的阻塞上限都是3S
        if str_TCP_reutn_data == None:
            return "#状态:数据超时#"
        if str_TCP_reutn_data == False:
            return "#状态:离线#"
        if type(str_TCP_reutn_data) != bytes:
            return "#状态:数据异常1#"
        str_TCP_reutn_data = dict_TCP_i.bytes_to_str(str_TCP_reutn_data)
        if type(str_TCP_reutn_data) != str:
            return "#状态:数据异常2#"
        return str_TCP_reutn_data

    def send_info_to_equipment(self, int_eid, str_info):
        assert type(int_eid) == int, "send_data_to_equipment type(eid)!=int"
        assert type(str_info) == str, "send_data_to_equipment type(str_info)!=str"
        dicttcp = DictTcp()
        dict_TCP_i = dicttcp.get_e_tcp(int_eid)
        if type(dict_TCP_i) != MyETcp or dict_TCP_i.is_line_out() == True:
            return None
        assert (
            type(dict_TCP_i) == MyETcp
        ), "send_data_to_equipment type(dict_TCP_i)!=MyETcp"
        str_TCP_reutn_data = dict_TCP_i.send_data_to_equipment(str_info)
        if type(str_TCP_reutn_data) != bytes:
            return None
        str_TCP_reutn_data = dict_TCP_i.bytes_to_str(str_TCP_reutn_data)
        if type(str_TCP_reutn_data) != str:
            return None
        return str_TCP_reutn_data

    def do_GET(self):
        # 收到get请求处理函数
        str_getdata = str(self.path)
        # 获取到传来的信息
        user_email = ""
        if self.path.startswith("/ok") == True:
            str_return = (
                '<head><meta charset="utf-8"><title>何辰川</title></head><body><div><h1>%s</h1></div></body>'
                % time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            )
            self.send_content(str_return)
            return
        elif self.path == "/app.apk":
            str_return = """
                        <html>
                        <head>
                        	<meta charset="utf-8">
                        	<meta name="apk下载" content="width=device-width" />
                        </head>
                        <body>
                        	<!-- <div><h1><a href="http://121.89.243.207:8080/release-app.apk" download="app.apk">点击下载</a></h1></div> -->
                        	<div>
                        		<h1><a href="https://gitee.com/he_chen_chuan/Mytabs">gitee</a></h1>
                        	</div>
                        	<div>
                        		<h1><a href="https://github.com/BAICHEN123/Mytabs/releases">github</a></h1>
                        	</div>
                        </body> 
                        </html> 
                        """
            self.send_content(str_return)
            return
        elif self.path == "/release-app.apk":
            try:
                f = open("app-release.apk", "rb")
                user_head = f.read()
                f.close()
                try:
                    self.send_content(user_head)
                    return
                except ConnectionResetError as e:
                    # MyPrintE.e_print(e)
                    return
                except BrokenPipeError as e:
                    # MyPrintE.e_print(e)
                    return
            except Exception as e:
                MyPrintE.e_print(e)
                self.send_content("资源不存在", 404)
                return
        elif self.path.startswith("/user_head") == True:
            try:
                f = open("head/" + self.path[10:], "rb")
                user_head = f.read()
                f.close()
                try:
                    self.send_content(user_head)
                    return
                except BrokenPipeError as e:
                    # MyPrintE.e_print(e)
                    return
            except Exception as e:
                MyPrintE.e_print(e)
                self.send_content("error1", 202)
                return
        elif self.path == "/blackipreload":
            black_data = Blackip.black_ip_init()
            smtp_data = MySmtp.load_email_password()
            time_data = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            str_return = f"""<head><meta charset="utf-8"><title>reload</title></head><body>
            <div><h1>{time_data}</h1></div>
            <div><h1>smtp读取到的长度 {smtp_data}</h1></div>
            <div><h1>黑名单长度 {black_data}</h1></div>
            </body>"""
            self.send_content(str_return)
            return
        else:
            # 不提供以外服务
            self.send_content("error2", 404)

    def for_friend(self, str_post_data):
        global dict_share_md5
        """
		用字典临时储存
		储存还没有被接收的分享码
		dict_share_md5["#eid#eid#...#time.time()#".md5]=share_uid,list_eid,time.time(),share_id
		时间戳用来限制时间
		每个分享码限制一个人在五分钟内使用，
		传入发送用户的uid，想要分享eid
			用于校验分享的用户是否有此设备的权限
		传入接收用户的id
			用于和设备绑定
		sql要求
			存储过程，分享的时候校验所有权
			存储过程：插入的时候防止重复
		{'uid': '1', 'share_eid': '19-20-21-'}
		"""
        # str_post_data = self.req_datas_to_string(req_datas)
        dict_post = self.dict_jiao_yan(
            self.str_to_dict(str_post_data), self.LIST_FOR_SHARE_NEED
        )  # 整理数据顺便校验
        if dict_post == 0:
            return "end=1,log=数据缺失"
        list_share_eid = list()
        try:
            dict_post["uid"] = int(dict_post["uid"])
            for str_eid in dict_post["share_eid"].split("-"):
                if str_eid == "":
                    continue
                list_share_eid.append(int(str_eid))
        except ValueError as e:
            MyPrintE.e_print(e, "dict_post=" + str(dict_post))
            return "end=2,log=数据异常"
        list_sql_eid = self.mymysql.list_tuple_to_list(
            self.mymysql.mysql_sql_select(
                self.mymysql.SQL_SELECT_UID_EIDX_NONAME, (dict_post["uid"],)
            )
        )
        if list_sql_eid == None:
            MyPrintE.log_print("for_friend  list_sql_eid==0 出错")
            return "end=3,log=未查询到您未拥有设备，越权操作"
        for eid_i in list_share_eid:
            if eid_i not in list_sql_eid:
                MyPrintE.log_print("for_friend  eid_i not in list_sql_eid 出错")
                return "end=4,log=您没有部分设备的权限，越权操作"
        data_time = int(time.time() * 10000)
        # 仅对设备、用户id取MD5，不再加入时间，这样如果用户在短时间之内创建了同样的设备分享，就不会再多次入库了
        share_index_md5 = hashlib.md5(
            (dict_post["share_eid"] + "uid=" + str(dict_post["uid"])).encode("utf-8")
        ).hexdigest()
        if share_index_md5 not in dict_share_md5:
            # 将分享码的信息入库
            share_id = self.mymysql.mysql_sql_insert(
                self.mymysql.SQL_INSERT_SHARE_DATA,
                (
                    share_index_md5,
                    dict_post["uid"],
                ),
            )
            if share_id == None:
                MyPrintE.log_print(
                    "for_friend  SQL_INSERT_SHARE_DATA  出错",
                    (
                        share_index_md5,
                        dict_post["uid"],
                    ),
                )
                # 用户分享的设备未与自己绑定
                return "end=5,log=您没有部分设备的权限，越权操作"
            dict_share_md5[share_index_md5] = [
                dict_post["uid"],
                list_share_eid,
                time.time(),
                share_id,
            ]
        else:
            # 用户之前创建过相同的设备分享，只要更新时间就可以了
            dict_share_md5[share_index_md5][2] = time.time()
        return "end=0,log=" + share_index_md5

    def get_share(self, str_post_data):
        global dict_share_md5
        # {'uid': '1', 'email': '2280057905@qq.com', 'password': '123456',
        #'new_time': '1618328118418', 'share_ma':
        #'1cc438227ca4415609444b7d5c85b0a7'}
        dict_post = self.dict_jiao_yan(
            self.str_to_dict(str_post_data), self.LIST_GET_SHARE_NEED
        )  # 整理数据顺便校验
        if dict_post == 0:
            return "end=1,log=数据异常"
        if dict_post["share_ma"] not in dict_share_md5:
            print(dict_post)
            print(dict_share_md5)
            return "end=2,log=此码已过期"

        try:
            dict_post["uid"] = int(dict_post["uid"])
            # 这里重写，先将分享码的id和接收用户的id绑定，然后再进行设备的绑定，如果失败则一起回滚
            # share_id 分享码id dict_share_md5[dict_post['share_ma']][3]
            # share_uid 分享设备的用户的id dict_share_md5[dict_post['share_ma']][0]
            # in_uid 接收分享的用户id dict_post['uid']
            # in_eid 被分享的设备的id list_share_eid=dict_share_md5[dict_post['share_ma']][1]
            self.mymysql.for_INSERT_EXIST_SHAER(
                dict_share_md5[dict_post["share_ma"]][3],
                dict_share_md5[dict_post["share_ma"]][0],
                dict_post["uid"],
                dict_share_md5[dict_post["share_ma"]][1],
            )
        except ValueError as e:
            MyPrintE.e_print(e, "dict_post=" + str(dict_post))
            # 数据格式不对
            return "end=2,log=数据内容错误"
        dict_share_md5.pop(dict_post["share_ma"])
        return "end=0,log=获取分享成功"

    def ld_select(self, str_post_data):
        """查询用户名下所有设备的联动"""
        dict_post = self.dict_jiao_yan(
            self.str_to_dict(str_post_data), self.LIST_LD_SELECT
        )  # 整理数据顺便校验
        if dict_post == 0:
            return "end=1,title=10,log=数据错误"
        # 传过来uid，查询的时候通过uid查询，查询联动表，返回格式化内容

        try:
            dict_post["uid"] = int(dict_post["uid"])
        except ValueError:
            return "end=2,title=10,log=内容错误"
        list_sql = self.mymysql.mysql_sql_select(
            self.mymysql.SELECT_UID_LD_ALL, (dict_post["uid"],)
        )
        if len(list_sql) == 0:
            # 刚接受分享完设备之后，刷新联动，有几率在有联动的情况下到此分支
            MyPrintE.log_print(
                "ld_select  SELECT_UID_LD_ALL", (dict_post["uid"], list_sql)
            )
            return "end=3,title=10,log=您还没有创建联动"
        str_end = ""
        for item in list_sql:
            tmp = f"A{item[0]}F{item[1]}J{item[2]}D{item[6]}@{item[3]}${item[4]}{item[5]}{item[7]}$@{item[8]}{item[9]}:{item[10]}"
            str_end = str_end + tmp + "#"
        return "end=0,title=10,log=" + str_end

    def ld_insert(self, str_post_data):
        dict_post = self.dict_jiao_yan(
            self.str_to_dict(str_post_data), self.LIST_LD_INSERT
        )  # 整理数据顺便校验
        if dict_post == 0:
            return "end=1,title=10,log=数据错误"
        # 传过来uid，查询的时候通过uid查询，查询联动表，返回格式化内容

        try:
            dict_post["uid"] = int(dict_post["uid"])
        except ValueError:
            return "end=2,title=10,log=内容错误"

        print(dict_post["data"])

        kk = re.match(self.re_ld_insert_data, dict_post["data"])
        if kk == None:
            return "end=3,title=10,log=格式错误"

        kk = kk.groups()
        if len(kk) != 10:
            return "end=3,title=10,log=数据缺失"
        # "@20$温度<aaa$@20@开关1:aaa"('20', '温度', '<', '', '', 'aaa', '20', '@开关1', '', 'aaa')
        # "@20$温度<99.99$@20@开关1:0"('20', '温度', '<', '99.99', '.99', '', '20', '@开关1', '0', '')

        # 身份验证的内容在这里插入
        if self.uid_have_eid(dict_post["uid"], int(kk[0])) == False:
            return "end=4,title=10,log=越权操作"
        if kk[6] != kk[0]:
            if self.uid_have_eid(dict_post["uid"], int(kk[6])) == False:
                return "end=4,title=10,log=越权操作"

        # "A10#@test1#>#20"
        str_send = "A0#" + kk[1] + "#" + kk[2] + "#"
        did = 0
        # 先验证，后入库
        if kk[4] != "":
            # 这是一个小数
            did = 2
            str_send = str_send + kk[3]
        elif kk[3] == "" and kk[5] != "":
            # 这是一个字符串
            did = 3
            str_send = str_send + kk[5]
        elif kk[3] != "":
            did = 1
            str_send = str_send + kk[3]
        str_send = str_send + "\t"
        print("str_send   ", str_send)
        str_test_end = self.send_info_to_equipment(int(kk[0]), str_send)
        if str_test_end != "L0":
            # 发起节点不认可数据
            print(str_test_end)
            self.send_content("end=3,title=10,log=发起节点不认可")
            return
        str_test_end = self.send_info_to_equipment(int(kk[6]), "get")
        for str_item in str_test_end.split("#"):
            if str_item.startswith(kk[7] + "["):
                """
                #懒得校验是否是合法区间了，有些数据的区间是动态区间，现在合法，不一定未来合法
                #@补光区间[10.00-100.00]:82.86(%)
                #('@补光区间', '10.00', '.00', '', '100.00', '.00', '', '82.86', '.86', '(%)')
                #bb=re.match(self.re_do_e_data,str_item)
                #if bb==None:
                #	continue
                #bb=bb.groups()
                #if bb[1]!="" and bb[4]!="":
                #	max=float(bb[4])
                #	min=float(bb[1])
                #	now=float(kk[8])
                #	if now<=max and now >=min:
                #		#数据合法
                #		pass
                """
                # 数据没问题
                # 可以入库了，入库之后再告知发起节点就算完成任务了
                list_tupe_data = self.mymysql.mysql_sql_callproc_1(
                    self.mymysql.LD_CALLPROC_IN,
                    (
                        int(kk[0]),
                        kk[1],
                        kk[2],
                        did,
                        kk[3] + kk[5],
                        int(kk[6]),
                        kk[7],
                        kk[8] + kk[9],
                        dict_post["uid"],
                    ),
                )
                if len(list_tupe_data[0]) != 3:
                    return "end=3,title=10,log=插入结果异常"
                # 在这里给节点发送监听信息
                str_e_data = self.send_info_to_equipment(
                    int(kk[0]), "A" + str(list_tupe_data[0][1]) + str_send[2:]
                )
                if (
                    type(str_e_data) == str
                    and str_e_data[0] == "L"
                    and int(str_e_data[1:]) > 0
                ):
                    return "end=0,title=10,log=添加成功，无需重启"
                print(list_tupe_data, str_e_data)
                return "end=0,title=10,log=添加成功,需要重启节点"
        return "end=3,title=10,log=接收节点不认可"

    def ld_delete(self, str_post_data):
        dict_post = self.dict_jiao_yan(
            self.str_to_dict(str_post_data), self.LIST_LD_INSERT
        )  # 整理数据顺便校验
        if dict_post == 0:
            return "end=1,title=10,log=数据错误"
        # 传过来uid，查询的时候通过uid查询，查询联动表，返回格式化内容

        try:
            dict_post["uid"] = int(dict_post["uid"])
            dict_post["data"] = int(dict_post["data"])
        except ValueError:
            return "end=2,title=10,log=内容错误"

        uid_have_eid = self.mymysql.mysql_sql_select(
            self.mymysql.LD_SELECT_UID_HAVE_DID, (dict_post["uid"], dict_post["data"])
        )
        if uid_have_eid[0][0] != 1:
            MyPrintE.log_print(
                "LD_SELECT_UID_HAVE_DID", (dict_post["uid"], dict_post["data"])
            )
            return "end=4,title=10,log=越权操作"
        int_eid = uid_have_eid[0][1]
        int_fid = uid_have_eid[0][2]

        uid_have_eid = self.mymysql.mysql_sql_delete(
            self.mymysql.DEL_LD_BANGDIN_DID, (dict_post["data"],)
        )
        if uid_have_eid != 1:
            MyPrintE.log_print(
                "DEL_LD_BANGDIN_DID", (dict_post["uid"], dict_post["data"])
            )
            return "end=5,title=10,log=删除失败 > _ <"

        # 从单片机删除监听
        str_send = "D" + str(int_fid)
        str_e_data = self.send_info_to_equipment(int_eid, str_send)
        if str_e_data != str_send:
            MyPrintE.log_print("str_e_data!= str_send", (int_eid, str_send, str_e_data))
            return "end=0,title=10,log=删除成功，需要重启节点"
        return "end=0,title=10,log=删除成功 ^ _ ^"

    def ld_updata(self, str_post_data):
        dict_post = self.dict_jiao_yan(
            self.str_to_dict(str_post_data), self.LIST_LD_INSERT
        )  # 整理数据顺便校验
        if dict_post == 0:
            print(str_post_data)
            return "end=1,title=10,log=数据错误"
        # 传过来uid，查询的时候通过uid查询，查询联动表，返回格式化内容

        try:
            dict_post["uid"] = int(dict_post["uid"])
        except ValueError:
            return "end=2,title=10,log=内容错误"

        print(dict_post["data"])

        kk = re.match(self.re_ld_updata_data, dict_post["data"])
        if kk == None:
            return "end=3,title=10,log=格式错误"

        kk = kk.groups()
        if len(kk) != 14:
            return "end=3,title=10,log=数据缺失"

        if self.uid_have_eid(dict_post["uid"], int(kk[4])) == False:
            return "end=4,title=10,log=越权操作"

        if kk[10] != kk[4]:
            if self.uid_have_eid(dict_post["uid"], int(kk[10])) == False:
                return "end=4,title=10,log=越权操作"

        # "A10#@test1#>#20"
        str_send = "A0#" + kk[5] + "#" + kk[6] + "#"
        did = int(kk[3])
        # 先验证，后入库
        if did == 1 or did == 2:
            str_send = str_send + kk[7]
        if did == 3:
            str_send = str_send + kk[9]
        str_send = str_send + "\t"
        print("str_send   ", str_send)
        str_test_end = self.send_info_to_equipment(int(kk[4]), str_send)
        if str_test_end != "L0":
            # 发起节点不认可数据
            print(str_test_end)
            return "end=3,title=10,log=发起节点不认可"
        str_test_end = self.send_info_to_equipment(int(kk[10]), "get")
        for str_item in str_test_end.split("#"):
            if str_item.startswith(kk[11] + "["):
                # 懒得校验是否是合法区间了，有些数据的区间是动态区间，现在合法，不一定未来合法
                # 数据没问题
                # 可以入库了，入库之后再告知发起节点就算完成任务了
                list_tupe_data = self.mymysql.mysql_sql_callproc_x(
                    self.mymysql.LD_CALLPROC_UPDATA,
                    (
                        int(kk[0]),
                        kk[1],
                        kk[2],
                        int(kk[4]),
                        kk[5],
                        kk[6],
                        did,
                        kk[7] + kk[9],
                        int(kk[10]),
                        kk[11],
                        kk[12] + kk[13],
                        dict_post["uid"],
                    ),
                )
                print(list_tupe_data)
                str_return = ""
                if len(list_tupe_data) == 2:
                    # 在这里插入删除监听的函数，fid=list_tupe_data[0][0]
                    str_send = "D" + str(list_tupe_data[0][0])
                    str_e_data = self.send_info_to_equipment(int(kk[4]), str_send)
                    if str_e_data != str_send:
                        MyPrintE.log_print(
                            "ld_updata", (int(kk[4]), str_send, str_e_data)
                        )
                        return "需要重启节点"
                    list_tupe_data.pop(0)
                if len(list_tupe_data[0][0]) != 3:
                    return "end=3,title=10,log=插入结果异常"
                # 程序执行到这里，算是已经成功了，只是需要通知节点和用户而已
                # 不管变没变，都要把新的数据和id发送给节点，让节点自己处理。删除旧的监听交给前面的
                str_e_data = self.send_info_to_equipment(
                    int(kk[4]), "A" + str(list_tupe_data[0][0][1]) + str_send[2:]
                )
                str_return = str_return + "修改成功,"
                # 在这里给节点发送监听信息
                if (
                    type(str_e_data) == str
                    and str_e_data[0] == "L"
                    and int(str_e_data[1:]) > 0
                ):
                    if str_return.find("需要重启节点") == -1:
                        str_return = str_return + "无需重启"
                else:
                    if str_return.find("需要重启节点") == -1:
                        str_return = str_return + "需要重启节点"
                if list_tupe_data[0][0][0] != int(kk[0]):
                    # 有重复的
                    str_return = str_return + ",内容重复，已去重"
                return "end=0,title=10,log=" + str_return
        return "end=3,title=10,log=接收节点不认可"

    def update(self, str_post_data):
        dict_post = self.str_to_dict(str_post_data)
        if dict_post == 0:
            print(str_post_data)
            return "end=1,title=5,log=无法解码"
        # 这里要加数据校验，啥都网数据库里加，
        print(str_post_data)
        # 对名称进行非法字符校验
        a = self.re_special_char.match(dict_post["name"])
        if a == None:
            return "end=4,title=5,log=数据非法1"
        try:
            # print(dict_post){'name': '未闻君名', 'email': '2275442930@qq.com', 'sex': '2','user_head_md5': 'dcda1eb07de0a72521140853f28b1488', 'user_head_end':'head'}
            self.mymysql.mysql_sql_update(
                self.mymysql.SQL_UPDATE_USERDATA,
                (
                    dict_post["name"],
                    int(dict_post["sex"]),
                    dict_post["user_head_md5"],
                    dict_post["user_head_end"],
                    dict_post["email"],
                ),
            )
            return "end=0,title=5,log=修改成功"
        except KeyError as e:
            MyPrintE.e_print(e)
            return "end=2,title=5,log=数据异常"
        except ValueError as e:
            MyPrintE.e_print(e)
            return "end=3,title=5,log=数据异常"

    def get_my_equipment(self, str_post_data):
        dict_post = self.str_to_dict(str_post_data)
        if dict_post == 0:
            return "end=1,title=8,log=无法解码"
        if "uid" in dict_post:
            dict_post["uid"] = int(dict_post["uid"])
            sql_data1 = self.mymysql.mysql_sql_select(
                self.mymysql.SQL_SELECT_UID_EIDX, (dict_post["uid"],)
            )
            str_send_data = "#"
            if len(sql_data1) > 0:
                for a in sql_data1:
                    str_send_data = (
                        str_send_data + str(a[0]) + ":" + str(a[0]) + "@" + a[1] + "#"
                    )
                return "end=0,log=" + str_send_data
            elif sql_data1 == []:
                return "end=1,title=8,log=未查询到您绑定设备"
        return "end=3,title=8,log=数据缺失"

    def get_equipment_data(self, str_post_data):
        # 用户请求单个设备提供的数据
        # 整理用户发来的数据并对内容校验，查看是否缺少内容
        dict_post = self.dict_jiao_yan(
            self.str_to_dict(str_post_data), self.LIST_USER_HAVE_NODE_NEED
        )
        if dict_post == 0:
            return "end=1,title=9,log=数据错误1"

        try:
            dict_post["eid"] = int(dict_post["eid"])
            dict_post["uid"] = int(dict_post["uid"])
        except ValueError as e:
            return "end=4,title=9,log=数据错误2"

        if dict_post["eid"] == 0 or dict_post["uid"] == 0:
            return "end=3,title=9,log=数据错误3"

        # 可以在这里插入用户身份的验证
        if self.uid_have_eid(dict_post["uid"], dict_post["eid"]) == False:
            return "end=2,title=10,log=越权操作"
        # 这里向设备发送信息请求，比较费时
        return "end=0,log=" + self.send_data_to_equipment(dict_post["eid"], "+GET")

    def get_equipment_info(self, str_post_data):
        # 整理用户发来的数据并对内容校验，查看是否缺少内容
        dict_post = self.dict_jiao_yan(
            self.str_to_dict(str_post_data), self.LIST_USER_HAVE_NODE_NEED
        )
        if dict_post == 0:
            return "end=2,title=9,log=数据错误1"

        try:
            dict_post["eid"] = int(dict_post["eid"])
            dict_post["uid"] = int(dict_post["uid"])
        except ValueError as e:
            return "end=3,title=9,log=数据错误2"

        if dict_post["eid"] == 0 or dict_post["uid"] == 0:
            return "end=4,title=9,log=数据错误3"

        # 可以在这里插入用户身份的验证
        if self.uid_have_eid(dict_post["uid"], dict_post["eid"]) == False:
            return "end=5,title=9,log=越权操作"

        # 这里向设备发送信息请求，比较费时
        str_info = self.send_info_to_equipment(dict_post["eid"], "INFO")
        if str_info != None:
            return "end=0,log=" + str_info
        # 没有请求到设备的描述的时候就只是返回一个 @ 触发加载机制，但是不传输实际数据
        # 如果传回其他end就会被多次显示，如果传回其他数据，可能导致解析异常
        return "end=0,title=9,log=@"

    def set_equipment_data(self, str_post_data):
        # 整理用户发来的数据并对内容校验，查看是否缺少内容
        dict_post = self.dict_jiao_yan(
            self.str_to_dict(str_post_data), self.LIST_USER_HAVE_NODE_NEED1
        )
        if dict_post == 0:
            return "end=1,title=10,log=数据错误"

        try:
            dict_post["eid"] = int(dict_post["eid"])
            dict_post["uid"] = int(dict_post["uid"])
        except ValueError as e:
            return "end=4,title=9,log=数据错误"

        # 身份验证的内容在这里插入
        if self.uid_have_eid(dict_post["uid"], dict_post["eid"]) == False:
            return "end=2,title=10,log=越权操作"
        return "end=0,log=" + self.send_data_to_equipment(
            dict_post["eid"], dict_post["send"]
        )

    def equipment_delete(self, str_post_data):
        dict_post = self.dict_jiao_yan(
            self.str_to_dict(str_post_data), self.LIST_LD_INSERT
        )  # 整理数据顺便校验
        if dict_post == 0:
            return "end=1,title=10,log=数据错误"
        # 传过来uid，查询的时候通过uid查询，查询联动表，返回格式化内容

        try:
            dict_post["uid"] = int(dict_post["uid"])
            dict_post["data"] = int(dict_post["data"])
        except ValueError:
            return "end=2,title=10,log=内容错误"

        if self.uid_have_eid(dict_post["uid"], dict_post["data"]) == False:
            return "end=4,title=10,log=越权操作"

        uid_have_eid = self.mymysql.mysql_sql_delete(
            self.mymysql.DEL_E_U_BANGDIN,
            (
                dict_post["uid"],
                dict_post["data"],
            ),
        )
        if uid_have_eid != 1:
            MyPrintE.log_print(
                "DEL_E_U_BANGDIN", (dict_post["uid"], dict_post["data"], uid_have_eid)
            )
            return "end=5,title=10,log=删除失败 > _ <"

        return "end=0,title=10,log=删除成功 ^ _ ^"

    def binding_equipment(self, str_post_data):
        dict_post = self.str_to_dict(str_post_data)
        if dict_post == 0:
            return "end=1,title=7,log=无法解码"
        if "chip_id" not in dict_post or "uid" not in dict_post:
            return "end=3,title=7,log=数据缺失"
        if dict_post["chip_id"] in dict_temporary_eid:
            # 设备的id暂存在内存里
            str_return = "+EID=" + str(dict_temporary_eid[dict_post["chip_id"]][0])
            dict_temporary_eid.pop(dict_post["chip_id"])
            return "end=0,log=" + str_return
        else:
            # 设备内存里不存在
            return "end=2,title=7,log=未找到"

    LIST_USER_LOGIN = ["uid", "email", "password"]

    def pw_login(self, str_post_data):
        """密码登录"""
        dict_post = self.dict_jiao_yan(
            self.str_to_dict(str_post_data), self.LIST_USER_LOGIN
        )  # 整理数据顺便校验
        if dict_post == 0:
            return "end=1,title=10,log=数据错误1"
        try:
            dict_post["uid"] = int(dict_post["uid"])
        except ValueError:
            return "end=2,title=10,log=数据错误2"

        sql_data1 = self.mymysql.mysql_sql_select(
            self.mymysql.SQL_SELECT_USERDATA3,
            (dict_post["uid"], dict_post["email"], dict_post["password"]),
        )
        print(sql_data1)
        if len(sql_data1) == 0:
            return "end=3,title=10,log=用户账号或者密码错误"
        # 更新用户登录时间
        new_time = int(time.time() * 1000)
        sql_str_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        net_md5 = hashlib.md5(sql_str_time.encode("utf-8")).hexdigest()
        # 更新数据库时间戳
        self.mymysql.mysql_sql_update(
            self.mymysql.SQL_UPDATE_LOGIN_YX1,
            (
                sql_str_time,
                dict_post["uid"],
                dict_post["email"],
            ),
        )
        #'SELECT id,name,sex,userheadmd5,userheadend FROM myuserdata WHERE
        # email=%s'
        # 					0 1 2 3 name 4 sex 5 userheadmd5 6 userheadend
        dict_u_net_md5[dict_post["uid"]] = net_md5, time.time()
        if None in sql_data1[0]:
            str_post_data = (
                "end=0&" + str(new_time) + "&" + net_md5 + "&" + str(sql_data1[0][0])
            )
        else:
            str_post_data = (
                "end=0&"
                + str(new_time)
                + "&"
                + net_md5
                + "&"
                + str(sql_data1[0][0])
                + "&"
                + sql_data1[0][1]
                + "&"
                + str(sql_data1[0][2])
                + "&"
                + sql_data1[0][3]
                + "&"
                + sql_data1[0][4]
            )
        # print("返回的数据" + str_post_data)
        return str_post_data

    # 密码验证码邮件
    LIST_YOUXIANG_PW_UPDATA = ["uid", "email", "password", "pw2"]

    def pw_updata(self, str_post_data):
        """修改密码"""
        dict_post = self.dict_jiao_yan(
            self.str_to_dict(str_post_data), self.LIST_YOUXIANG_PW_UPDATA
        )  # 整理数据顺便校验
        if dict_post == 0:
            return "end=1,title=10,log=数据错误1"
        try:
            dict_post["uid"] = int(dict_post["uid"])
        except ValueError:
            return "end=2,title=10,log=数据错误2"
        try:
            jy_data = dict_time[dict_post["uid"]]
        except KeyError:
            return "end=2,title=10,log=验证码过期"
        if jy_data[0] != dict_post["email"] or jy_data[2][:4] != dict_post["pw2"]:
            return "end=3,title=10,log=验证码错误"
        dict_time.pop(dict_post["uid"])
        self.mymysql.mysql_sql_update(
            self.mymysql.SQL_UPDATE_USERPW,
            (
                dict_post["password"],
                dict_post["uid"],
                dict_post["email"],
            ),
        )

        return "end=0,title=5,log=修改成功"

    def user_delete(self, str_post_data):
        """删除此用户"""
        return

    LIST_SELECT_OLD_DATE = ["uid", "eid", "mode", "min_data", "max_data"]

    def select_old_date(self, str_post_data):
        """查询历史数据"""
        dict_post = self.dict_jiao_yan(
            self.str_to_dict(str_post_data), self.LIST_SELECT_OLD_DATE
        )  # 整理数据顺便校验
        if dict_post == 0:
            dict_end = {
                "end": get_line().f_lineno,
                "file": __file__,
                "message": "数据内容错误",
            }
            return dict_end

        try:
            dict_post["uid"] = int(dict_post["uid"])
            dict_post["eid"] = int(dict_post["eid"])
        except ValueError:
            return {
                "end": get_line().f_lineno,
                "file": __file__,
                "message": "数据内容错误",
            }

        if self.uid_have_eid(dict_post["uid"], dict_post["eid"]) == False:
            return {
                "end": get_line().f_lineno,
                "file": __file__,
                "message": "越权操作",
            }
        if dict_post["mode"] == "day":
            sql_data1 = self.mymysql.mysql_sql_select(
                self.mymysql.SQL_SELECT_TIME_DATA,
                (
                    dict_post["eid"],
                    dict_post["min_data"],
                    dict_post["max_data"],
                ),
            )
            return {
                "end": 0,
                "file": __file__,
                "message": sql_data1,
            }
        else:
            return {
                "end": get_line().f_lineno,
                "file": __file__,
                "message": "未知 mode",
            }
        return dict()

    # 密码验证码邮件
    LIST_YOUXIANG_PW_UPDATA_SEND = ["uid", "email"]

    def pw_updata_send(self, str_post_data):
        """修改密码之前，发个验证码"""
        dict_post = self.dict_jiao_yan(
            self.str_to_dict(str_post_data), self.LIST_YOUXIANG_PW_UPDATA_SEND
        )  # 整理数据顺便校验
        if dict_post == 0:
            return "end=1,title=10,log=数据错误1"
        try:
            dict_post["uid"] = int(dict_post["uid"])
        except ValueError:
            return "end=1,title=10,log=数据错误2"

        data_time = int(time.time() * 1000)
        str_time_md5 = hashlib.md5(str(data_time).encode("utf-8")).hexdigest()
        if (
            dict_post["uid"] in dict_time
            and time.time() - dict_time[dict_post["uid"]][1] < 60
        ):
            time_out = int(60 - (time.time() - dict_time[dict_post["uid"]][1]))
            return f"end=1,title=10,log={time_out}秒后再试"
        # 0 邮箱服务正常，邮箱地址有问题 1 发送成功 2邮箱服务有问题
        # 发送时间的MD5前4位做验证码
        send_email_yanzhenma(dict_post["email"], str_time_md5[:4])
        print(str_time_md5[:4])
        dict_time[dict_post["uid"]] = [dict_post["email"], time.time(), str_time_md5]
        return "end=0,title=10,log=发送成功"

    def rename_equipment(self, str_post_data):
        # 取用户的id，和最后登录时间作为验证
        # {'uid': '1', 'eid': '21', 'name': '2号机te', 'oldname': '2号机'}
        dict_post = self.dict_jiao_yan(
            self.str_to_dict(str_post_data), self.LIST_RENAME_NODE
        )
        if dict_post == 0:
            return "end=1,title=11,log=数据错误1"
        if (len(dict_post["name"]) >= 40) or (len(dict_post["oldname"]) >= 40):
            return "end=1,title=11,log=数据错误2"
        # 对名字进行正则验证
        # a = self.re_special_char.match(dict_post["name"])
        # b = self.re_special_char.match(dict_post["oldname"])
        # if a == None or b == None:
        #     return "end=1,title=11,log=名称非法"
        try:
            dict_post["eid"] = int(dict_post["eid"])
            dict_post["uid"] = int(dict_post["uid"])
        except ValueError as e:
            MyPrintE.e_print(e, "dict_post=" + str(dict_post))
            return "end=1,title=11,log=数据错误3"
        a = self.mymysql.mysql_sql_update(
            self.mymysql.SQL_UPDATE_SETNAME2,
            (
                dict_post["name"],
                dict_post["uid"],
                dict_post["eid"],
            ),
        )
        if a == None or a != 1:
            MyPrintE.log_print(
                "rename_equipment",
                (dict_post["name"], dict_post["uid"], dict_post["eid"], a),
            )
            return "end=1,title=11,log=更新数据失败"
        return "end=0,title=11,log=修改成功"

    def do_POST_new(self, str_post_name, str_post_data):
        return self.DICT_POST_NEW[str_post_name](str_post_data)

    def do_POST(self):
        """
        规定
                处理成功		end=0,log=原先的返回信息
                处理失败(n>0)	end=n,log=提示信息
        """
        global dict_share_md5, dict_time, dict_u_net_md5
        str_post_path = str(self.path)
        # print(self.headers)
        print(
            time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            self.client_address,
            str_post_path,
            end="	",
        )
        # print(self.client_address)#客户端ip和端口号
        # print("文件的长度"+self.headers['content-length'])
        if int(self.headers["content-length"]) > 1048576:
            self.send_content("end=1,log=数据过大，限制为1MB", 200)
            return
        req_datas = self.rfile.read(int(self.headers["content-length"]))  # 按长度读取post数据
        # str_post_data = ""
        str_post_name = self.re_post_name.findall(str_post_path)
        if len(str_post_name) == 1 and str_post_name[0] in self.DICT_POST_NEW:
            str_post_data = self.req_datas_to_string2(req_datas, str_post_path)
            if str_post_data == None:
                self.send_content("dataerror")
                return
            str_post_data, str_net_md5 = str_post_data
            str_post_data = self.do_POST_new(str_post_name[0], str_post_data)
            if type(str_post_data) == str:
                if len(str_post_data) < 300:
                    print(str_post_data)
                assert str_post_data.startswith("end=") == True
            elif type(str_post_data) == dict:
                assert "end" in str_post_data
            else:
                assert False
            self.send_content2(str_post_data, str_net_md5)
            return

        if str_post_path.startswith("/email_log_login=") == True:
            userdata_email_md5 = str_post_path[17:]
            print(userdata_email_md5)
            if len(userdata_email_md5) != 32:
                self.send_content("error", 404)
                return
            # 用户邮箱的md5剪切成功->合法请求
            # 用户邮箱的md5剪切成功->合法请求
            if userdata_email_md5 not in dict_time:
                # 验证码过期
                self.send_content("end=1,title=2,log=该邮箱没有验证码")
                return

            print("key=" + dict_time[userdata_email_md5][2][:4])
            str_key = hashlib.md5(
                (
                    dict_time[userdata_email_md5][2][:4]
                    + dict_time[userdata_email_md5][0]
                ).encode("utf-8")
            ).hexdigest()
            str_post_data = Mykeyer.keyer_bytes_get_str(str_key, req_datas)
            if str_post_data == None or str_post_data == 0:
                self.send_content("end=2,title=2,log=验证码错误1")
                return

            dict_post = self.dict_jiao_yan(
                self.str_to_dict(str_post_data), self.LIST_YOUXIANG_LOGIN
            )  # 整理数据顺便校验
            if dict_post == 0:
                print(str_post_data, dict_post)
                self.send_content("end=3,title=2,log=验证码错误2")
                return

            dict_time.pop(userdata_email_md5)
            # print("解析安卓传来数据成功")
            # 从post数据里抠出邮箱，校验MD5，检验验证码解析出的数据

            if (
                hashlib.md5(dict_post["email"].encode("utf-8")).hexdigest()
                != userdata_email_md5
            ):
                print(str_post_data)
                self.send_content("end=3,title=2,log=验证码错误3")
                return
            """post数据：
				接受：
					发送用户输入的验证码和get邮箱返回的验证码
					用户的邮箱
				发送：
					uid
					name
					head_md5
					head_end
					sex
					net_md5		//用户用于向服务器发起请求的请求码
					new_time 	//服务器最后登录时间"""
            # 将数据库的用户信息发送给用户

            sql_data1 = self.mymysql.mysql_sql_select(
                self.mymysql.SQL_SELECT_USERDATA1, (dict_post["email"],)
            )
            int_uid = int(sql_data1[0][0])
            if int_uid < 1:
                print(sql_data1)
                self.send_content("end=4,title=1,log=数据库查询失败")
                return
            # 更新用户登录时间
            new_time = int(time.time() * 1000)
            sql_str_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            net_md5 = hashlib.md5(sql_str_time.encode("utf-8")).hexdigest()
            # 更新数据库时间戳
            self.mymysql.mysql_sql_update(
                self.mymysql.SQL_UPDATE_LOGIN_YX1,
                (
                    sql_str_time,
                    int_uid,
                    dict_post["email"],
                ),
            )
            #'SELECT id,name,sex,userheadmd5,userheadend FROM myuserdata WHERE
            # email=%s'
            # 					0 1 2 3 name 4 sex 5 userheadmd5 6 userheadend
            print(sql_data1)
            dict_u_net_md5[int_uid] = net_md5, time.time()
            if None in sql_data1[0]:
                str_post_data = (
                    "end=0&"
                    + str(new_time)
                    + "&"
                    + net_md5
                    + "&"
                    + str(sql_data1[0][0])
                )
            else:
                str_post_data = (
                    "end=0&"
                    + str(new_time)
                    + "&"
                    + net_md5
                    + "&"
                    + str(sql_data1[0][0])
                    + "&"
                    + sql_data1[0][1]
                    + "&"
                    + str(sql_data1[0][2])
                    + "&"
                    + sql_data1[0][3]
                    + "&"
                    + sql_data1[0][4]
                )
            print("返回的数据" + str_post_data)
            self.send_content2(str_post_data, str_key)
            return
        elif str_post_path.startswith("/email_log_zhuce") == True:
            userdata_email_md5 = str_post_path[16:]
            print(userdata_email_md5)
            if len(userdata_email_md5) != 32:
                # 非法请求
                self.send_content("error", 404)
                return

            # 用户邮箱的md5剪切成功->合法请求
            if userdata_email_md5 not in dict_time:
                # 验证码过期
                self.send_content("end=1,title=2,log=该邮箱没有验证码")
                return
            print("key=" + dict_time[userdata_email_md5][2][:4])
            str_key = hashlib.md5(
                (
                    dict_time[userdata_email_md5][2][:4]
                    + dict_time[userdata_email_md5][0]
                ).encode("utf-8")
            ).hexdigest()
            str_post_data = Mykeyer.keyer_bytes_get_str(str_key, req_datas)
            if str_post_data == None or str_post_data == 0:
                self.send_content("end=2,title=2,log=验证码错误1")
                return

            # 从post数据里抠出邮箱，校验MD5，检验验证码解析出的数据
            dict_post = self.dict_jiao_yan(
                self.str_to_dict(str_post_data), self.LIST_ZHUCE
            )  # 整理数据顺便校验
            if dict_post == 0:
                print(str_post_data, dict_post)
                self.send_content("end=3,title=2,log=验证码错误2")
                return
            if (
                hashlib.md5(dict_post["email"].encode("utf-8")).hexdigest()
                != userdata_email_md5
            ):
                # 校验解析出来的邮箱md5和连接的md5是否相同
                self.send_content("end=3,title=2,log=验证码错误3")
                return
            # 发过来的数据没有问题，验证通过
            dict_time.pop(userdata_email_md5)
            """post数据：
				接受：
					邮箱和密码
				发送：
					net_md5		//用户用于向服务器发起请求的请求码
					new_time 	//服务器最后登录时间"""

            new_time = int(time.time() * 1000)
            sql_str_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            net_md5 = hashlib.md5(sql_str_time.encode("utf-8")).hexdigest()
            # 将用户信息入库
            # print("插入开始",dict_post["email"],dict_post["password1"],new_time)
            uid = self.mymysql.mysql_sql_insert(
                self.mymysql.SQL_INSERT_EMAIL,
                (dict_post["email"], dict_post["password1"], sql_str_time),
            )
            if uid == None:
                print(
                    time.strftime("%Y-%m-%d %H:%M:%S  ", time.localtime()),
                    "uid 插入错误",
                    (dict_post["email"], dict_post["password1"], sql_str_time),
                )
                self.send_content("end=4,title=2,log=数据库插入失败")
                return
            dict_u_net_md5[uid] = net_md5, time.time()
            str_post_data = "end=0&" + str(new_time) + "&" + net_md5 + "&" + str(uid)
            self.send_content2(str_post_data, str_key)
            return
        elif str_post_path.startswith("/email_send_login") == True:
            # 字节转换为字符串
            str_post_data = self.req_datas_to_string(req_datas)
            if str_post_data == 0:
                self.send_content("end=1,title=3,log=无法解码")
                return
            try:
                user_email = self.re_email.findall(str_post_data)[0][6:]
            except IndexError as e:
                MyPrintE.e_print(
                    e, "/email_send_login  email 提取出错 data=" + str_post_data
                )
                self.send_content("end=2,title=3,log=无法解码")
                return
            # 加载数据
            sql_data1 = self.mymysql.mysql_sql_select(
                self.mymysql.SQL_SELECT_EMAIL, (user_email,)
            )
            if sql_data1 != None and sql_data1[0][0] != 0:
                data_time = int(time.time() * 1000)
                str_time_md5 = hashlib.md5(str(data_time).encode("utf-8")).hexdigest()
                user_email_md5 = hashlib.md5(user_email.encode("utf-8")).hexdigest()
                if (
                    user_email_md5 in dict_time
                    and time.time() - dict_time[user_email_md5][1] < 60
                ):
                    time_out = int(60 - (time.time() - dict_time[user_email_md5][1]))
                    self.send_content(f"end=4,title=3,log={time_out}秒后再试")
                    return
                # 发送时间的MD5前4位做验证码
                send_email_yanzhenma(user_email, str_time_md5[:4])
                dict_time[user_email_md5] = [user_email, time.time(), str_time_md5]
                print(user_email, "   ", str_time_md5[:4])
                self.send_content("end=0,log=" + str_time_md5[-4:])
                return
            else:
                self.send_content("end=3,title=3,log=邮箱未注册，请点击注册按键进行注册")
                return
        elif str_post_path.startswith("/email_send_zhuce") == True:
            # 字节转换为字符串
            str_post_data = self.req_datas_to_string(req_datas)
            if str_post_data == 0:
                self.send_content("end=1,title=4,log=无法解码")
                return
            print(str_post_data)
            try:
                user_email = self.re_email.findall(str_post_data)[0][6:]
            except IndexError as e:
                MyPrintE.e_print(e)
                self.send_content("end=2,title=4,log=无法解码")
                return
            # 查询邮箱注册信息
            sql_data1 = self.mymysql.mysql_sql_select(
                self.mymysql.SQL_SELECT_EMAIL, (user_email,)
            )
            if sql_data1 != None and sql_data1[0][0] == 0:
                # 邮箱没有注册过，发送邮件准备注册
                print(user_email)
                data_time = int(time.time() * 1000)
                str_time_md5 = hashlib.md5(str(data_time).encode("utf-8")).hexdigest()
                user_email_md5 = hashlib.md5(user_email.encode("utf-8")).hexdigest()
                if (
                    user_email_md5 in dict_time
                    and time.time() - dict_time[user_email_md5][1] < 60
                ):
                    time_out = int(60 - (time.time() - dict_time[user_email_md5][1]))
                    self.send_content(f"end=4,title=3,log={time_out}秒后再试")
                    return
                # 0 邮箱服务正常，邮箱地址有问题 1 发送成功 2邮箱服务有问题
                # 发送时间的MD5前4位做验证码
                send_email_yanzhenma(user_email, str_time_md5[:4])
                print(str_time_md5[:4])
                dict_time[hashlib.md5(user_email.encode("utf-8")).hexdigest()] = [
                    user_email,
                    time.time(),
                    str_time_md5,
                ]
                self.send_content("end=0,log=" + str_time_md5[-4:])
                return
            else:
                # 邮箱注册过
                self.send_content("end=3,title=4,log=邮箱已注册，可以使用邮箱接收验证码登录")
                return
        elif str_post_path.startswith("/pic=") == True:
            if self.re_md5head.findall(str_post_path)[0] == str_post_path:
                # pic_have_id=os.system('dir head | find /i "'+str_post_path[5:]+'" && echo
                # have')
                if os.path.exists("./head/" + str_post_path[5:]):
                    # print(str_post_path[5:]+" 文件存在")
                    self.send_content("update 1")
                    return
                elif type(req_datas) == bytes:
                    f = open("head/" + str_post_path[5:], "wb")
                    f.write(req_datas)
                    f.close
                    self.send_content("update 1")
                    return
                else:
                    self.send_content("update error 2")
                    return
        else:
            self.send_content("post error 2", 404)
            return


class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    pass


if __name__ == "__main__":
    # print("主线程pid=",os.getpid())
    if os.path.exists("./head") == False:
        print("缺少head文件夹,是否新建？yes？")
        if input() == "yes":
            os.mkdir("head", 755)
    init_email_passwd()
    Blackip.black_ip_init()
    new_a_thread_clear_dict_time()
    open_TCP_UDP()
    httpd = ThreadingHTTPServer(("", 8080), RequestHandler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()
