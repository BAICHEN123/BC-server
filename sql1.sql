
#新的数据库先改一次密码，不然可能导致无密码登录
#显示所有警告信息
warnings;
# 正常 root 登入mysql之后执行该文件“\. ./sql1.sql”
#flush privileges;
#ALTER USER 'root'@'localhost' IDENTIFIED  BY '12345678';
#flush privileges;

#show variables like 'autocommit';#查看是否自动提交
#set autocommit = 0;#关闭自动提交
drop database test1;
create database test1;
use test1;
#用户表##
warnings;

create table myuserdata(
	id bigint unsigned auto_increment primary key,
	email char(200) not null unique key,
	name char(100) ,
	sex tinyint default 2 ,
	password char(32) not null,
	loginnewtime datetime not null,
	userheadmd5 char(32),
	userheadend char(6) default '.head',
	life tinyint default 1,
	index index_user_name(name)
	)engine=innodb default charset=UTF8MB4;


create table class_name(
	id int unsigned auto_increment primary key,
	name char(100) unique key,#这里要补充
	bian_ma char(50) not null,#编码，不同的程序语言可能编码不一样，在服务器这里可以转换一下
	bei_zhu TEXT)engine=innodb default charset=UTF8MB4;

#插入初始之指令
insert into class_name(id,name,bian_ma,bei_zhu) values(1,'arduino-esp8266-0.0.1','utf-8','arduino-esp8266-0.0.1 arduino环境开发的esp88226666开发板 测试版本0.0.1');


#设备表##
create table she_bei(
	id bigint unsigned auto_increment primary key,
	class_id int unsigned not null,
	chip_id char(130) not null,
	mac_add bigint unsigned not null,
	lan_ip char(15) not null,
	tcp_ip char(15) not null,
	newtime datetime not null,
	constraint unique_chip_id unique (class_id,chip_id),
	constraint fk_class_id foreign key(class_id) references class_name(id)
	)engine=innodb default charset=UTF8MB4;

#设备用户的绑定表
create table user_and_shebei(
uid bigint unsigned,
eid bigint unsigned,
name char(40) default 'nullname',
primary key(uid,eid),
constraint fk_uid foreign key(uid) references myuserdata(id),
constraint fk_eid foreign key(eid) references she_bei(id)
)engine=innodb default charset=UTF8MB4;

#记录用户产生的分享码
create table user_share(
id bigint unsigned auto_increment primary key,
share_md5 char(32) not null,
uid bigint unsigned not null,
time datetime not null,
life tinyint default 1 not null,
constraint foreign key(uid) references myuserdata(id)
)engine=innodb default charset=UTF8MB4;
#insert into user_share(share_md5,uid,time) values(%s,%s,now())

#记录分享码成功分享的eid
create table user_share_eid(
eid bigint unsigned not null,
share_id bigint unsigned not null,
primary key(share_id,eid),
constraint foreign key(eid) references she_bei(id),
constraint foreign key(share_id) references user_share(id)
)engine=innodb default charset=UTF8MB4;

#记录用户分享码接收的用户的id
create table user_get_share_uid(
share_id bigint unsigned unique key not null,
uid bigint unsigned not null,
constraint foreign key(uid) references myuserdata(id),
constraint foreign key(share_id) references user_share(id)
)engine=innodb default charset=UTF8MB4;



#节点的数据类型，用来在服务器端校验数据
create table ld_leixing(
id int unsigned primary key,
name char(10) not null unique
)engine=innodb default charset=UTF8MB4;


#插入初始数据类型，参考python的数据类型，依靠python识别节点传来的数据是什么类型，
insert into ld_leixing(id,name) values(1,'int');
insert into ld_leixing(id,name) values(2,'float');
insert into ld_leixing(id,name) values(3,'str');




#drop tables ld_faqi;
#记录联动需要监听的数据
#
#
#
#不允许以相同的方式相同的参值监听相同的数据，
create table ld_faqi(
id bigint unsigned auto_increment primary key,
eid bigint unsigned not null,
aname char(50) not null,
afuhao char(1) not null,
did int unsigned not null,
canzhi char(30) not null,
constraint unique (eid,aname,afuhao,did,canzhi),
constraint foreign key(did) references ld_leixing(id),
constraint foreign key(eid) references she_bei(id)
)engine=innodb default charset=UTF8MB4;

#drop tables ld_jieshou;
#记录联动接收方
#
#
#
#
create table ld_jieshou(
id bigint unsigned auto_increment primary key,
eid bigint unsigned not null,
gname char(50) not null,
gdata char(30) not null,
constraint unique (eid,gname,gdata),
constraint foreign key(eid) references she_bei(id)
)engine=innodb default charset=UTF8MB4;

