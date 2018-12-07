from sys import argv
import os
import time
import shutil

def TimeStampToTime(timestamp):
    timeStruct = time.localtime(timestamp)
    return time.strftime('%Y-%m-%d',timeStruct)

def GetFileList(dir, fileList):
    newDir = dir
    if os.path.isfile(dir):
        fileList.append(dir)
    elif os.path.isdir(dir):  
        for s in os.listdir(dir):
            #如果需要忽略某些文件夹，使用以下代码
            #if s == "xxx":
                #continue
            newDir=os.path.join(dir,s)
            GetFileList(newDir, fileList)  
    return fileList

def enumAndRename(fromDir, toDir):
    fileList = GetFileList(fromDir, [])
    for f in fileList:
        t = os.path.getatime(f)
        strDate = TimeStampToTime(t)
        [dirname,filename]=os.path.split(f)
        strNewDir = os.path.join(toDir, strDate)
        if not os.path.exists(strNewDir):
            os.path.os.mkdir(strNewDir)
        strNewName = os.path.join(toDir, strDate, strDate + filename)
        print(strNewName)
        shutil.copy(f, strNewName)

if __name__ == '__main__':
    fromDir = argv[1]
    toDir = argv[2]
    print(fromDir)
    print(toDir)
    if not os.path.isdir(fromDir):
        print("Error source")

    if not os.path.isdir(toDir):
        print("Error target")
    
    enumAndRename(fromDir, toDir)
