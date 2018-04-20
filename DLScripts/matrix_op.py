import numpy as np
#import pickle
#import tensorflow as tf
import random
#from scipy.sparse import coo_matrix, csr_matrix

#matrix #1 2*3*4
mat1_a1_len = 2
mat1_a2_len = 3
mat1_a3_len = 4

#matrix #2 3*4
mat2_a1 = 3
mat2_a2 = 4


def build_graph():
    pass

def run():
    pass

# sess = tf.InteractiveSession()

# a = tf.constant([1, 2, 3, 4, 5, 6], shape=[2, 3]) #=> [[1. 2. 3.] [4. 5. 6.]]
# b = tf.constant([7, 8, 9, 10, 11, 12], shape=[3, 2]) #=> [[7. 8.] [9. 10.] [11. 12.]]
# c = tf.matmul(a, b) #=> [[58 64] [139 154]]

# a = tf.constant(np.arange(1,13), shape=[2, 2, 3]) #=> [[[ 1. 2. 3.] [ 4. 5. 6.]], [[ 7. 8. 9.] [10. 11. 12.]]]

# tf.global_variables_initializer().run()

# print("c:",c.eval())

#numpy matrix operation
def TestBroadCasting():
    #broadcasting
    a = np.array( [ [ 1,2 ], [ 3,4 ] ] )
    b = np.array( [ [ 1,2 ], [ 3,4 ] ] )
    c = np.array( [[1], [2]])
    d = 3.0
    e = 2.0
    f = np.array( [ [[ 1,2 ], [ 3,4 ]] ] )
    g = np.array( [ [[ 1,2 ]], [[ 3,4 ]] ] )
    h = np.array( [ [[ 1,2,3 ], [ 3,4,5 ]] ] )
    i = np.array( [ [[ 1,2,3 ], [ 3,4,5 ], [ 3,4,5 ]] ] )
    j = np.array( [ [[ 1,2 ], [ 3,4 ]],  [[ 1,2 ], [ 3,4 ]] ] )
    k = np.array( [ [ [ 1,2 ], [ 3,4 ] ], [ [ 2,4 ], [ 3,4 ] ] ] )
    #print ("a+d=", a+d)
    #print ("a*e=", a*e)
    #print ("a+c=", a+c)
    print ("a*b=", np.matmul(a,b))
    print ("a*f=", np.matmul(a,f))
    print("a shape:", a.shape, "f's shape", f.shape,  "g's shape", g.shape)
    #print ("a*g=", np.matmul(a,g)) =>doesn't work
    print ("a*h=", np.matmul(a,h))
    #print ("a*i=", np.matmul(a,i)) => doesn't work
    print ("a*j=", np.matmul(a,j))
    print ("k*j=", np.matmul(k,j))

def TestTensorDot():
    a = np.array(range(1, 5))
    a.shape = (2, 2)
    A = np.array(('a', 'b', 'c', 'd'), dtype=object)
    A.shape = (2, 2)
    print(a)
    print(A)
    #print(np.matmul(a,A))
    print("1:", np.tensordot(a, A) )
    print("2:",np.tensordot(a, A, 1))
    print("3:",np.tensordot(a, A, 0))
    print("4:",np.tensordot(a, A, (0, 1)))
    print("5:",np.tensordot(a, A, (1, 0)))
    # np.tensordot(a, A, (2, 1))
    # np.tensordot(a, A, ((0, 1), (0, 1)))
    # np.tensordot(a, A, ((2, 1), (1, 0)))

if __name__ == '__main__':
    TestTensorDot()