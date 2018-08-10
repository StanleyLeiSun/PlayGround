import tensorflow as tf
import numpy as np
import os
import time
import datetime
from lstm_model import RNN_Model
import data_helper

tf.reset_default_graph()

saver = tf.train.Saver()

with tf.Session() as sess:
  saver.restore(sess, "/tmp/model.ckpt")
  print("Model restored.")
  