#drop tables ld_bangdin;
#记录联动关系绑定
#
#
#
create table ld_bangdin(
id bigint unsigned auto_increment primary key,
jid bigint unsigned not null,
fid bigint unsigned not null,
uid bigint unsigned not null,
time datetime not null,
index(uid),
constraint unique (fid,jid),
constraint foreign key(uid) references myuserdata(id),
constraint foreign key(jid) references ld_jieshou(id),
constraint foreign key(fid) references ld_faqi(id)
)engine=innodb default charset=UTF8MB4;


CREATE TABLE e_time_date (
	eid bigint unsigned not null,
    value VARCHAR(3000) not null,
    date DATE not null,
    time TIME not null,
	index(date),
	index(time),
	index(eid),
	constraint foreign key(eid) references she_bei(id)
)engine=innodb default charset=UTF8MB4;


#存储过程 uid eid 绑定
delimiter $$
create procedure uid_and_eid_insert(in in_uid bigint unsigned,in in_eid bigint unsigned)
begin
	DECLARE exict_uid_eid int default 0;
	select count(uid) into exict_uid_eid from user_and_shebei where uid=in_uid and eid=in_eid;
	if exict_uid_eid=0 then
		insert into user_and_shebei(uid,eid) values(in_uid,in_eid);
	end if;
end$$
delimiter ;

#drop procedure eid_exict;
delimiter $$
create procedure eid_exict(in in_class_id int unsigned,in in_chip_id char(130),in in_mac_add bigint unsigned,in in_lan_ip char(15),in in_tcp_ip char(15),in in_time datetime)
begin
	DECLARE count_eid int default 0;
	DECLARE out_eid bigint unsigned;
	DECLARE out_bian_ma char(50);
	select COUNT(she_bei.id),she_bei.id,bian_ma into count_eid,out_eid,out_bian_ma FROM she_bei,class_name WHERE class_id=in_class_id  and chip_id=in_chip_id and class_id=class_name.id group by she_bei.id;
	if count_eid=0 then 
		select count_eid;
		INSERT INTO she_bei(class_id,chip_id,mac_add,lan_ip,tcp_ip,newtime) values(in_class_id,in_chip_id,in_mac_add,in_lan_ip,in_tcp_ip,in_time);
		set out_eid=last_insert_id();
		select bian_ma into out_bian_ma from class_name where class_name.id=in_class_id;
	else 
		update she_bei set mac_add=in_mac_add,lan_ip=in_lan_ip,tcp_ip=in_tcp_ip,newtime=in_time where id = out_eid;
	end if;
	select out_eid,out_bian_ma;
end$$
delimiter ;



#(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),dict_post['uid'],dict_post["email"],)
#create procedure user_login(in id bigint unsigned,)


delimiter $$

#存储过程 uid eid 分享
#禁止覆盖
#记录被成功分享的eid
#drop procedure share_eid;
#share_id	分享码id
#share_uid	分享设备的用户的id
#in_uid		接收分享的用户id
#in_eid		被分享的设备的id
delimiter $$
create procedure share_eid(in share_id bigint unsigned,in share_uid bigint unsigned,in in_uid bigint unsigned,in in_eid bigint unsigned)
begin
	DECLARE exict_uid_eid int default 0;
	DECLARE e_name char(40);
	select count(uid) into exict_uid_eid from user_and_shebei where uid=in_uid and eid=in_eid;
	if exict_uid_eid=0 then
		select name into e_name from user_and_shebei where uid=share_uid and eid=in_eid;
		insert into user_and_shebei(uid,eid,name) values(in_uid,in_eid,e_name);
		insert into user_share_eid(share_id,eid) values(share_id,in_eid);
	end if;
end$$
delimiter ;



#联动的存储过程
#应为监听和接收是分开储存且不允许重复的，所以调用存储过程，有重复的就直接找到fid就可以了
#添加一个监听			(int,str,char,int,str,int)
#insert into ld_faqi(eid,aname,afuhao,did,canzhi,uid,time) values(%s,%s,%s,%s,%s,%s,now())
#添加一个接受数据		(int,str,str,int)
#insert into ld_jieshou(eid,gname,gdata,uid,time) values(%s,%s,%s,%s,now())
#将监听和接受数据绑定	(int,int,int)
#insert into ld_bangdin(jid,fid,uid,time) values(%s,%s,%s,now())
#
#
#drop procedure ld_insert;
delimiter $$



