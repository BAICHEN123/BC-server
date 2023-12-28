"""
本文件的作用为：
11		把 dict_TCP 的对象单个tcp进行封装，每次修改 dict_TCP 里的存储结构就要重写全部的函数，实在是太累了
			将常用操作方式封装起来
			封装需要实现主函数的尽可能多的功能
			设计目标：
			1	储存单个tcp链接
			2	储存链接对应的设备的粗略信息
			3	封装链接的提取和存储
			4	封装设备的通讯过程？？？

//14.5	dict_TCP 移动并封装到 MyETcp.py 里
"""
import socket
import MyPrintE
import time
import re
from Mymysql import Mymysql
from MySmtp import send_email_warning
from MySmtp import email_send_str


dict_TCP = dict()


"""记录一个用户某一时刻离线的所有设备"""


class UserDieE:
    """"""

    def __init__(self, int_uid):
        assert type(int_uid) == int
        self.uid = int_uid
        self.email = None
        self.name = None
        self.elist = list()

    def add_die_e(self, ename):
        assert type(ename) == str
        self.elist.append(ename)

    def send_email(self, sql, str_time):
        assert type(sql) == Mymysql
        assert len(self.elist) > 0
        if self.email == None or self.name == None:
            # 使用uid从数据库里查
            sql_data = sql.mysql_sql_select(
                "select email,name from myuserdata where id=%s", (self.uid,)
            )
            assert len(sql_data) == 1
            sql_data = sql_data[0]
            self.email = sql_data[0]
            self.name = sql_data[1]
        str_list_e = "【" + "】、【".join(self.elist) + "】"
        # 【self.name】您好，您的【设备名】、【设备名】、【设备名】、【设备名】已经离线超过30分钟。当前时间{str_time}
        str_message = f"{self.name}您好，您的{str_list_e}已经离线。时间{str_time}"
        email_send_str(self.email, str_message)


class DictTcp:
    STR_TIME = "Time%Y-%m-%d %w %H:%M:%S	"

    def __init__(self):
        global dict_TCP
        if type(dict_TCP) != dict:
            dict_TCP = dict()

    def set_e_tcp(self, int_eid, tcp_link, bm):
        global dict_TCP
        assert type(int_eid) == int
        assert type(bm) == str
        assert type(tcp_link) == socket.socket
        old_msg = None
        try:
            old_msg = dict_TCP[int_eid]
            assert type(old_msg) == MyETcp
            # 将旧的警告继承下去
            old_msg = old_msg.dict_msg
        except KeyError:
            old_msg = None
        dict_TCP[int_eid] = MyETcp(int_eid, tcp_link, bm, old_msg)
        return True

    def get_e_tcp(self, int_eid):
        global dict_TCP
        assert type(int_eid) == int
        try:
            myetcp = dict_TCP[int_eid]
        except KeyError as e:
            return None
        if type(myetcp) == MyETcp:
            return myetcp
        return None

    def e_die_send_emil(self, list_die):
        assert type(list_die) == list
        if len(list_die) == 0:
            return
        # 告知用户设备状态变动
        sql = Mymysql()
        dict_email_elist = dict()
        # 将离线的设备按用户邮箱的方式排列出来
        for eid in list_die:
            assert type(eid) == int
            list_sql = sql.mysql_sql_select(
                "select a.id,b.name from myuserdata a,user_and_shebei b where b.eid=%s and b.uid=a.id",
                (eid,),
            )
            # [(email,user name,e name)]
            for item in list_sql:
                if item[0] not in dict_email_elist:
                    dict_email_elist[item[0]] = UserDieE(item[0])
                dict_email_elist[item[0]].add_die_e(item[1])

        str_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        for id, item in dict_email_elist.items():
            assert type(item) == UserDieE
            try:
                item.send_email(sql, str_time)
            except Exception as e:
                MyPrintE.e_print(e)

    def clean_dict_TCP_olddata(self):
        global dict_TCP
        if len(dict_TCP) == 0:
            return
        list_die = list()
        str_heart = time.strftime(self.STR_TIME, time.localtime())
        str_data = time.strftime("%Y-%m-%d")
        str_time = time.strftime("%H:%M:%S")
        list_eid_data = list()
        dict_TCP_copy = dict_TCP.copy()
        # RuntimeError: dictionary changed size during iteration
        for dict_i, elink in dict_TCP_copy.items():
            assert type(elink) == MyETcp, "claer_dict_TCP_olddata type error"
            if elink.do_heart_beat(str_heart) == False:
                # 是否离线，是否需要邮件提醒用户
                if elink.is_line_out() == True and elink.send_email_fig() == True:
                    list_die.append(dict_i)
                # 是否超过暂存时间，超过暂存时间，就从字典中移除
                if elink.is_die():
                    dict_TCP.pop(dict_i)
            elif elink.bytes_last_data and len(elink.bytes_last_data) > 0:
                str_last_data = elink.bytes_to_str(elink.bytes_last_data)
                if elink.bytes_last_data[0] == 9:
                    str_last_data = str_last_data.replace("\t", "#", 1)
                list_eid_data.append((dict_i, str_last_data, str_data, str_time))

        print(" dict_TCP=", list(dict_TCP.keys()), end="")
        if len(list_eid_data) > 0:
            sql = Mymysql()
            end = sql.mysql_sql_inserts(sql.SQL_INSERT_TIME_DATA, list_eid_data)
            print(" SQL_INSERT_TIME_DATA end=", end, end="  ")
        self.e_die_send_emil(list_die)


