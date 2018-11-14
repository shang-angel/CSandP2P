import socket
import os
import struct
import sys
import hashlib
import time
import base64

filePath = "F:\\Github\\ComNetProject1\\Task1_CS\\Server\\serverData\\"
codepath = "F:\\Github\\ComNetProject1\\Task1_CS\\Server\\Chiper.txt"
BUFFSIZE = 51200
CODESIZE = 64
CODE = "utf-8"
# socket相关配置
# 建立UDP socket
serverAddress = ("127.0.0.1", 3100)
serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serverSocket.bind(serverAddress)
clientAddress = ("127.0.0.1", 3101)
serverSocket.listen(3)
#mainSocket = None
# socket相关功能函数
# 获得加密私钥


def getTheKey():
    if not os.path.isfile(codepath):
        print("Can not find the file of the key!\n")
        exit(0)
    f = open(codepath, 'rb')
    f.seek(5)
    key = f.read(CODESIZE)
    return key

# 数据内容加密解密


def chiperCode(s):
    key = getTheKey()
    realKey = key.decode(CODE)
    contest = s.decode(CODE)
    index = 0
    result = ""
    for i in range(0, len(contest)):
        if index >= len(realKey):
            index = 0
        result += chr(ord(realKey[index]) ^ ord(contest[i]))
        index = index+1
    return result.encode(CODE)
# 日志记录函数


def log(actoin, flag, exeTime):
    outFilePath = filePath+"logServer.txt"
    if os.path.isfile(outFilePath):
        fp = open(outFilePath, 'a')
        date = time.asctime(time.localtime(time.time()))
        fp.write(date+'\n'+"Action: "+actoin+'\n'+'Flag: '+flag+'\n'+'Time: ')
        fp.write(str(exeTime))
        fp.write('s\n\n')
        fp.close()
    else:
        print("[Error]:can not open the server log file")
        exit(0)
# 进度条函数


def progress_bar(num_cur, total):
    ratio = float(num_cur) / total
    percentage = int(ratio * 100)
    r = '\r[%s%s]%d%%' % (">"*percentage, " "*(100-percentage), percentage)
    sys.stdout.write(r)
    sys.stdout.flush()

# 列出资源文件夹ServerData中的数据文件，发送给客户端


def listFile():
    print("\n**********************************************************************")
    start = time.time()
    file_dir = filePath
    print("Ready to list file")
    for root, dirs, files in os.walk(file_dir):
        # print(root) #当前目录路径
        # print(dirs) #当前路径下所有子目录
        print(files)  # 当前路径下所有非目录子文件
        check1 = hashlib.md5()
        # files.remove("UDPServer.py")
        fileStr = str(files)
        fileBytes = fileStr.encode(CODE)
        check1.update(fileBytes)
        fileBytesChiper = chiperCode(fileBytes)
        mainSocket.send(fileBytesChiper)
        mainSocket.send(check1.hexdigest().encode("utf-8"))
    print("Have sent files!")
    end = time.time()
    log('The client request for the file list', 'OK', end-start)
    print("**********************************************************************\n")
    return 0

# 响应客户端下载文件的请求,先满足小型文件传输


def downloadFile(fileName):
    # 打开要传输的文件
    print("\n**********************************************************************")
    file = filePath + fileName
    print("send " + file)
    mainSockett, addr = serverSocket.accept()
    if not mainSockett:
        print("The data connection false")
        return 0

    start = time.time()
    if os.path.isfile(file):
        fsize = str(os.path.getsize(file))
        send_size = 0  # 定义已发送文件的大小
        mainSockett.send(fsize.encode("utf-8"))

        fs = open(file, "rb")
        print("Start downloading")
        check2 = hashlib.md5()
        while True:
            fileData = fs.read(BUFFSIZE)
            if not fileData:
                break
            check2.update(fileData)
            send_size += len(fileData)
            # Data=chiperCode(base64.b64encode(fileData))
            time.sleep(0.01)
            mainSockett.send(fileData)
            progress_bar(send_size, int(fsize, 10))
        print("\nDownload successfully")
        fs.close()
        checkData = check2.hexdigest().encode('utf-8')
        time.sleep(0.1)
        mainSockett.send(checkData)
        end = time.time()
        log('The client ask for download the file \'' +
            fileName+'\'', 'OK', end-start)
    else:
        print("ERROR:can't find file")
        error = "0"
        end = time.time()
        log('The client ask for download the file \'' +
            fileName+'\'', 'Fail:an error happened', end-start)
        mainSockett.send(error.encode("utf-8"))
    mainSockett.close()
    print("**********************************************************************\n")
    return 0

# 接收客户端上传的文件


def upload(fileName):
    print("\n**********************************************************************")
    print("Ready to upload file from client")
    start = time.time()
    try:
        data = mainSocket.recv(BUFFSIZE)
        fsize = int(data, 10)
        if fsize > 0:
            file = filePath + fileName
            fs = open(file, "wb")
            recvd_size = 0  # 定义已接收文件的大小
            print("Start uploading")
            check3 = hashlib.md5()
            while not recvd_size == fsize:
                if fsize - recvd_size > BUFFSIZE:
                    data = mainSocket.recv(BUFFSIZE)
                    check3.update(data)
                    recvd_size += len(data)
                    fs.write(data)
                    progress_bar(recvd_size, fsize)
                else:
                    data = mainSocket.recv(fsize - recvd_size)
                    recvd_size = fsize
                    check3.update(data)
                    progress_bar(recvd_size, fsize)
                    fs.write(data)
            checkData = mainSocket.recv(32)
            if not (checkData == check3.hexdigest().encode(CODE)):
                end = time.time()
                log('The client wish to upload the file \''+fileName +
                    '\' to server', 'Fail:the file has been broken', end-start)
                print("[Error]:The file may be broken\n")
            else:
                print("\nUpload successfully")
                end = time.time()
                log('The client wish to upload the file \'' +
                    fileName+'\' to server', 'OK', end-start)

            fs.close()

        else:
            end = time.time()
            log('The client wish to upload the file \''+fileName +
                '\' to server', 'Fail:an error happened', end-start)
            print("ERROR:can't find file")

    except:
        end = time.time()
        log('The client wish to upload the file \''+fileName +
            '\' to server', 'Fail:an error happened', end-start)
        print("ERROR:Upload timeout")
    print("**********************************************************************\n")
    return 0


# 命令部响应客户端请求部分
log('The server open', 'OK', 0)
start = time.time()

while True:
    # 服务器接收客户端消息

    print("waitting for connection")
    global mainSocket
    mainSocket, addr = serverSocket.accept()
    msg = '''\nInput one of the following command:\n 
                    * list  ------------------- list the files on server \n
                    * download [filename] -----download file from server\n
                    * upload [filename] -----------upload file to server \n
                    * exit ---------------------------------close socket\n '''
    mainSocket.send(msg.encode('utf-8'))
    while True:
        data = mainSocket.recv(BUFFSIZE)
        if not data:
            print("Client has exist")
            break
        tmp = data.decode("utf-8")
        text = tmp.split()
        print(text[0] + "---")
        # 收到请求文件的命令 download
        if text[0] == "download" and len(text) == 2:
            downloadFile(text[1])

        elif text[0] == "list" and len(text) == 1:
            listFile()

        elif text[0] == "upload" and len(text) == 2:
            upload(text[1])
        elif text[0] == 'exit':
            mainSocket.close()
            serverSocket.shutdown(2)
            break
serverSocket.close()
end = time.time()
log("The server close", 'OK', end-start)
