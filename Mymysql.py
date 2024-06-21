import mysql.connector
import MyPrintE
import time
import threading
import MyConfig
from MySmtp import email_send_str

CHARSET = MyConfig.SQL_CHARSET
HOST = MyConfig.SQL_HOST
USER = MyConfig.SQL_USER
PASSWD = MyConfig.SQL_PASSWD
DATABASE = MyConfig.SQL_DATABASE
AUTH_PLUGIN = MyConfig.SQL_AUTH_PLUGIN


sql_link_couunt = 0
list_sql_link = list()
list_sql_link_lock = threading.Lock()


def wait_mysql__server_start():
    count=0
    for i in range(0,100):
        try:
            sql_obj = MySqlLink()
            MyPrintE.log_print(f"成功检测到mysql服务 {type(sql_obj)}" 
                    + time.strftime("%Y-%m-%d %H:%M:%S  ", time.localtime()))
            return True
        except mysql.connector.Error as err:
            print(f"Error connecting to MySQL: {err}")
            time.sleep(1)  # 等待 1 秒后重试
    return False

# select b.id,b.fid,b.jid,f.eid,f.aname,f.afuhao,f.did,f.canzhi,j.eid,j.gname,j.gdata from ld_bangdin b,ld_faqi f,ld_jieshou j where b.uid=1 and f.id=b.fid and  j.id=b.jid;
#
#
#
class MySqlLink:
    global sql_link_couunt
    # 占用状态
    WORKING = 1
    # 空闲状态
    MO_YU = 0

    def __init__(self):
        global sql_link_couunt, list_sql_link
        self.sql_link = None
        # assert type(sql_link)==mysql.connector.connection.MySQLConnection,"MySqlLink type(sql_link)==mysql.connector.connection.MySQLConnection"
        self.sql_link = mysql.connector.connect(
            charset=CHARSET,
            host=HOST,
            user=USER,
            passwd=PASSWD,
            database=DATABASE,
            auth_plugin=AUTH_PLUGIN,
        )
        self.sql_status = self.MO_YU
        sql_link_couunt = sql_link_couunt + 1
        MyPrintE.log_print("产生了一个sql连接，当前连接数" + str(sql_link_couunt))

    def free_lick(self):
        # 释放这个链接的使用权，将状态设置为 摸鱼 MO_YU
        self.sql_status = self.MO_YU

    def get_link(self):
        # 此链接被获取，将状态设置为繁忙
        self.sql_status = self.WORKING

    def sql_close(self):
        self.sql_link.close()

    def sql_commit(self):
        self.sql_link.commit()

    def sql_rollback(self):
        self.sql_link.rollback()

    # 获取一个数据库操作游标
    def re_cursor(self):
        try:
            return self.sql_link.cursor()
        except mysql.connector.errors.OperationalError as e:
            # MyPrintE.e_print(e,"数据库链接已断开，尝试重新连接")#print(time.strftime("%Y-%m-%d %H:%M:%S  ", time.localtime()),e.with_traceback,"   数据库链接已断开，尝试重新连接")
            try:
                self.sql_link = mysql.connector.connect(
                    charset=CHARSET,
                    host=HOST,
                    user=USER,
                    passwd=PASSWD,
                    database=DATABASE,
                    auth_plugin=AUTH_PLUGIN,
                )
                return self.sql_link.cursor()
            except Exception as e:
                MyPrintE.e_print(
                    e
                )  # print(time.strftime("%Y-%m-%d %H:%M:%S  ", time.localtime()),e.with_traceback,"   重新连接数据库失败")
                email_send_str(
                    MyConfig.SQL_ERROR_EMAIL,
                    "数据库异常，重连失败"
                    + time.strftime("%Y-%m-%d %H:%M:%S  ", time.localtime()),
                )
                return

    def __del__(self):
        global sql_link_couunt
        if self.sql_link:
            self.sql_close()
        sql_link_couunt = sql_link_couunt - 1
        MyPrintE.log_print("删掉了一个sql链接，当前连接数" + str(sql_link_couunt))