""""""
# 规定链接正在工作是True


class MyETcp:
    """
    单个设备的报错信息维护使用一个字典来维护
    字典储存报错的id
    dict_msg[1]=time.time()

    节点设备的报错信息使用唯一id，然后再对逐条区分使用 m w e 。

    """

    __re_msg = re.compile("([mwe])(\d+)")
    __re_msg_data = re.compile("^#([^#]+)#$")

    def __init__(self, INT_EID, socket_Node, str_BM, dict_msg=None):
        """
        socket_Node	tcp链接对象
        str_BM		设备的编码
        """
        assert (
            type(socket_Node) == socket.socket
        ), "ETcp type(socket_Node)!=socket.socket"
        assert type(str_BM) == str, "ETcp type(str_BM)!=str"
        assert type(INT_EID) == int, "ETcp type(INT_EID)!=int"
        self.socket_node = socket_Node
        self.INT_EID = INT_EID
        self.str_bm = str_BM
        self.line_out_send_email_fig = False
        if dict_msg == None:
            self.dict_msg = dict()
        else:
            assert type(dict_msg) == dict
            self.dict_msg = dict_msg
        self.working_status = False
        self.time_out = time.time()
        self.socket_node.settimeout(None)  # 设置为永不超时
        self.bytes_last_data = None

    """销毁对象之前先关闭链接"""

    def __del__(self):
        if type(self.socket_node) == socket.socket:
            try:
                self.socket_node.close()
            except:
                self.socket_node = None

    """添加了异常处理的tcp数据发送"""

    def e_send(self, str_data, float_time_out_s=3.0):
        assert type(str_data) == str, "ETcp type(str_data)!=str"
        assert (
            type(float_time_out_s) == float or type(float_time_out_s) == int
        ) and float_time_out_s >= 0, (
            "ETcp type(float_time_out_s)!=float or float_time_out_s<0"
        )
        if self.socket_node == None:  # 判断是否为空
            return False
        self.socket_node.settimeout(float_time_out_s)  # 设置等待时间上限
        try:
            self.socket_node.send(str_data.encode(self.str_bm))
        except BrokenPipeError as e:
            # 管道已经被破坏
            # MyPrintE.e_print(e,'eid='+str(self.INT_EID))
            self.socket_node = None
            return False
        except ConnectionResetError as e:
            # 管道已经被关闭
            # MyPrintE.e_print(e,'eid='+str(self.INT_EID))
            self.socket_node = None
            return False
        except TimeoutError as e:
            # MyPrintE.e_print(e,'eid='+str(self.INT_EID))#发生系统级别的超时
            self.socket_node = None
            return False
        except Exception as e:
            MyPrintE.e_print(e, "eid=" + str(self.INT_EID))  # 发生系统级别的超时
            self.socket_node = None
            return False
        return True

    """添加了异常处理的tcp数据请求"""

    def __e_recv(self, float_time_out_s=3.0):
        assert (
            type(float_time_out_s) == float or type(float_time_out_s) == int
        ) and float_time_out_s >= 0, (
            "ETcp type(float_time_out_s)!=int or float_time_out_s<0"
        )
        if self.socket_node == None:  # 判断是否为空
            return None
        self.socket_node.settimeout(float_time_out_s)  # 设置等待时间上限
        bytes_TCP_data = None
        try:
            bytes_TCP_data = self.socket_node.recv(1024)  # 接收套接字
            self.time_out = time.time()  # 更新最后一次收到数据的时间
            if len(bytes_TCP_data) > 0 and bytes_TCP_data[0] in [9, 35]:
                self.bytes_last_data = bytes_TCP_data
        except ConnectionResetError as e:
            # 管道已经被关闭
            # MyPrintE.e_print(e,'eid='+str(self.INT_EID))
            self.socket_node = None
            return None
        except BlockingIOError as e:
            if float_time_out_s != 0:  # 一般发生在非阻塞状态下，没有缓存可读或者没有缓存可以写，链接还是可以使用的
                # MyPrintE.e_print(e,'eid='+str(self.INT_EID))
                self.socket_node = None
                return None
        except BrokenPipeError as e:
            # 管道已经被关闭
            # MyPrintE.e_print(e,'eid='+str(self.INT_EID))
            self.socket_node = None
            return None
        except socket.timeout as e:
            # MyPrintE.e_print(e,'socket.timeout eid='+str(self.INT_EID))
            # 这里的超时未收到数据不一定是链接失效，没有清除的必要。
            # 这里将链接关闭会导致没有更新协议的设备在收到未定义的指令之后（没有任何回复）链接关闭不断的重新建立tcp链接
            # self.socket_node.close()
            # self.socket_node=None
            self.socket_node.settimeout(None)
            return None
        except TimeoutError as e:
            # MyPrintE.e_print(e,'eid='+str(self.INT_EID))#发生系统级别的超时
            self.socket_node = None
            return None
        except OSError as e:
            MyPrintE.e_print(e, "eid=" + str(self.INT_EID))
            self.socket_node = None
            return None
        except Exception as e:
            MyPrintE.e_print(e, "eid=" + str(self.INT_EID))
            self.socket_node = None
            return None

        # 设置为永不超时
        self.socket_node.settimeout(None)

        return bytes_TCP_data

    """一个指令的执行及结果的返回
	//stm32采用at指令控制esp8266联网时无法发送 '\0',所以决定使用'\t'替换'\0'作为心跳包的标志
	return：	False	链接失效
				None	超时没有数据
				type()=bytes 正常数据
	"""

    def send_data_to_equipment(self, str_send_data, float_time_out_s=3.0):
        if self.socket_node == None:  # 判断是否为空
            return False
        time_out = 0
        while self.working_status == True:  # 等待其他线程释放此连接
            time.sleep(0.1)
            time_out = time_out + 0.1
            if time_out > float_time_out_s:
                return None
        if self.socket_node == None:  # 判断是否为空
            return False
        self.working_status = True  # 声明占有此连接
        # 清除掉所有的旧数据
        self.__clear_recv_cache()  # 返回值就不管了，反正后面还会进行非空判断
        # 发送指令#send只是把数据复制到缓存里面去，设置时间没啥卵用
        if self.e_send(str_send_data) == False:
            self.working_status = False  # 设置为空闲状态
            return False
        # 接收返回的数据
        start_time = time.time()
        float_time_out_s = float_time_out_s - time_out  # 减去获取链接阻塞用掉的时间，剩下的时间
        tcp_date = self.__e_recv(float_time_out_s)
        while type(tcp_date) == bytes and len(tcp_date) > 0:
            if tcp_date[0] == 35:  # '#' 的ASCII是35
                break
            elif tcp_date[0] == 64:  #'@'==64
                break
            elif tcp_date[0] == 76:  #'L'==76
                break
            elif tcp_date[0] == 68:  #'D'==68
                break
            elif tcp_date[0] == 9:  # '\t' 的ASCII是9
                # 重新计算还可以阻塞多少S
                float_time_out_s = float_time_out_s - (time.time() - start_time)
                if float_time_out_s < 0:
                    # 时间不够了
                    tcp_date = None
                    break
                start_time = time.time()  # 重新掐表
                tcp_date = self.__e_recv(float_time_out_s)
            else:
                MyPrintE.log_print("send_data_to_equipment else 1")
                print(tcp_date)
                tcp_date = None
                break
        self.working_status = False  # 设置为空闲状态
        return tcp_date

    """清除掉tcp所有的缓存"""

    def __clear_recv_cache(self):
        if self.socket_node == None:  # 判断是否为空
            return False
        tcp_data = self.__e_recv(0)
        while type(tcp_data) == bytes:
            tcp_data = self.__e_recv(0)
        # 连接为空，说明链接断裂了
        return self.socket_node != None

    """处理心跳包的缓存内容，并返回数据"""

    def do_heart_beat(self, str_data):
        if self.socket_node == None:  # 判断是否为空
            return False
        # 如果当前的状态是空闲的就清除数据
        error_i = 0  # 我下面这个循环会出问题
        while self.working_status == False and self.socket_node != None:
            tcp_data = self.__e_recv(0)
            if tcp_data == None:
                break
            tcp_data = None
            error_i = error_i + 1
            assert error_i < 1000, "do_heart_beat error_i >1000"

        # 超时太久就丢掉了，不再持有这个过期的链接了
        if self.is_line_out() == True:
            self.socket_node = None
            return False
        self.e_send(str_data)
        if self.socket_node == None:  # 判断是否为空,空则说明链接裂开了
            # MyPrintE.log_print('do_heart_beat eid='+str(self.INT_EID))
            return False
        return True

    """将字节内容转换成字符串"""

    def bytes_to_str(self, bytes_data):
        if type(bytes_data) == bytes:
            try:
                return bytes_data.decode(self.str_bm)
            except UnicodeDecodeError as e:
                MyPrintE.e_print(e, "eid=" + str(self.INT_EID))
                return None
        else:
            return None

    """
	当收到udp消息之后会调用此函数
	str_jb		为 14.4 中描述的 m,w,e
	int_jb_id	为节点设备定义的错误id，用来防止单个错误重复向用户报错
	str_message	为节点提交的警告内容

	处理要求：
		1、携带错误级别和错误id返回一个 tcp消息，告知节点设备，我已收到你的请求，不要再重复发送了
		2、	m：		进行消息校验，权限校验，然后对绑定设备发送相应的指令，完成联动
			w:		将携带的 str_message 转发给用户
			e:		将携带的 str_message 转发给用户，并在服务器记录错误
		3、记录设备的 str_jb，int_jb_id 以及到达服务器的时间，在确定对用户的发送频率之后，按频率处理
	处理流程：
		1、获取所有的报错信息（id，级别，警告内容）
		2、不同级别的信息交给不同的函数去处理，是否在服务器记录等操作
		3、


	"""

    def do_udp_data(self, int_EID, int_CHIP_ID, str_message):
        assert type(int_EID) == int and int_EID == self.INT_EID
        assert type(int_CHIP_ID) == int
        assert type(str_message) == str
        list_msg = self.__re_msg.findall(str_message)
        list_message = list()
        str_send_message_data = ""
        for tuple_item in list_msg:
            str_jb = tuple_item[0]  # 级别
            int_jb_id = int(tuple_item[1])  # 级别id
            if int_jb_id not in self.dict_msg:
                self.dict_msg[int_jb_id] = 0

            # 告知节点我已知晓,并请求回复，验证此警告是否存在
            bytes_tcp_data = self.send_data_to_equipment(str_jb + str(int_jb_id))
            # print(bytes_tcp_data)
            str_message = self.bytes_to_str(bytes_tcp_data)
            # print(str_message)
            if type(str_message) != str:
                continue
            # print(str_message)
            str_message = self.__re_msg_data.match(str_message)
            if type(str_message) != re.Match:
                MyPrintE.log_print("未采集到报错信息", (str_jb, int_jb_id, str_message))
                continue
            str_message = str_message.group(1)

            # 尝试一次性打包所有的在报错信息，发给用户
            # m指令每次都处理，不受时间的限制，因为是发送给其他节点的

            if str_jb == "m":
                # print("str_message",str_message)
                if int(str_message) == int_jb_id:
                    self.__do_message(int_jb_id)
                    continue
            # 我这里把相同报错的时间间隔写死了，以后的话可以查数据库，根据用户的配置来定制
            elif time.time() - self.dict_msg[int_jb_id] < 3600:
                MyPrintE.log_print("时候未到", (self.dict_msg[int_jb_id], str_message))
                pass
            elif str_jb == "w":
                self.dict_msg[int_jb_id] = time.time()
                self.__do_warning(int_jb_id, str_message)
                list_message.append(str(int_jb_id) + "</td><td>" + str_message)
                pass
            elif str_jb == "e":
                self.dict_msg[int_jb_id] = time.time()
                self.__do_error(int_jb_id, str_message)
                list_message.append(str(int_jb_id) + "</td><td>" + str_message)
                pass
            else:
                MyPrintE.log_print("do_udp_data else error")
        if len(list_message) > 0:
            str_send_message_data = (
                "<tr><td>ID</td><td>错误信息</td></tr><tr><td>"
                + "</td></tr><tr><td>".join(list_message)
                + "</td></tr>"
            )
            self.__send_waring_email(str_send_message_data)
            pass

    """处理指令消息"""

    def __do_message(self, int_fid):
        assert type(int_fid) == int
        # 阉割了，没有详细指令了，直接把fid传过来，验证两次fid一样就算是成功了。
        # 根据发送过来的fid，找到所有对应的jid，发送指令
        sql = Mymysql()
        etcp = DictTcp()
        list_tuple = sql.mysql_sql_select(sql.FID_SELECT_J, (int_fid,))

        # 如果这个监听是多余的，就从数据库和单片机里删除
        if len(list_tuple) == 0:
            # 从数据库删除
            kk = sql.mysql_sql_delete(sql.DELTET_NONE_FAQI, (int_fid,))
            # 从单片机删除
            str_send = "D" + str(int_fid)
            str_e_data = self.send_data_to_equipment(str_send)
            if str_e_data != str_send:
                MyPrintE.log_print(
                    "str_e_data!= str_send", (self.INT_EID, str_send, str_e_data)
                )
            return

        # 将相同设备的指令拼接到一起发送，如果指令长度超出 1024就会崩溃
        dict_eid_data = dict()
        for item in list_tuple:
            if item[0] in dict_eid_data:
                dict_eid_data[item[0]] = (
                    dict_eid_data[item[0]] + item[1] + ":" + item[2]
                )
                # 长度最够长就先发送出去，太长的话一次发不完
                if len(dict_eid_data[item[0]]) > 250:  # 250*3<<<1024,300*3=900，接近临界值了
                    et = etcp.get_e_tcp(item[0])
                    if type(et) != MyETcp:
                        dict_eid_data.pop(item[0])  # 设备不在线，发不了，上线的时候会在其他位置重新发送
                        continue
                    str_req = et.send_data_to_equipment(dict_eid_data[item[0]])
                    if type(str_req) != bytes:
                        MyPrintE.log_print(
                            "__do_message", (str_req, item[0], dict_eid_data[item[0]])
                        )
                    dict_eid_data.pop(item[0])  # 如果刚好发送完，就不用启动下一个循环了
            else:
                dict_eid_data[item[0]] = item[1] + ":" + item[2]
        # 将剩余的内容发送出去
        for eid, data in dict_eid_data.items():
            et = etcp.get_e_tcp(eid)
            if type(et) != MyETcp:
                continue
            str_req = et.send_data_to_equipment(data)
            if type(str_req) != bytes:
                MyPrintE.log_print("__do_message", (str_req, eid, data))
        return

    """处理警告消息"""

    def __do_warning(self, int_jb_id, str_message):
        assert type(int_jb_id) == int
        assert type(str_message) == str
        return

    """处理错误消息"""

    def __do_error(self, int_jb_id, str_message):
        assert type(int_jb_id) == int
        assert type(str_message) == str
        return

    SELECT_EMAIL_ENAME = "select email,a.name,b.name from myuserdata a,user_and_shebei b where b.eid=%s and b.uid=a.id"

    def __send_waring_email(self, str_message):
        sql = Mymysql()
        list_sql_email = sql.mysql_sql_select(self.SELECT_EMAIL_ENAME, (self.INT_EID,))
        # [('1020005654@qq.com',uname，ename), ('2275442930@qq.com',), ('2280057905@qq.com',)]
        for item in list_sql_email:
            send_email_warning(item[0], item[1], item[2], str_message)
            MyPrintE.log_print(
                " __do_warning ", ((item[0], item[1], item[2], str_message))
            )
        return

    def send_jiantin(self, sql):
        assert type(sql) == Mymysql
        ld_list = sql.mysql_sql_select(sql.SELECT_EID_LD, (self.INT_EID,))
        i = 0
        msg = ""
        for item in ld_list:
            # "A10#@test1#>#20\t"
            # b.id,f.aname,f.afuhao,f.did,f.canzhi
            i = i + 1
            msg = msg + f"A{item[0]}#{item[1]}#{item[2]}#{item[4]}\t"
            if i == 3:
                i = 0
                str_req = self.send_data_to_equipment(msg)
                if type(str_req) != bytes:
                    MyPrintE.log_print(" send_jiantin ", (self.INT_EID, msg, str_req))
                # print("str_req",str_req)
                # 对str_req处理，可以获得监听的插入结果
                msg = ""
        if msg != "":
            str_req = self.send_data_to_equipment(msg)
            if type(str_req) != bytes:
                MyPrintE.log_print(" send_jiantin ", (self.INT_EID, msg, str_req))
        self.re_jiantin(sql)

    def re_jiantin(self, sql):
        assert type(sql) == Mymysql
        ld_list = sql.mysql_sql_select(sql.SELECT_FID_DO_EID, (self.INT_EID,))
        i = 0
        msg = ""
        dict_eid_data = dict()
        for item in ld_list:
            if item[1] in dict_eid_data:
                dict_eid_data[item[1]] = dict_eid_data[item[1]] + "C" + str(item[0])
            else:
                dict_eid_data[item[1]] = "C" + str(item[0])
        kk = DictTcp()
        for eid, data in dict_eid_data.items():
            link = kk.get_e_tcp(eid)
            if type(link) != MyETcp:
                continue
            assert len(data) < 1000
            str_req = self.bytes_to_str(link.send_data_to_equipment(data))
            if type(str_req) != str:
                MyPrintE.log_print(" re_jiantin 1 ", (eid, data, str_req))
                continue
            if str_req.startswith("#") == False or int(str_req[1:]) < 1:
                MyPrintE.log_print(" re_jiantin 2 ", (eid, data, str_req))

    # 凉了吗？  True 凉了
    def is_die(self):
        if time.time() - self.time_out > 3600:
            return True

    # 离线了吗？ True 离线了
    def is_line_out(self):
        if self.socket_node == None or time.time() - self.time_out > 120:
            return True

    # 需要发邮件提醒用户设备离线了吗？ True 需要     只需要发送一次邮件提醒用户设备已经离线
    def send_email_fig(self):
        if time.time() - self.time_out > 180 and self.line_out_send_email_fig == False:
            self.line_out_send_email_fig = True
            return True
