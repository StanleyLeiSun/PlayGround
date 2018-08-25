# -*- coding:utf-8 -*-
"""
author:stansun
"""
import numpy as np
import pandas as pd
import sklearn.feature_extraction.text as skyfe
import sys
if (sys.version_info[0] < 3):
    import cPickle as p
    reload(sys)  # Reload does the trick!
    sys.setdefaultencoding('UTF8')
else:
    import pickle as p

import lstm_config

def load_data(max_len,batch_size,n_words=20000,valid_portion=0.1,sort_by_len=True):
    
    train_set_x, train_set_y = load_dataset_file()

    train_set_y = train_set_y.astype(float)
   
    train_set_y = train_set_y/5 
    #train_set length
    n_samples= len(train_set_x)
    #shuffle and generate train and valid dataset
    sidx = range(n_samples)
    n_train = int(np.round(n_samples * (1. - valid_portion)))
    valid_set_x = [train_set_x[s] for s in sidx[n_train:]]
    valid_set_y = [train_set_y[s] for s in sidx[n_train:]]
    train_set_x = [train_set_x[s] for s in sidx[:n_train]]
    train_set_y = [train_set_y[s] for s in sidx[:n_train]]


    train_set = (train_set_x, train_set_y)
    valid_set = (valid_set_x, valid_set_y)


    #remove unknow words
    def remove_unk(x):
        return [[1 if w >= n_words else w for w in sen] for sen in x]

    test_set_x, test_set_y = train_set_x, train_set_y 
    valid_set_x, valid_set_y = valid_set
    train_set_x, train_set_y = train_set

    train_set_x = remove_unk(train_set_x)
    valid_set_x = remove_unk(valid_set_x)
    test_set_x = remove_unk(test_set_x)



    def len_argsort(seq):
        return sorted(range(len(seq)), key=lambda x: len(seq[x]))

    if sort_by_len:
        sorted_index = len_argsort(test_set_x)
        test_set_x = [test_set_x[i] for i in sorted_index]
        test_set_y = [test_set_y[i] for i in sorted_index]

        sorted_index = len_argsort(valid_set_x)
        valid_set_x = [valid_set_x[i] for i in sorted_index]
        valid_set_y = [valid_set_y[i] for i in sorted_index]


        sorted_index = len_argsort(train_set_x)
        train_set_x = [train_set_x[i] for i in sorted_index]
        train_set_y = [train_set_y[i] for i in sorted_index]

        train_set=(train_set_x,train_set_y)
        valid_set=(valid_set_x,valid_set_y)
        test_set=(test_set_x,test_set_y)


        new_train_set_x=np.zeros([len(train_set[0]),max_len])
        new_train_set_y=np.zeros(len(train_set[0]))

        new_valid_set_x=np.zeros([len(valid_set[0]),max_len])
        new_valid_set_y=np.zeros(len(valid_set[0]))

        new_test_set_x=np.zeros([len(test_set[0]),max_len])
        new_test_set_y=np.zeros(len(test_set[0]))

        mask_train_x=np.zeros([max_len,len(train_set[0])])
        mask_test_x=np.zeros([max_len,len(test_set[0])])
        mask_valid_x=np.zeros([max_len,len(valid_set[0])])



    def padding_and_generate_mask(x,y,new_x,new_y,new_mask_x):

        for i,(x,y) in enumerate(zip(x,y)):
            #whether to remove sentences with length larger than maxlen
            if len(x)<=max_len:
                new_x[i,0:len(x)]=x
                new_mask_x[0:len(x),i]=1
                new_y[i]=y
            else:
                new_x[i]=(x[0:max_len])
                new_mask_x[:,i]=1
                new_y[i]=y
        new_set =(new_x,new_y,new_mask_x)
        del new_x,new_y
        return new_set

    train_set=padding_and_generate_mask(train_set[0],train_set[1],new_train_set_x,new_train_set_y,mask_train_x)
    test_set=padding_and_generate_mask(test_set[0],test_set[1],new_test_set_x,new_test_set_y,mask_test_x)
    valid_set=padding_and_generate_mask(valid_set[0],valid_set[1],new_valid_set_x,new_valid_set_y,mask_valid_x)

    return train_set,valid_set,test_set

