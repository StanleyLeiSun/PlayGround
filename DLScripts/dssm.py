import pickle
import random
import time
import sys
import numpy as np
import tensorflow as tf
import process_text
from scipy import spatial
import argparse

flags = tf.app.flags
FLAGS = flags.FLAGS

flags.DEFINE_string('summaries_dir', 'data\dssm-400-120-relu', 'Summaries directory')
flags.DEFINE_float('learning_rate', 0.1, 'Initial learning rate.')
flags.DEFINE_integer('max_steps', 408, 'Number of steps to run trainer.')
flags.DEFINE_integer('epoch_steps', 408, "Number of steps in one epoch.")
flags.DEFINE_integer('pack_size', 20, "Number of batches in one pickle pack.")
flags.DEFINE_bool('gpu', 1, "Enable GPU or not")
parser = argparse.ArgumentParser(description='dssm trainer', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('--train_query', type=str, dest='train_query_file', required=True, help='training query file')
parser.add_argument('--test_query', type=str, dest='test_query_file', required=True, help='test query file')
parser.add_argument('--train_doc', type=str, dest='train_doc_file', required=True, help='training doc file')
parser.add_argument('--test_doc', type=str, dest='test_doc_file', required=True, help='test doc file')
parser.add_argument('--out', type=str, dest='out_file', default='pred.txt', help='pred output')
parser.add_argument('--epoch', type=int, dest='epoch_num', default=5, help='pred output')
parser.add_argument('--lr', type=float, dest='learning_rate',default=0.1)
parser.add_argument('--bs', type=int, dest='batch_size', default=1024)
args = parser.parse_args()


start = time.time()
#query_train_data, doc_train_data = process_text.build_data(args.train_file)
#query_test_data, doc_test_data = process_text.build_data(args.test_file)

query_train_data = pickle.load(open(args.train_query_file, 'rb'))
doc_train_data = pickle.load(open(args.train_doc_file, 'rb'))
query_test_data = pickle.load(open(args.test_query_file, 'rb'))
doc_test_data = pickle.load(open(args.test_doc_file, 'rb'))

end = time.time()
print("Loading data from HDD to memory: %.2fs" % (end - start))

TRIGRAM_D = 27000
NEG = 50
BS = args.batch_size
L1_N = 400
L2_N = 120

train_iter_num_epoch = int(query_train_data.shape[0] / BS)
test_iter_num_epoch = int(query_test_data.shape[0] / BS)
print(train_iter_num_epoch, test_iter_num_epoch)

query_in_shape = np.array([BS, TRIGRAM_D], np.int64)
doc_in_shape = np.array([BS, TRIGRAM_D], np.int64)


def variable_summaries(var, name):
    """Attach a lot of summaries to a Tensor."""
    with tf.name_scope('summaries'):
        mean = tf.reduce_mean(var)
        tf.summary.scalar('mean/' + name, mean)
        with tf.name_scope('stddev'):
            stddev = tf.sqrt(tf.reduce_sum(tf.square(var - mean)))
        tf.summary.scalar('sttdev/' + name, stddev)
        tf.summary.scalar('max/' + name, tf.reduce_max(var))
        tf.summary.scalar('min/' + name, tf.reduce_min(var))
        tf.summary.histogram(name, var)


with tf.name_scope('input'):
    # Shape [BS, TRIGRAM_D].
    query_batch = tf.sparse_placeholder(tf.float32, shape=(None, TRIGRAM_D), name='QueryBatch')
    # Shape [BS, TRIGRAM_D]
    doc_batch = tf.sparse_placeholder(tf.float32, shape=(None, TRIGRAM_D), name='DocBatch')

with tf.name_scope('L1'):
    l1_par_range = np.sqrt(6.0 / (TRIGRAM_D + L1_N))
    weight1 = tf.Variable(tf.random_uniform([TRIGRAM_D, L1_N], -l1_par_range, l1_par_range))
    bias1 = tf.Variable(tf.random_uniform([L1_N], -l1_par_range, l1_par_range))
    variable_summaries(weight1, 'L1_weights')
    variable_summaries(bias1, 'L1_biases')

    # query_l1 = tf.matmul(tf.to_float(query_batch),weight1)+bias1
    query_l1 = tf.sparse_tensor_dense_matmul(query_batch, weight1) + bias1
    # doc_l1 = tf.matmul(tf.to_float(doc_batch),weight1)+bias1
    doc_l1 = tf.sparse_tensor_dense_matmul(doc_batch, weight1) + bias1

    query_l1_out = tf.nn.relu(query_l1)
    doc_l1_out = tf.nn.relu(doc_l1)

with tf.name_scope('L2'):
    l2_par_range = np.sqrt(6.0 / (L1_N + L2_N))

    weight2 = tf.Variable(tf.random_uniform([L1_N, L2_N], -l2_par_range, l2_par_range))
    bias2 = tf.Variable(tf.random_uniform([L2_N], -l2_par_range, l2_par_range))
    variable_summaries(weight2, 'L2_weights')
    variable_summaries(bias2, 'L2_biases')
    query_l2 = tf.matmul(query_l1_out, weight2) + bias2
    doc_l2 = tf.matmul(doc_l1_out, weight2) + bias2
    query_y = tf.nn.relu(query_l2)
    doc_y = tf.nn.relu(doc_l2)


with tf.name_scope('FD_rotate'):

    n_doc_y = doc_y
    print(query_y.shape)
    # Rotate FD+ to produce 50 FD-
    temp = tf.tile(n_doc_y, [1, 1])

    for i in range(NEG):
        rand = int((random.random() + i) * BS / NEG)
        n_doc_y = tf.concat([n_doc_y,
                           tf.slice(temp, [rand, 0], [BS - rand, -1]),
                           tf.slice(temp, [0, 0], [rand, -1])], 0)

with tf.name_scope('Cosine_Similarity'):
    # Cosine similarity
    query_norm = tf.tile(tf.sqrt(tf.reduce_sum(tf.square(query_y), 1, True)), [NEG + 1, 1])
    doc_norm = tf.sqrt(tf.reduce_sum(tf.square(n_doc_y), 1, True))

    prod = tf.reduce_sum(tf.multiply(tf.tile(query_y, [NEG + 1, 1]), n_doc_y), 1, True)
    norm_prod = tf.multiply(query_norm, doc_norm)

    cos_sim_raw = tf.truediv(prod, norm_prod)
    cos_sim = tf.transpose(tf.reshape(tf.transpose(cos_sim_raw), [NEG + 1, BS])) * 20

with tf.name_scope('Loss'):
    # Train Loss
    prob = tf.nn.softmax((cos_sim))
    hit_prob = tf.slice(prob, [0, 0], [-1, 1])
    loss = -tf.reduce_sum(tf.log(hit_prob)) / BS
    tf.summary.scalar('loss', loss)

with tf.name_scope('Training'):
    # Optimizer
    train_step = tf.train.GradientDescentOptimizer(args.learning_rate).minimize(loss)

# with tf.name_scope('Accuracy'):
#     correct_prediction = tf.equal(tf.argmax(prob, 1), 0)
#     accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))
#     tf.scalar_summary('accuracy', accuracy)

merged = tf.summary.merge_all()

with tf.name_scope('Test'):
    average_loss = tf.placeholder(tf.float32)
    loss_summary = tf.summary.scalar('average_loss', average_loss)


def pull_batch(query_data, doc_data, batch_idx, batch_size):
    # start = time.time()
    start, end = batch_idx * batch_size, ( batch_idx + 1 ) * batch_size
    query_in = query_data[start:end, :]
    doc_in = doc_data[start:end,  :]
    # if batch_idx == 0:
    #     print(query_in.getrow(53))
    query_in = query_in.tocoo()
    doc_in = doc_in.tocoo()

    query_in = tf.SparseTensorValue(
        np.transpose([np.array(query_in.row, dtype=np.int64), np.array(query_in.col, dtype=np.int64)]),
        np.array(query_in.data, dtype=np.float),
        np.array((query_in.shape[0], TRIGRAM_D), dtype=np.int64))
    doc_in = tf.SparseTensorValue(
        np.transpose([np.array(doc_in.row, dtype=np.int64), np.array(doc_in.col, dtype=np.int64)]),
        np.array(doc_in.data, dtype=np.float),
        np.array((doc_in.shape[0], TRIGRAM_D), dtype=np.int64))
    return query_in, doc_in


def feed_dict(Train, batch_idx, batch_size):
    """Make a TensorFlow feed_dict: maps data onto Tensor placeholders."""
    if Train:
        query_in, doc_in = pull_batch(query_train_data, doc_train_data, batch_idx, batch_size)
    else:
        query_in, doc_in = pull_batch(query_test_data, doc_test_data, batch_idx, batch_size)
    return {query_batch: query_in, doc_batch: doc_in}


config = tf.ConfigProto()  # log_device_placement=True)
config.gpu_options.allow_growth = True
# if not FLAGS.gpu:
# config = tf.ConfigProto(device_count= {'GPU' : 0})
saver = tf.train.Saver()

with tf.Session(config=config) as sess:
    sess.run(tf.global_variables_initializer())
    train_writer = tf.summary.FileWriter(FLAGS.summaries_dir + '/train', sess.graph)
    test_writer = tf.summary.FileWriter(FLAGS.summaries_dir + '/test', sess.graph)

    # Actual execution
    start = time.time()

    for epoch in range(args.epoch_num):
        for batch_idx in range(train_iter_num_epoch):
            progress = 100.0 * (batch_idx+1) / train_iter_num_epoch
            sys.stdout.write("\r%.2f%% Epoch %d" % (progress, epoch))
            sys.stdout.flush()

            sess.run(train_step, feed_dict=feed_dict(True, batch_idx % train_iter_num_epoch, BS))

            if batch_idx == train_iter_num_epoch - 1:
                end = time.time()
                epoch_loss = 0
                for i in range(train_iter_num_epoch):
                    loss_v = sess.run(loss, feed_dict=feed_dict(True, i, BS))
                    epoch_loss += loss_v

                epoch_loss /= train_iter_num_epoch
                train_loss = sess.run(loss_summary, feed_dict={average_loss: epoch_loss})
                train_writer.add_summary(train_loss, epoch * train_iter_num_epoch + 1)

                print("Epoch #%-5d | Train Loss: %-4.3f | PureTrainTime: %-3.3fs" %
                      (epoch, epoch_loss, end - start))

                epoch_loss = 0
                for i in range(test_iter_num_epoch):
                    loss_v = sess.run(loss, feed_dict=feed_dict(False, i, BS))
                    epoch_loss += loss_v

                epoch_loss /= test_iter_num_epoch

                test_loss = sess.run(loss_summary, feed_dict={average_loss: epoch_loss})
                test_writer.add_summary(test_loss, epoch * train_iter_num_epoch + 1)

                start = time.time()
                print("Epoch #%-5d | Batch: %d | Test Loss: %-4.3f | CalLossTime: %-3.3fs" %
                      (epoch, batch_idx, epoch_loss, end - start))
    # saver = saver.save(sess, "data/model.ckpt")
    with open(args.out_file, 'w') as o:
        for i in range(test_iter_num_epoch):
            data = feed_dict(False, i, 1)
            q = sess.run(query_y, feed_dict=data)
            d = sess.run(doc_y, feed_dict=data)
            sim = 1.0 - spatial.distance.cosine(q.reshape(L2_N), d.reshape(L2_N))
            o.write('{0}\n'.format(sim))

    np.savetxt("weight1_08.txt", weight1.eval())
    np.savetxt("bias1_08.txt", bias1.eval())
    np.savetxt("weight2_08.txt", weight2.eval())
    np.savetxt("bias2_08.txt", bias2.eval())

    pickle.dump(weight1.eval(), open('weight1_08.pickle', 'wb', True))
    pickle.dump(bias1.eval(), open('bias1_08.pickle', 'wb', True))
    pickle.dump(weight2.eval(), open('weight2_08.pickle', 'wb', True))
    pickle.dump(bias2.eval(), open('bias2_08.pickle', 'wb', True))
