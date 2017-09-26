from scipy.sparse import coo_matrix, csr_matrix
import re
import pprint
import sys
import numpy as np
import pickle
import tensorflow as tf

TRIGRAM_D = 5
L1_N = 3
l1_par_range = 10

#mtx = csr_matrix((3, TRIGRAM_D), dtype=np.int8)
mtx = csr_matrix( np.random.randint(5, size=(3, TRIGRAM_D)) )
#print(mtx.todense())

weight1 = tf.Variable(tf.random_uniform([TRIGRAM_D, L1_N], -l1_par_range, l1_par_range,dtype=tf.int32))



doc_batch = tf.sparse_placeholder(tf.int32, shape=(None, TRIGRAM_D), name='DocBatch')
 
bias1 = tf.Variable(tf.random_uniform([L1_N], 0, l1_par_range, dtype=tf.int32))
 
doc_l1 = tf.sparse_tensor_dense_matmul(doc_batch, weight1)/bias1

doc_in = mtx.tocoo()
doc_in = tf.SparseTensorValue(
        np.transpose([np.array(doc_in.row, dtype=np.int64), np.array(doc_in.col, dtype=np.int64)]),
        np.array(doc_in.data, dtype=np.float),
        np.array((doc_in.shape[0], TRIGRAM_D), dtype=np.int64))

doc_y = tf.nn.relu(doc_l1)

norm1 = tf.reduce_sum(doc_y, 0, True)

tile1 = tf.tile(norm1, [2 + 1, 1])
		
sess = tf.Session()
sess.run(tf.global_variables_initializer())


#print("Weight1")
#print (sess.run(weight1))

#print("Bias1")
#print (sess.run(bias1))

#print("result")
#print (sess.run(doc_l1, feed_dict = {doc_batch:doc_in}))

print("doc_y")
print(sess.run(doc_y, feed_dict = {doc_batch:doc_in}))

print("norm1")
print(sess.run(norm1, feed_dict = {doc_batch:doc_in}))

print("tile1")
print(sess.run(tile1, feed_dict = {doc_batch:doc_in}))