def load_dataset_file():
    dataset_path= lstm_config.data_root + 'tencent_quality.pickle'
    f=open(dataset_path,'rb')
    print ('load data from %s'%dataset_path)
    #train_set = np.array(pkl.load(f))
    #test_set = np.array(pkl.load(f))
    dataset = p.load(f)
    f.close()

    train_set_x = dataset['x']
    train_set_y = dataset['y']
    return train_set_x, train_set_y

#return batch dataset
def batch_iter(data,batch_size):

    #get dataset and label
    x,y,mask_x=data 
    x=np.array(x)
    y=np.array(y)
    data_size=len(x)
    num_batches_per_epoch=int((data_size-1)/batch_size)
    for batch_index in range(num_batches_per_epoch):
        start_index=batch_index*batch_size
        end_index=min((batch_index+1)*batch_size,data_size)
        return_x = x[start_index:end_index]
        return_y = y[start_index:end_index]
        return_mask_x = mask_x[:,start_index:end_index]
        # if(len(return_x)<batch_size):
        #     print(len(return_x))
        #     print return_x
        #     print return_y
        #     print return_mask_x
        #     import sys
        #     sys.exit(0)
        yield [return_x,return_y,return_mask_x]



#region vectorlize doc

def save_embedded(mapping, training_x, training_y, version):
    data = {'mapping':mapping, 'x': training_x, 'y': training_y}
    with open(lstm_config.data_root+version+'.pickle', 'wb') as f:
        p.dump(data, f)

def build_dict(d, sentence):
    for w in sentence:
        if w in d:
            d[w] +=1
        else:
            d[w] = 1

def dict_to_embedding(dic, vacabulary_size, base_idx=0):
    ret_map = {}
    for i in range(0, vacabulary_size):
        ret_map[dic[i][0]] = vacabulary_size - i + base_idx

    return ret_map

def build_embedding_map(titles vacabulary_size):
    dic = {}
    for s in titles:
        build_dict(dic, s)

    sortdict = sorted(dic.items(), key = lambda x: x[1], reverse=True) 
    print("Total vacabulary: %d, reduce to: %d"%(len(sortdict), vacabulary_size))
         
    return dict_to_embedding(sortdict, vacabulary_size)

def encoding_sentence(sentence, mapping ):
    return [mapping.get(w,0) for w in sentence ]

def vector_rawdata_file():
    dataset_path='~/data/tencent-dump.csv'
    article = pd.read_table(dataset_path,  error_bad_lines=False)
    article = article[['title','srouce', 'quality']].drop_duplicates().dropna()
    train_set_x = np.array(article['title'], dtype='unicode_')
    train_set_y = np.array(article[['quality']], dtype='unicode_')
    sources = np.array(article['source'], dtype='unicode_')
    
    mapping = build_embedding_map(train_set_x, 5000)

    source_dic = {}
    build_dict(source_dic, sources)
    source_mapping = dict_to_embedding(source_dic, len(source_dic), len(mapping))
    
    train_set_x = [ [source_mapping(sources[i])] + encoding_sentence(s, mapping) for i,s in enumerate(train_set_x)]
    save_embedded(mapping, train_set_x, train_set_y, 'tencent_quality')

    return train_set_x, train_set_y

def build_vectors(sentences, vacabulary_size):
    vectorizer = skyfe.CountVectorizer()
    trans = vectorizer.fit_transform(corpus)
    fname = vectorizer.get_feature_names()
    print (trans)
    print (trans.toarray())
    print(fname)

    #enable tf-idf
    transformer = skyfe.TfidfTransformer()
    tfidf = transformer.fit_transform(trans)  
    print(tfidf.toarray())
    print(tfidf.get_feature_names())

    #hashed
    vectorizer2 = skyfe.HashingVectorizer(n_features = 6,norm = None)
    trans = vectorizer2.fit_transform(corpus)
    #fname = vectorizer2.get_feature_names()
    print (trans.toarray())
    #print (fname)

#endregion

def test():
    train_set_x, train_set_y = load_rawdata_file()


if __name__ == "__main__":
    vector_rawdata_file()
    #test()

    #load_data(2000, 200)

    #titles = ["abcdefffh", "hello lsdm"]

    # corpus=["I come to China to travel", 
    #     "This is a car polupar in China",          
    #     "I love tea and Apple ",   
    #     "The work is to write some papers in science"] 

    #build_vectors(corpus, 200)

    #map = build_embedding(titles, 6)
    #f = open("mappingfile", 'wb')
    #p.dump(map, f)
    #f.close()

    #print(map)

    #print(encoding_sentence("hlala  ff", map))
