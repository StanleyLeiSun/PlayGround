import os

import cv2
import numpy as np
from sklearn.cluster  import KMeans
from matplotlib import pyplot as plt

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
            ret_files.append(get_file_list(newDir))
    
    return ret_files

def load_file_names(img_root):
    file_names=get_file_list(img_root)
    #keep only images
    pic_names=['bmp','jpg','png','tiff','gif','pcx','tga','exif','fpx','svg','psd','cdr','pcd','dxf','ufo','eps','ai','raw','WMF']
    for name in file_names:
        file_format=name.split('.')[-1]
        if file_format not in pic_names:
            file_names.remove(name)

#build image SIFT and file hash dataset

def get_sift(images):
    
    sift_det=cv2.xfeatures2d.SIFT_create()
    des_list=[]
    des_matrix=np.zeros((1,128))
    for path in images:
        img=cv2.imread(path)
        gray=cv2.cvtColor(img,cv2.COLOR_RGB2GRAY)
        kp,des=sift_det.detectAndCompute(gray,None)
        if des!=None:
                des_matrix=np.row_stack((des_matrix,des))
        des_list.append(des)
    
    des_matrix=des_matrix[1:,:]   # the des matrix of sift

#cluster and caculate the center for feature

def clustering(num_clusters, des_matrix):

    kmeans=KMeans(n_clusters=num_clusters,random_state=33)
    kmeans.fit(des_matrix)
    centres = kmeans.cluster_centers_ 
    
    #return centres,des_list


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


if __name__ == '__main__':
    files = get_file_list("/mnt/d/BaiduNetdiskDownload/")
    print(len(files))