class Mymysql:
    # 用设备分类id和设备的芯片id查询到设备的数据库id
    SQL_CALLPROC_EXICT_EID = "eid_exict"
    # 输入uid，eid
    SQL_SELECT_EXIST_EID_AN_UID = "call uid_and_eid_insert(%s,%s)"
    # 输入share_id,get_share_id,eid
    INSERT_EXIST_SHAER = "call share_eid(%s,%s,%s,%s)"
    # 禁止用户备注名里出现特殊符号
    SQL_UPDATE_BINDING3 = "INSERT INTO user_and_shebei(uid,eid,) values(%s,%s)"
    # 查询邮件是否注册过
    SQL_SELECT_EMAIL = "SELECT COUNT(email) FROM myuserdata WHERE email=%s"
    # 同步用户信息
    SQL_SELECT_USERDATA = "SELECT id,name,sex,userheadmd5,userheadend  FROM myuserdata WHERE id=%s and email=%s"
    # 同步用户信息
    SQL_SELECT_USERDATA1 = (
        "SELECT id,name,sex,userheadmd5,userheadend  FROM myuserdata WHERE email=%s"
    )
    # 同步用户信息
    SQL_SELECT_USERDATA3 = "SELECT id,name,sex,userheadmd5,userheadend  FROM myuserdata WHERE id=%s and email=%s and password=%s"
    # 同步用户信息
    SQL_SELECT_USERDATA2 = "SELECT id FROM myuserdata WHERE email=%s"
    # 插入注册信息
    SQL_INSERT_EMAIL = (
        "INSERT INTO myuserdata(email,password,loginnewtime) values(%s,%s,%s) "
    )
    # 更新密码
    SQL_UPDATE_PASSWORD = (
        "UPDATE myuserdata SET password=%s,loginnewtime=%s WHERE email=%s"
    )
    # 更新最后登录时间
    SQL_UPDATE_LOGIN_YX = "UPDATE myuserdata SET loginnewtime=%s WHERE email=%s "
    # 更新最后登录时间
    SQL_UPDATE_LOGIN_YX1 = (
        "UPDATE myuserdata SET loginnewtime=%s WHERE id=%s and email=%s "
    )
    # 更新用户信息
    SQL_UPDATE_USERDATA = "UPDATE myuserdata SET name=%s,sex=%s,userheadmd5=%s,userheadend=%s where email=%s"
    # 更新用户密码
    SQL_UPDATE_USERPW = "UPDATE myuserdata SET password=%s where id=%s and email=%s"
    # 修改设备的名字
    SQL_UPDATE_SETNAME2 = "UPDATE user_and_shebei set name=%s WHERE uid=%s and eid=%s"
    # 查询一个用户绑定的所有的设备
    SQL_SELECT_UID_EIDX = "select eid,name from user_and_shebei where uid=%s"
    # 查询一个用户绑定的所有的设备
    SQL_SELECT_UID_EIDX_NONAME = "select eid from user_and_shebei where uid=%s"
    # 记录用户分享码接收的用户的id
    SQL_INSERT_GET_SHARE_UID = (
        "insert into user_get_share_uid(uid,share_id) values(%s,%s)"
    )
    # 记录分享码产生的信息
    SQL_INSERT_SHARE_DATA = (
        "insert into user_share(share_md5,uid,time) values(%s,%s,now())"
    )
    # 查询用户是否拥有此设备
    SQL_SELECT_UID_HAVE_EID = "select uid from user_and_shebei where uid=%s and eid=%s"
    # 这里有个问题，之前我这里是返回 count(eid) ，但是经常判定错误，我怀疑是这个函数有缓存，导致我的设备发生改动之后，就判定错误，但是我懒得测试先记录下来吧

    ##添加一个监听			(int,str,char,int,str,int)
    # IN_JIANTIN="insert into ld_faqi(eid,aname,afuhao,did,canzhi,uid,time) values(%s,%s,%s,%s,%s,%s,now())"
    ##添加一个接受数据		(int,str,str,int)
    # IN_JIESHOU="insert into ld_jieshou(eid,gname,gdata,uid,time) values(%s,%s,%s,%s,now())"
    ##将监听和接受数据绑定	(int,int,int)
    # IN_LD_BANGDIN="insert into ld_bangdin(jid,fid,uid,time) values(%s,%s,%s,now())"

    # 请使用查询的方式调用此sql
    # 下面是参考
    # call ld_insert(20,'温度','>',2,'30.1',21,'@开关2','1',1,now());
    LD_CALLPROC_IN = "ld_insert"
    LD_CALLPROC_UPDATA = "ld_updata"

    # uid 查询联动绑定表，产看该用户添加的所有联动 (int uid)
    SELECT_UID_LD = """select b.id,b.fid,b.jid,f.eid,f.aname,f.afuhao,f.did,f.canzhi,j.eid,j.gname,j.gdata 
					from ld_bangdin b inner join ld_faqi f on f.id=b.fid  inner join ld_jieshou j on b.jid=j.id
					where b.uid=%s"""

    # eid 在 联动发起表和联动接收表 中且 在 绑定表 中绑定 (int eid,int eid)
    SELECT_EID_LD = """select distinct f.id,f.aname,f.afuhao,f.did,f.canzhi
	from ld_bangdin b,ld_faqi f
	where f.eid=%s and f.id=b.fid"""

    # 查找所有对 eid 有指示动作的 fid
    SELECT_FID_DO_EID = """select f.id,f.eid from ld_bangdin b
	inner join ld_faqi f on f.id=b.fid  inner join ld_jieshou j on b.jid=j.id
	where j.eid=%s"""

    # 查询一个用户名下所有的设备的所有联动			(int uid)
    SELECT_UID_LD_ALL = """select distinct b.id,b.fid,b.jid,f.eid,f.aname,f.afuhao,f.did,f.canzhi,j.eid,j.gname,j.gdata 
	from ld_bangdin b,ld_faqi f,ld_jieshou j,(select eid from user_and_shebei where uid=%s) a
	where (f.eid=a.eid or j.eid=a.eid) and f.id=b.fid and j.id=b.jid"""

    FID_SELECT_J = """select j.eid,j.gname,j.gdata 
	from ld_bangdin b inner join ld_faqi f on f.id=b.fid  inner join ld_jieshou j on b.jid=j.id
	where f.id=%s"""

    # 删除没有指向 ld_jieshou 的 ld_faqi
    DELTET_NONE_FAQI = """delete from ld_faqi f where f.id=%s"""

    # 查询用户是否拥有此设备,顺便把设备的eid也发过来
    LD_SELECT_UID_HAVE_DID = "select count(b.uid),f.eid,f.id from ld_bangdin b,ld_faqi f where b.uid=%s and b.id=%s and f.id=b.fid"

    DEL_LD_BANGDIN_DID = "delete from ld_bangdin where id=%s"
    DEL_E_U_BANGDIN = "delete from user_and_shebei where uid=%s and eid=%s"

    SEL_U_NET_MD5 = "select loginnewtime from myuserdata where id=%s"

    SQL_INSERT_TIME_DATA = (
        "INSERT INTO e_time_date(eid,value,date,time) values(%s,%s,%s,%s)"
    )
    SQL_SELECT_TIME_DATA = """SELECT value,DATE_FORMAT(date, '%Y-%m-%d'),TIME_FORMAT(time, "%H:%i:%S") FROM e_time_date WHERE eid = %s AND date >= %s AND date <= %s"""
    # SELECT value,DATE_FORMAT(date, '%%%%Y-%%%%m-%%%%d'),TIME_FORMAT(time, '%%%%H:%%%%i:%%%%s')
    # %S既可以格式化时间，有不会被识别成占位符
    """
     '2022-01-03', '08:00:00'
	eid bigint unsigned not null,
    value VARCHAR(3000) not null,
    date DATE not null,
    time TIME not null,
    """

    LIST_SQL_LINK_MAX = 5  # 目前设置数据库的链接上限是5
    MAX_WHILE_MS = 1000  # 设置阻塞的上限时间，单位ms
    MIN_WHILE_MS = 10  # 设置查询的间隔时间，单位ms

    # 这个http类是单线程工作，有一个sql链接就够了，? 不行了，现在是多线程了，要搞连接池了
    # {'name': '未闻君名', 'email': '2275442930@qq.com', 'sex': '2', 'user_head_md5': 'dcda1eb07de0a72521140853f28b1488', 'user_head_end': 'head'}
    def __init__(self):
        global list_sql_link, list_sql_link_lock
        with list_sql_link_lock:
            if len(list_sql_link) == 0:
                list_sql_link.append(MySqlLink())  # 都初始化了，我先放一个链接到列表里

    def __del__(self):
        # self.sql1.close()
        # 清空列表，sql链接的关闭函数写在 MySqlLink 里
        # list_sql_link.clear()
        pass

    def get_a_sql_link_of_lock(self):
        # 返回的数据类型是 MySqlLink
        global list_sql_link
        for item in list_sql_link:
            if item.sql_status == item.MO_YU:
                item.get_link()
                return item
        # 程序到这里没有返回说明已经建立的所有链接都被使用了，需要再次创建链接
        if len(list_sql_link) < self.LIST_SQL_LINK_MAX:
            sql_i = MySqlLink()
            list_sql_link.append(sql_i)
            MyPrintE.log_print("产生了一个sql连接,len(list_sql_link)=", len(list_sql_link))
            sql_i.get_link()
            return sql_i
        else:
            # 所有的链接都在使用中，并且已经到达建立链接的上限，开始阻塞，等待空闲链接的出现
            time_out = 0
            while time_out < self.MAX_WHILE_MS:
                time.sleep(0.001 * self.MIN_WHILE_MS)  # 等待 MIN_WHILE_MS ms 后重新查看一次
                time_out = time_out + self.MIN_WHILE_MS
                for item in list_sql_link:
                    if item.sql_status == item.MO_YU:
                        item.get_link()
                        return item
        # 没办法喽，阻塞了好久，都没有可用的链接
        MyPrintE.log_print("超时未有可用sql链接")
        return None

    def get_a_sql_link(self):
        global list_sql_link_lock
        with list_sql_link_lock:
            return self.get_a_sql_link_of_lock()

    def list_tuple_to_list(self, list1):
        try:
            if type(list1) != list or type(list1[0]) != tuple:
                return 0
            list2 = list()
            for list_i in list1:
                list2.append(list_i[0])
            return list2
        except IndexError as e:
            return 0
        except SyntaxError as e:
            return 0
        except TypeError as e:
            return 0

    def list_to_list_tuple(self, share_uid, get_share_uid, list_eid):
        list2 = list()
        for i in list_eid:
            list2.append(
                (
                    share_uid,
                    get_share_uid,
                    i,
                )
            )
        return list2

    def for_INSERT_EXIST_SHAER(self, share_id, share_uid, get_share_uid, list_eid):
        mysqllink1 = self.get_a_sql_link()  # 获取一个空闲的链接
        if mysqllink1 == None:
            return None  # 因为没有获取到空闲链接，所以不用释放链接，下同
        sql_send = mysqllink1.re_cursor()  # 获取游标？
        if sql_send == None:
            mysqllink1.free_lick()
            return None
        try:
            sql_send.execute(self.SQL_INSERT_GET_SHARE_UID, (get_share_uid, share_id))
            for eid in list_eid:
                sql_send.execute(
                    self.INSERT_EXIST_SHAER, (share_id, share_uid, get_share_uid, eid)
                )
        except Exception as e:
            MyPrintE.e_print(e)
            mysqllink1.sql_rollback()
            mysqllink1.free_lick()
            return None
        mysqllink1.sql_commit()  # 提交更改
        # 虽然名字是插入，但是调用的是存储过程，没有返回值，调用别的不合适，只要不报异常，就是正常执行
        # share_id	分享码id				dict_share_md5[dict_post['share_ma']][3]
        # share_uid	分享设备的用户的id		dict_share_md5[dict_post['share_ma']][0]
        # in_uid		接收分享的用户id		dict_post['uid']
        # in_eid		被分享的设备的id		list_share_eid=dict_share_md5[dict_post['share_ma']][1]
        mysqllink1.free_lick()
        return sql_send.rowcount

    def mysql_sql_select(self, str_sql, tuple_sql_data):
        mysqllink1 = self.get_a_sql_link()
        if mysqllink1 == None:
            return None
        sql_send = mysqllink1.re_cursor()
        if sql_send == None:
            mysqllink1.free_lick()
            return
        sql_send.execute(str_sql, tuple_sql_data)
        sql_data1 = sql_send.fetchall()
        mysqllink1.sql_commit()  # 虽然我知道select不用commit，但是我想试试，不然就要放弃连接池计划了
        mysqllink1.free_lick()
        return sql_data1

    def mysql_sql_update(self, str_sql, tuple_sql_data):
        mysqllink1 = self.get_a_sql_link()
        if mysqllink1 == None:
            return None
        sql_send = mysqllink1.re_cursor()
        if sql_send == None:
            mysqllink1.free_lick()
            return
        try:
            sql_send.execute(str_sql, tuple_sql_data)
        except Exception as e:
            MyPrintE.e_print(e)
            mysqllink1.sql_rollback()
            mysqllink1.free_lick()
            return None
        mysqllink1.sql_commit()
        mysqllink1.free_lick()
        return sql_send.rowcount

    def mysql_sql_insert(self, str_sql, tuple_sql_data):
        mysqllink1 = self.get_a_sql_link()
        if mysqllink1 == None:
            return None
        sql_send = mysqllink1.re_cursor()
        if sql_send == None:
            mysqllink1.free_lick()
            return None
        try:
            sql_send.execute(str_sql, tuple_sql_data)
        except Exception as e:
            MyPrintE.e_print(e)
            mysqllink1.sql_rollback()
            mysqllink1.free_lick()
            return None
        mysqllink1.sql_commit()
        mysqllink1.free_lick()
        if sql_send.rowcount > 0:
            return sql_send.lastrowid
        else:
            return 0

    def mysql_sql_inserts(self, str_sql, list_sql_data):
        mysqllink1 = self.get_a_sql_link()
        if mysqllink1 == None:
            return None
        sql_send = mysqllink1.re_cursor()
        if sql_send == None:
            mysqllink1.free_lick()
            return None
        try:
            for tuple_sql_data in list_sql_data:
                sql_send.execute(str_sql, tuple_sql_data)
        except Exception as e:
            MyPrintE.e_print(e)
            mysqllink1.sql_rollback()
            mysqllink1.free_lick()
            return None
        mysqllink1.sql_commit()
        mysqllink1.free_lick()
        return sql_send.rowcount

    def mysql_sql_delete(self, str_sql, tuple_sql_data):
        mysqllink1 = self.get_a_sql_link()
        if mysqllink1 == None:
            return None
        sql_send = mysqllink1.re_cursor()
        if sql_send == None:
            mysqllink1.free_lick()
            return
        try:
            sql_send.execute(str_sql, tuple_sql_data)
        except Exception as e:
            MyPrintE.e_print(e)
            mysqllink1.sql_rollback()
            mysqllink1.free_lick()
            return None
        mysqllink1.sql_commit()
        sql_data1 = sql_send.rowcount
        mysqllink1.free_lick()
        return sql_data1

    # 针对仅有一行数据返回的sql存储过程
    def mysql_sql_callproc_1(self, str_callproc_name, tuple_sql_date):
        mysqllink1 = self.get_a_sql_link()
        if mysqllink1 == None:
            return None
        sql_send = mysqllink1.re_cursor()
        if sql_send == None:
            mysqllink1.free_lick()
            return
        try:
            sql_send.callproc(str_callproc_name, tuple_sql_date)
        except Exception as e:
            MyPrintE.e_print(e)
            mysqllink1.sql_rollback()
            mysqllink1.free_lick()
            return None
        mysqllink1.sql_commit()
        # 提取存储过程的返回数据
        sql_data_1 = sql_send.stored_results()
        """
		list_data_s=list()
		for data_i in sql_data_1:
			list_data_s.appen(data_i.fetchall())
		"""
        # [(19, 'utf-8')]
        mysqllink1.free_lick()  # 释放链接
        return next(sql_data_1).fetchall()

    # 针对多行数据返回的sql存储过程
    def mysql_sql_callproc_x(self, str_callproc_name, tuple_sql_date):
        mysqllink1 = self.get_a_sql_link()
        if mysqllink1 == None:
            return None
        sql_send = mysqllink1.re_cursor()
        if sql_send == None:
            mysqllink1.free_lick()
            return
        try:
            sql_send.callproc(str_callproc_name, tuple_sql_date)
        except Exception as e:
            MyPrintE.e_print(e)
            mysqllink1.sql_rollback()
            mysqllink1.free_lick()
            return None
        mysqllink1.sql_commit()  # 提交更改
        # 提取存储过程的返回数据
        sql_data_1 = sql_send.stored_results()
        list_data_s = list()
        for data_i in sql_data_1:
            list_data_s.append(data_i.fetchall())
        # a=next(sql_data_1).fetchall()
        # a=[(19, 'utf-8')]
        mysqllink1.free_lick()  # 释放链接
        return list_data_s
