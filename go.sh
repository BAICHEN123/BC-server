#utf-8
echo 拉取代码
cd ./the-server
#git pull
cd ..
echo 当前python3进程
ps -aux|grep the-server
echo 任意按键结束所有python3进程
#pause
#killall python3 -15
pkill -f "python3 -u ./the-server/web.py"
sleep 1
echo 移动日志
mv log* ./oldlog/
echo 运行程序
time1=$(date "+%Y-%m-%d-%Hh%Mm%Ss")
#cp web.py ./oldlog/web$time1.py
nohup python3 -u  ./the-server/web.py >> log$time1.log 2>>log$time1.log  &
echo 执行完毕
sleep 1
cat log$time1.log 2>>log$time1.log
