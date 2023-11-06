import os

def get_file_list(dir):
    ret_files = []
    if os.path.isfile(dir):
        ret_files.append(dir)
    elif os.path.isdir(dir):  
        for s in os.listdir(dir):
            #if s == "xxx":
                #continue
            newDir=os.path.join(dir,s)
            ret_files.extend(get_file_list(newDir))
    
    return ret_files