create procedure ld_insert(in in_feid bigint unsigned,
in in_aname char(50),
in in_afuhao char(1),
in in_did int unsigned,
in in_canzhi char(30),
in in_jeid bigint unsigned,
in in_gname char(50),
in in_gdata char(30),
in in_uid bigint unsigned)
begin
	DECLARE count_id int default 0;
	DECLARE tmp_fid bigint unsigned;
	DECLARE tmp_jid bigint unsigned;
	DECLARE tmp_bid bigint unsigned;
	select COUNT(id),id into count_id,tmp_fid FROM ld_faqi WHERE eid=in_feid and aname=in_aname and afuhao=in_afuhao and canzhi=in_canzhi group by id;
	if count_id=0 then 
		insert into ld_faqi(eid,aname,afuhao,did,canzhi) values(in_feid,in_aname,in_afuhao,in_did,in_canzhi);
		set tmp_fid=last_insert_id();
	end if;
	set count_id=0;
	select COUNT(id),id into count_id,tmp_jid FROM ld_jieshou WHERE eid=in_jeid and gname=in_gname and gdata=in_gdata group by id;
	if count_id=0 then 
		insert into ld_jieshou(eid,gname,gdata) values(in_jeid,in_gname,in_gdata);
		set tmp_jid=last_insert_id();
	end if;
	set count_id=0;
	select COUNT(id),id into count_id,tmp_bid from ld_bangdin where fid=tmp_fid and jid=tmp_jid group by id;
	if count_id=0 then
		insert into ld_bangdin(fid,jid,uid,time) values(tmp_fid,tmp_jid,in_uid,now());
		set tmp_bid=last_insert_id();
	end if;
	select tmp_bid,tmp_fid,tmp_jid;
end$$
delimiter ;

#call ld_insert(20,'温度','>',2,'30.1',21,'@开关2','1',1,now());

	##这是存储过程，运行传回多组数据，将需要清除的监听也传回去？
	##检查是否有多余的监听和接收

#drop procedure ld_updata;
#要求	1	插入发起 前查看是否有两个接收共用一个监听，如果有，就检查是否有和新的相同的，没有相同的就新建一个发起。如果没有就修改    关于新建，如果有和其他相同的，就直接引用
#		2	插入接受 前检查是否有两个监听公用一个接受，如果有，就新建一个接受，没有就修改，同上
#		3	将上面
#
#
delimiter $$


create procedure ld_updata(
in in_bid bigint unsigned,
in in_fid bigint unsigned,
in in_jid bigint unsigned,
in in_feid bigint unsigned,
in in_aname char(50),
in in_afuhao char(1),
in in_did int unsigned,
in in_canzhi char(30),
in in_jeid bigint unsigned,
in in_gname char(50),
in in_gdata char(30),
in in_uid bigint unsigned)
begin
	DECLARE count_id int default 0;
	DECLARE tmp_fid bigint unsigned default 0;
	DECLARE tmp_jid bigint unsigned default 0;
	DECLARE tmp_bid bigint unsigned default 0;
	DECLARE fig_f bigint unsigned default 0;
	DECLARE fig_j bigint unsigned default 0;

	##只有在修改后有相同的，且修改前没有被占用时，才会产生野数据

	##先检查有没有修改的相同的，直接引用
	select count(id),id  into count_id,tmp_fid from ld_faqi f where eid=in_feid and aname=in_aname and afuhao=in_afuhao and canzhi=in_canzhi group by id;
	if count_id=0 then
		##没有可以直接引用的就更新或者新建
		##检查绑定
		set count_id=0;
		select count(id) into count_id from ld_bangdin where fid=in_fid and id!=in_bid;
		if count_id=0 then
			##没有多次引用发起，可以直接修改
			update ld_faqi set eid=in_feid,aname=in_aname,afuhao=in_afuhao,did=in_did,canzhi=in_canzhi where id=in_fid;
			set tmp_fid=in_fid;
		else
			##被多次引用，不可修改，需要新建
			insert into ld_faqi(eid,aname,afuhao,did,canzhi) values(in_feid,in_aname,in_afuhao,in_did,in_canzhi);
			set tmp_fid=last_insert_id();
		end if;
	else
		set fig_f=1;
	end if;
	##tmp_fid中储存发起的id

	##先检查有没有修改的相同的，直接引用
	set count_id=0;
	select COUNT(id),id into count_id,tmp_jid FROM ld_jieshou WHERE eid=in_jeid and gname=in_gname and gdata=in_gdata group by id;
	if count_id=0 then
		##没有相同的可以引用，需要新建，或者修改
		set count_id=0;
		select count(id) into count_id from ld_bangdin where jid=in_jid and id!=in_bid;
		if count_id=0 then
			##没有多次引用，可以直接修改
			update ld_jieshou set eid=in_jeid,gname=in_gname,gdata=in_gdata where id=in_jid;
			set tmp_jid=in_jid;
		else 
			##被多次引用，不可修改，需要新建
			insert into ld_jieshou(eid,gname,gdata) values(in_jeid,in_gname,in_gdata);
			set tmp_jid=last_insert_id();

		end if;
	else
		set fig_j=1;
	end if;
	##tmp_jid储存接收id

	##将新的关系绑定，旧的关系处理
	set count_id=0;
	##检查有没有相同联动，没有就可以修改，有了bid自动赋值，需要删掉原来的
	select COUNT(id),id into count_id,tmp_bid from ld_bangdin where fid=tmp_fid and jid=tmp_jid group by id;
	if count_id=0 then
		update ld_bangdin set fid=tmp_fid,jid=tmp_jid,uid=in_uid,time=now() where id=in_bid;
		set tmp_bid=in_bid;
	else
		if tmp_bid!=in_bid then 
			delete ld_bangdin from ld_bangdin where id=in_bid;
		end if;
	end if;


	##先把联动绑定表修改了，才会释放id
	if fig_f=1 then 
		set count_id=0;
		select count(id) into count_id from ld_bangdin b where b.fid=in_fid;
		if count_id=0 then 
			delete f from ld_faqi f where f.id=in_fid;
			select in_fid;
		end if;
	end if;

	if fig_j=1 then
		set count_id=0;
		select count(id) into count_id from ld_bangdin b where b.jid=in_jid;
		if count_id=0 then 
			delete j from ld_jieshou j where j.id=in_jid;
		end if;
	end if;

	select tmp_bid,tmp_fid,tmp_jid;

