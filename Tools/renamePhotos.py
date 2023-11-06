# -*- coding: utf-8 -*-
from sys import argv
import os
import time
import shutil

def parseArgument():
    if len(argv) < 4:
        print("Usage: python renamePhotos.py fromDir toDir")
        exit(1)
    
    if argv[1] !=  'merge' and argv[1] != 'merge-by-date':
        print("Usage: python renamePhotos.py cmd<merge, merge-by-date> fromDir toDir")
        exit(1)
    
    if not os.path.isdir(argv[2]):
        print("Error source")
        exit(1)

    if not os.path.isdir(argv[3]):
        print("Error target")
        #exit(1)

    params = {}
    i = 1
    for a in argv[1:] :
        params[a] = i
        i += 1

    return argv[1], argv[2], argv[3],params

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

def copyFile(source, target):
    [dirname,filename]=os.path.split(target)
    if not os.path.exists(dirname):
        print("Make dir", dirname)
        os.path.os.mkdir(dirname)
    shutil.copy(source, target)
    
def enumAndRename(fromDir, toDir):
    fileList = GetFileList(fromDir, [])
    for f in fileList:
        t = os.path.getmtime(f)
        strDate = TimeStampToTime(t)
        [dirname,filename]=os.path.split(f)
        strNewName = os.path.join(toDir, strDate, strDate + '-' + filename)
        copyFile(f, strNewName)

def enumAndCopy(fromDir, toDir, printOnly = True):
    fileList = GetFileList(fromDir, [])
    for f in fileList:
        strNewPath = f.replace(fromDir, toDir)
        if os.path.exists(strNewPath):
            continue

        if printOnly == True:
            size = os.path.getsize(f)
            print( "File:{f}, Size:{size}",f, strNewPath, size)
            continue
        #do the real copy
        copyFile(f, strNewPath)
        


if __name__ == '__main__':
    cmd, fromDir ,toDir, params = parseArgument()

    print("cmd:{cmd}, fromDir:{fromDir}, toDir:{toDir}")

    if cmd == "merge":
        printOnly = False
        if params.has_key("printOnly"):
            printOnly = True
        enumAndCopy(fromDir, toDir,printOnly)
    elif cmd == "merge-by-date":
        enumAndRename(fromDir, toDir)

def check_datepattern(path):

    import re
    patterns = [r'\d{4}-\d{2}-\d{2}',r'\d{4}\d{2}\d{2}',r'\d{4}-\d{2}-\d{2}']
    sub_string = re.findall(pattern, os.path.basename(path))[0]
