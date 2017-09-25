from scipy.sparse import coo_matrix, csr_matrix
import re
import pprint
import sys
import numpy as np
import pickle
import tensorflow as tf

TRIGRAM_D = 8
L1_N = 3
l1_par_range = 1

mtx = csr_matrix((3, TRIGRAM_D), dtype=np.int8)
#print(mtx.todense())

weight1 = tf.Variable(tf.random_uniform([TRIGRAM_D, L1_N], -l1_par_range, l1_par_range))



doc_batch = tf.sparse_placeholder(tf.float32, shape=(None, TRIGRAM_D), name='DocBatch')
 
bias1 = tf.Variable(tf.random_uniform([L1_N], -l1_par_range, l1_par_range))
 
doc_l1 = tf.sparse_tensor_dense_matmul(doc_batch, weight1) + bias1

doc_in = mtx.tocoo()
doc_in = tf.SparseTensorValue(
        np.transpose([np.array(doc_in.row, dtype=np.int64), np.array(doc_in.col, dtype=np.int64)]),
        np.array(doc_in.data, dtype=np.float),
        np.array((doc_in.shape[0], TRIGRAM_D), dtype=np.int64))

sess = tf.Session()
sess.run(tf.global_variables_initializer())


print("Weight1")
print (sess.run(weight1))

print("Bias1")
print (sess.run(bias1))

print("result")
print (sess.run(doc_l1, feed_dict = {doc_batch:doc_in}))