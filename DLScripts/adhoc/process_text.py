from scipy.sparse import coo_matrix, csr_matrix
import re
import pprint
import sys
import numpy as np
import pickle

pp = pprint.PrettyPrinter(indent=4)
TRIGRAM_SIZE = 27000

def get_char_index(c):
    if c == '#':
        return 27
    if c == '$':
        return 28
    if str.isalpha(c):
        return (1 + ord(c) - ord('a'))
    return -1

def get_chartrimgram_index(str):
    if len(str) == 3:
        return get_char_index(str[0]) * 28 * 28 + get_char_index(str[1]) * 28 + get_char_index(str[2])
    return -1

def get_sentence_array(setence):
    array = np.zeros((1, TRIGRAM_SIZE))
    index_dic = get_setenece_onehot(setence)
    print(setence)
    for k,v in index_dic.items():
        array[0, k] = v
    return array
    
def get_setenece_onehot(setence):
    tri_dic = {}
    setence = setence.lower()
    setence = re.sub(r'\W+', '', setence)
    for word in setence.split():
        if len(word) == 0:
            continue
        word = '#' + word + '#'
        word_sparse_index = [get_chartrimgram_index(word[i:i + 3]) for i in range(len(word) - 2)]
        print(word_sparse_index)
        for index in word_sparse_index:
            if index > 0 and index < TRIGRAM_SIZE:
                if index in tri_dic:
                    tri_dic[index] += 1.
                else:
                    tri_dic[index] = 1.
    return tri_dic

def build_data(file):
    ith = 0
    query_rows, query_columns, query_data = [], [], []
    doc_rows, doc_columns, doc_data = [], [], []

    for line in open(file):
        tokens = line.split('\t')
        if len(tokens) >= 2:
            query = tokens[0]
            print(query)
            doc = tokens[1]
            query_onehot = get_setenece_onehot(query)

            for k, v in query_onehot.items():
                query_rows.append(ith)
                query_columns.append(k)
                query_data.append(v)

            doc_onehot = get_setenece_onehot(doc)
            for k, v in doc_onehot.items():
                doc_rows.append(ith)
                doc_columns.append(k)
                doc_data.append(v)
            ith += 1
            if ith % 10000 == 0:
                print(ith)
    query_csr = csr_matrix((query_data, (query_rows, query_columns)))
    doc_csr = csr_matrix((doc_data, (doc_rows, doc_columns)))
    print("query data")
    print(query_data)
    #print(query_rows)
    #print(query_columns)
    #print(doc_data)
    return query_csr, doc_csr

if __name__ == '__main__':
    q_csr, d_csr = build_data(sys.argv[1])
    #pickle.dump(q_csr, open(sys.argv[1] + '.query.pickle', 'wb', True), protocol=4)
    #pickle.dump(d_csr, open(sys.argv[1] + '.doc.pickle', 'wb', True), protocol=4)
    print("q_csr")
    print(q_csr.count_nonzero())
    print(q_csr.shape)
    # print(q_coo.shape)
    # print(q_coo.row)
    # print(q_coo.col)
    # print(len(q_coo.data))
    # print(q_coo.count_nonzero())
    # print(d_coo.count_nonzero())
