## 一个物联网项目的服务器端代码仓库

[Thanks Chat-GPT for the translation.](./README.en.md)

### 其他端
#### gitee
[app](https://gitee.com/he_chen_chuan/BC-app)  
[esp8266 节点](https://gitee.com/he_chen_chuan/node)  

#### github
[app](https://github.com/BAICHEN123/BC-app)  
[esp8266 节点](https://github.com/BAICHEN123/node)  

### 使用方式
我只在我的Ubuntu 22.04.3 LTS (GNU/Linux 6.2.0-37-generic x86_64)系统验证过  
mysql  Ver 8.0.35-0ubuntu0.22.04.1 for Linux on x86_64 ((Ubuntu))   
Python 3.10.12   
pip mysql-connector                       2.2.9
```
python -m pip install mysql-connector
```
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
目前不支持配置文件，请根据下文提示自行修改代码，毕竟目前只有我自己在用。  
等“star”多了，我会考虑增加。  

    修改email邮件的发送服务器、账号、密码  
    文件： [MySmtp.py](./MySmtp.py)
    ```  
    HOST = "smtp.qq.com"
    # SUBJECT ='何辰川的APP'
    FROM = "2280057905@qq.com"
    str_email_password = "ztyhzosrkgkzdiif"
    PORT = 465
    ```
    **注**：程序启动后会从程序运行目录下查找"email_password.txt"文件读取"str_email_password"  
    ~~代码里的str_email_password是过期的，不用为我担心。~~  
    "email_password.txt"创建参考  
    ```
    echo ztyhzosrkgkzdiif >./email_password.txt
    ```
    **不配置的话无法通过邮件发送验证码文件，但是可以从python程序日志读取到验证码。**

    **修改端口之后需要把其他设备上的代码的端口也修改。**

    用于和app通讯的http端口  
    文件： [web.py](./web.py)
    ``` 
    httpd = ThreadingHTTPServer(("", 8080), RequestHandler)
    ```


    用于和esp8266 节点通讯的tcp端口  
    文件： [web.py](./web.py)
    ```         
    serversocket.bind(("", 9999))
    ```


    用于和esp8266 节点通讯的udp端口  
    文件： [web.py](./web.py)
    ```         
    UDP_s.bind(("", 9998))
    ```


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
    





