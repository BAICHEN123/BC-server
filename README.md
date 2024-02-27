## 一个物联网项目的服务器端代码仓库

[Thanks Chat-GPT for the translation.](./README.en.md)

### 新内容
1. 支持云端升级 OTA。
将编译完成的 bin 文件拷贝至 MyConfig.OTA_DIR_NAME 目录下对应的位置，就会根据 bin 中包含的编译日期、编译文件字符信息进行分类，根据节点发送的 OTA_SERVER_FIND_TAG 信息判断对应的节点是否需要更新。  
344400字节的固件大约6109ms发完并写入，比我串口烧程序快多了。  
~~等我搞完节点日志功能之后会尝试用OTA的方式调试程序，反正都不能用断点调试，OTA烧程序还快~~


### 其他端
#### gitee
[app](https://gitee.com/he_chen_chuan/BC-app)  
[esp8266 节点](https://gitee.com/he_chen_chuan/node)  

#### github
[app](https://github.com/BAICHEN123/BC-app)  
[esp8266 节点](https://github.com/BAICHEN123/node)  

### 使用方式  
#### 基础环境  
我只在我的Ubuntu 22.04.3 LTS (GNU/Linux 6.2.0-37-generic x86_64)系统验证过  
inotifywait 3.22.1.0   
```
apt install inotify-tools
```
mysql  Ver 8.0.35-0ubuntu0.22.04.1 for Linux on x86_64 ((Ubuntu))   
Python 3.10.12   
pip mysql-connector                       2.2.9
```
python -m pip install mysql-connector
```
#### 执行操作  
1. 先“git clone”该仓库代码并“cd”进去
2. 登入mysql之后执行 “[sql1.sql](./sql1.sql)” 文件里的sql代码，该文件用于新建数据库、表格、触发器等，并配置用于程序登录的账户和密码。请自行检查相关名称是否有冲突。  
    ```
    \. ./sql1.sql
    ```  
    或  
    ```
    source ./sql1.sql
    ```  

    **注**：找不到文件自行替换成相对路径或绝对路径。  
    **注**：修改相关名称后自行在代码中查找相关名称，并修改。mysql登录相关的代码主要在文件[Mymysql.py](./Mymysql.py)里。  
3. 修改配置  
常用的配置量移动到了“[MyConfig.py](./MyConfig.py)”里面，自己根据名称猜一下是干啥的，有微量的注释   
4. 启动程序。  
    2种方法，直接运行或者nohup运行python程序。  
    我一般在仓库的父目录运行程序，并建立一个"log"文件夹储存一些相关的日志。[go.sh](./go.sh)也是依据这一逻辑编写的。如果你有其他想法，应该修改[go.sh](./go.sh)，不然可能无法运行。  
    第一次运行使用第一种方式，运行后输入"yes"在运行目录创建文件夹"head"(用来存头像的)。

    ```
    python ./web.py
    ```  
    或  
    ```
    chmod 744 ./go.sh
    ./go.sh
    ```  
    





