

drop procedure uid_and_eid_insert;
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

drop procedure eid_exict;
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


drop procedure share_eid;

#存储过程 uid eid 分享
#禁止覆盖
#记录被成功分享的eid
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
drop procedure ld_insert;
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

drop procedure ld_updata;
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