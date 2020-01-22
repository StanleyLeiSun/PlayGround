import os

#import cv2
import numpy as np
from sklearn.cluster  import KMeans
from matplotlib import pyplot as plt
import pickle  
import gc
import hashlib

#load image file names

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

def load_file_names(img_root):
    file_names=get_file_list(img_root)
    img_names = []
    #keep only images
    pic_names=['bmp','jpg','png','tiff','gif','pcx','tga','exif','fpx','svg','psd','cdr','pcd','dxf','ufo','eps','ai','raw','WMF']
    for name in file_names:
        file_format=name.split('.')[-1]
        if file_format.lower() in pic_names:
            #file_names.remove(name)
            img_names.append(name)
    
    return img_names


def get_file_hash(file_path):
    md5_1 = hashlib.md5()
    with open(file_path,'rb') as f:
        while 1:
            data =f.read()
            if data:
                md5_1.update(data)
            else:
                break
    ret = md5_1.hexdigest()
    return ret


#get file info {name, size, hash, full_path}
def get_file_info(file_name):
    [dirname,filename]=os.path.split(file_name)
    file_size = os.path.getsize(file_name)
    file_hash = get_file_hash(file_name)
    return (filename,file_size, file_hash, file_name)


#build image SIFT and file hash dataset

def get_sift(images):
    
    sift_det=cv2.xfeatures2d.SIFT_create(500)
    des_list=[]
    total = len(images)
    i = 1
    des_matrix=np.zeros((1,128))
    for path in images:
        #print("Going to process:" + path, end='\r')
        img=cv2.imread(path)
        gray=cv2.cvtColor(img,cv2.COLOR_RGB2GRAY)
        kp,des=sift_det.detectAndCompute(gray,None)
        print("{2:.2f}% Done. Img: {0} has {1} features.".format( path, len(des), i*100/total), end='\r')
        i = i + 1
        if len(des) > 0:
                des_matrix=np.row_stack((des_matrix,des))
        des_list.append(des)
        gc.collect()
    
    des_matrix=des_matrix[1:,:]   # the des matrix of sift
    print("")
    return des_matrix, des_list

#cluster and caculate the center for feature

def clustering(num_clusters, des_matrix):

    kmeans=KMeans(n_clusters=num_clusters,random_state=33)
    kmeans.fit(des_matrix)
    centres = kmeans.cluster_centers_ 

    return centres


#convert SIFT to feature
def des2feature(des,num_words,centures):
    img_feature_vec=np.zeros((1,num_words),'float32')
    for i in range(des.shape[0]):
        feature_k_rows=np.ones((num_words,128),'float32')
        feature=des[i]
        feature_k_rows=feature_k_rows*feature
        feature_k_rows=np.sum((feature_k_rows-centures)**2,1)
        index=np.argmax(feature_k_rows)
        img_feature_vec[0][index]+=1
    return img_feature_vec

#store the features, file hash and SIFT as index

#given an image find the most similar
def getNearestImg(feature,dataset,num_close):
    
    features=np.ones((dataset.shape[0],len(feature)),'float32')
    features=features*feature
    dist=np.sum((features-dataset)**2,1)
    dist_index=np.argsort(dist)
    return dist_index[:num_close]


def showImg(target_img_path,index,dataset_paths):
    
    # get img path
    paths=[]
    for i in index:
        paths.append(dataset_paths[i])
        
    plt.figure(figsize=(10,20))
    plt.subplot(432),plt.imshow(plt.imread(target_img_path)),plt.title('target_image')
    
    for i in range(len(index)):
        plt.subplot(4,3,i+4),plt.imshow(plt.imread(paths[i]))
    plt.show()

def find_dup_hash(files):
    file_dict = {}
    dup_files = []
    for f in files:
        file_info = get_file_info(f)
        exist = file_dict.get(file_info[2])

        if (exist is None):
            file_dict[file_info[2]] = file_info
        else: #find a dup
            if ((exist[0] == file_info[0]) is False):
                print ("find dup:")
                print (exist[3])
                print (file_info[3])
            
            dup_files.append(file_info)
    
    return dup_files
    

if __name__ == '__main__':
    img_path = "/mnt/d/pic/index/2017/"
    files = get_file_list(img_path)
    print("Found %d files totally."%len(files))

    img_files = load_file_names(img_path)
    img_count = len(img_files)
    print("Identified %d images."%img_count)

    dup = find_dup_hash(files)

    sum_size = 0
    for f in dup:
        sum_size += f[1]
    
    print("Find {0} dup. Total Size: {1}MB".format(len(dup), (int)(sum_size/(1024*1024))))

    # idx = 0
    # while (idx < img_count):
    #     last_idx = idx + 1000
    #     if last_idx >= img_count:
    #         last_idx = img_count - 1
    #     matrix, l = get_sift(img_files[idx:last_idx])
    #     print("Going to save matrix start from:%d"%idx)

    #     with open(img_path + 'img_features_%d.data'%idx, 'wb') as f:  
    #         feature_string = pickle.dump(matrix, f) 
    #     idx = last_idx + 1

    #c = clustering(100, matrix)
    #with open(img_path + 'img_cluster.data', 'wb') as f:  
    #    matrix_string = pickle.dump(c, f) 

    #with open(fn, 'r') as f:  
    #    summer = pickle.load(f) 
    print("We're done. Bye.")
