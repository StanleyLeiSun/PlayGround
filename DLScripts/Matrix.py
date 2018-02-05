# pylint: disable-msg=C0103

#import re
#import pprint
#import sys
import numpy as np
#import pickle
import tensorflow as tf
import random
from scipy.sparse import coo_matrix, csr_matrix

TRIGRAM_D = 5
L1_N = 3
L1_PAR_RANGE = 10

#mtx = csr_matrix((3, TRIGRAM_D), dtype=np.int8)
mtx = csr_matrix(np.random.randint(1, 5, size=(3, TRIGRAM_D)))

doc_in = mtx.tocoo()
doc_in = tf.SparseTensorValue(
    np.transpose([np.array(doc_in.row, dtype=np.int64), np.array(doc_in.col, dtype=np.int64)]),
    np.array(doc_in.data, dtype=np.float),
    np.array((doc_in.shape[0], TRIGRAM_D), dtype=np.int64))

#print(mtx.todense())

weight1 = tf.Variable(
    tf.random_uniform([TRIGRAM_D, L1_N], -L1_PAR_RANGE, L1_PAR_RANGE, dtype=tf.int32))

doc_batch = tf.sparse_placeholder(tf.int32, shape=(None, TRIGRAM_D), name='DocBatch')

bias1 = tf.Variable(tf.random_uniform([L1_N], 0, L1_PAR_RANGE, dtype=tf.int32))

doc_l1 = tf.sparse_tensor_dense_matmul(doc_batch, weight1)/bias1

doc_y = tf.nn.relu(doc_l1)

norm1 = tf.reduce_sum(doc_y, 0, True)

tile1 = tf.tile(norm1, [2 + 1, 1])

tile2 = tf.tile(norm1, [1, 2])
tile3 = tf.tile(norm1, [2, 1])

n_doc_y = doc_y
temp = tf.tile(n_doc_y, [1, 1])

NEG = 6
BS = 3
for i in range(NEG):
    rand = int((random.random() + i) * BS / NEG)
    n_doc_y = tf.concat([n_doc_y,
                        tf.slice(temp, [rand, 0], [BS - rand, -1]),
                        tf.slice(temp, [0, 0], [rand, -1])], 0)


sess = tf.Session()
sess.run(tf.global_variables_initializer())


#print("Weight1")
#print (sess.run(weight1))

#print("Bias1")
#print (sess.run(bias1))

#print("result")
#print (sess.run(doc_l1, feed_dict = {doc_batch:doc_in}))

print("doc_y")
print(sess.run(doc_y, feed_dict={doc_batch:doc_in}))

print("norm1")
#print(sess.run(norm1, feed_dict={doc_batch:doc_in}))

print("tile1")
#print(sess.run(tile1, feed_dict={doc_batch:doc_in}))

print("tile2")
#print(sess.run(tile2, feed_dict={doc_batch:doc_in}))

print("tile3")
#print(sess.run(tile3, feed_dict={doc_batch:doc_in}))

print("n_doc_y")
print(sess.run(n_doc_y, feed_dict={doc_batch:doc_in}))