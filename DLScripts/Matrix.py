from scipy.sparse import coo_matrix, csr_matrix
import re
import pprint
import sys
import numpy as np
import pickle


mtx = csr_matrix((3, 4), dtype=np.int8)
mtx.todense()
