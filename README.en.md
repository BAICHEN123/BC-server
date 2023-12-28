 ## Repository for a Internet of Things (IoT) Project - Server-side Code

**Thanks Chat-GPT for the translation**

### Other Repositories
#### Gitee
[App](https://gitee.com/he_chen_chuan/Mytabs)  
[ESP8266 Node](https://gitee.com/he_chen_chuan/node)  

#### GitHub
[App](https://github.com/BAICHEN123/Mytabs)  
[ESP8266 Node](https://github.com/BAICHEN123/node)  

Documentation for the other two repositories will be released later.

### Usage
I have only tested it on my Ubuntu 22.04.3 LTS (GNU/Linux 6.2.0-37-generic x86_64) system.  
MySQL Version 8.0.35-0ubuntu0.22.04.1 for Linux on x86_64 ((Ubuntu))   
Python 3.10.12   
pip mysql-connector 2.2.9
```
python -m pip install mysql-connector
```
1. First, "git clone" this repository and "cd" into it.
2. After logging into MySQL, execute the SQL code in the "[sql1.sql](./sql1.sql)" file, which is used to create a new database, tables, triggers, etc., and configure the account and password for program login. Please check if there are any conflicts with related names.
    ```
    \. ./sql1.sql
    ```  
    or  
    ```
    source ./sql1.sql
    ```  

    **Note**: If the file is not found, replace it with the correct relative or absolute path.  
    **Note**: After changing related names, search for and modify them in the code. The code related to MySQL login is mainly in the file [Mymysql.py](./Mymysql.py).  
3. Modify configurations  
Currently, there is no support for configuration files. Please modify the code according to the instructions below, as it is currently only used by myself.  
When there are more "stars," I will consider adding this feature.  

    Modify the email sending server, account, and password for emails  
    File: [MySmtp.py](./MySmtp.py)
    ```  
    HOST = "smtp.qq.com"
    # SUBJECT ='何辰川的APP'
    FROM = "2280057905@qq.com"
    str_email_password = "ztyhzosrkgkzdiif"
    PORT = 465
    ```
    **Note**: After the program starts, it will look for the "email_password.txt" file in the program's running directory to read "str_email_password."  
    ~~The code's str_email_password is outdated, no need to worry about it.~~  
    Creating "email_password.txt" reference  
    ```
    echo ztyhzosrkgkzdiif >./email_password.txt
    ```
    **If not configured, you cannot send the verification code file via email, but you can read the code from the Python program logs.**

    **After changing the port, you need to modify the code on other devices as well.**

    HTTP port for communication with the app  
    File: [web.py](./web.py)
    ``` 
    httpd = ThreadingHTTPServer(("", 8080), RequestHandler)
    ```


    TCP port for communication with ESP8266 Nodes  
    File: [web.py](./web.py)
    ```         
    serversocket.bind(("", 9999))
    ```


    UDP port for communication with ESP8266 Nodes  
    File: [web.py](./web.py)
    ```         
    UDP_s.bind(("", 9998))
    ```


4. Start the program.  
    There are two methods: running directly or running the Python program with nohup.  
    I usually run the program in the parent directory of the repository and create a "log" folder to store some related logs. [go.sh](./go.sh) is also written based on this logic. If you have other ideas, you should modify [go.sh](./go.sh), or it may not run properly.  
    For the first run, use the first method. After running, enter "yes" to create the "head" folder in the running directory (used to store avatars).

    ```
    python ./web.py
    ```  
    or  
    ```
    chmod 744 ./go.sh
    ./go.sh
    ```  