end$$
delimiter ;





#创建服务器链接账户##
create user 'user_test1'@'localhost' identified by '%^TY56ty';
grant select,insert,update on test1.* to 'user_test1'@'localhost';
grant delete on test1.* to 'user_test1'@'localhost';
ALTER USER 'user_test1'@'localhost' IDENTIFIED WITH mysql_native_password BY '%^TY56ty';
grant delete on test1.user_and_shebei to 'user_test1'@'localhost';
GRANT EXECUTE ON test1.*  to 'user_test1'@'localhost';
flush privileges;

#SQL_SELECT_GET_EID='SELECT COUNT(she_bei.id),she_bei.id,bian_ma 
#FROM she_bei,class_name
# WHERE she_bei.class_id=%s 
#and she_bei.chip_id=%s 
#and she_bei.class_id=class_name.id'
#DROP PROCEDURE eid_exict;

#select COUNT(she_bei.id),she_bei.id,bian_ma FROM she_bei,class_name WHERE class_id=in_class_id  and chip_id=in_chip_id and class_id=class_name.id group by she_bei.id ;
#call eid_exict(1,'1458208',71421550543925,'192.168.137.124','116.253.21.85','2021-03-18 21:21:07');

#用户绑定设备表##
#drop table user_get_shebei;
#create table user_get_shebei(	id bigint unsigned primary key,	shebei_id_many  text,	foreign key(id) references myuserdata(id)	)engine=innodb default charset=UTF8MB4;


#设备绑定用户表##
#drop table shebei_to_users;
#create table shebei_to_users(id bigint unsigned primary key,	users_id  text,	foreign key(id) references she_bei(id)	)engine=innodb default charset=UTF8MB4;

#触发器
#DROP trigger copy_uid;
#DROP trigger copy_eid;
#create trigger copy_uid after insert on myuserdata for each row insert into user_get_shebei(id,shebei_id_many) values(NEW.id,'#');
#create trigger copy_eid after insert on she_bei for each row insert into shebei_to_users(id,users_id) values(NEW.id,'#');

#DROP trigger user_and_shebei_del_trigger;
#删除节点之前删除联动xinxi
create trigger user_and_shebei_del_trigger before 
delete on user_and_shebei 
for each row 
delete b from ld_bangdin b inner join ld_faqi f on f.id=b.fid  inner join ld_jieshou j on b.jid=j.id where b.uid=old.uid and (j.eid=old.eid or f.eid=old.eid);


#删除联动绑定之前，删除发起和接收信息？
#有点儿难搞，搞定时清理吧，需要的触发器太多了？