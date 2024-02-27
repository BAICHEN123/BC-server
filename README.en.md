 ## Repository for a Internet of Things (IoT) Project - Server-side Code

**Thanks Chat-GPT for the translation**

### New Content
1. Support for OTA (Over-the-Air updates) has been added.  
After compiling, copy the generated bin file to the corresponding location under MyConfig.OTA_DIR_NAME directory. The files will be classified based on the compilation date and character information contained in the bin file. Update decisions for corresponding nodes will be made based on the OTA_SERVER_FIND_TAG information sent by the nodes.  
Firmware of approximately 344400 bytes is transmitted and written in approximately 6109ms, much faster than burning programs via serial port.  
~~After I finish implementing the node logging feature, I will attempt to debug the program using OTA. After all, breakpoints debugging is not feasible, and OTA burning is faster.~~

### Other Repositories
#### Gitee
[App](https://gitee.com/he_chen_chuan/Mytabs)  
[ESP8266 Node](https://gitee.com/he_chen_chuan/node)  

#### GitHub
[App](https://github.com/BAICHEN123/Mytabs)  
[ESP8266 Node](https://github.com/BAICHEN123/node)  

Documentation for the other two repositories will be released later.

### Usage
#### Basic Environment
I have only validated this on my Ubuntu 22.04.3 LTS (GNU/Linux 6.2.0-37-generic x86_64) system.  
- inotifywait version 3.22.1.0
    ```bash
    sudo apt install inotify-tools
    ```
- MySQL version 8.0.35-0ubuntu0.22.04.1 for Linux on x86_64 ((Ubuntu))
- Python 3.10.12
- Pip package: mysql-connector 2.2.9
    ```bash
    python -m pip install mysql-connector
    ```

#### Operations
1. Clone the repository using "git clone" and navigate into the cloned directory using "cd".
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
Frequently used configuration parameters have been moved to "[MyConfig.py](./MyConfig.py)". Please try to guess their purposes based on the names, as there are minimal comments.

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