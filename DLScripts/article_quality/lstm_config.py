import tensorflow as tf
import os

isLocal = True

flags =tf.app.flags

data_root = '/fds/data/article_quality/'
training_device = "/device:GPU:0"

flags.DEFINE_integer('batch_size',640,'the batch_size of the training procedure')
flags.DEFINE_float('lr',0.1,'the learning rate')
flags.DEFINE_float('lr_decay',0.6,'the learning rate decay')
flags.DEFINE_integer('vocabulary_size',6000,'vocabulary_size')
#flags.DEFINE_integer('emdedding_dim',128,'embedding dim')
#flags.DEFINE_integer('hidden_neural_size',128,'LSTM hidden neural size')
#flags.DEFINE_integer('hidden_layer_num',1,'LSTM hidden layer num')
flags.DEFINE_integer('emdedding_dim',24,'embedding dim')
flags.DEFINE_integer('hidden_neural_size',24,'LSTM hidden neural size')
flags.DEFINE_integer('hidden_layer_num',3,'LSTM hidden layer num')
flags.DEFINE_string('dataset_path','data/subj0.pkl','dataset path')
flags.DEFINE_integer('max_len',40,'max_len of training sentence')
flags.DEFINE_integer('valid_num',100,'epoch num of validation')
flags.DEFINE_integer('checkpoint_num',1000,'epoch num of checkpoint')
flags.DEFINE_float('init_scale',0.1,'init scale')
flags.DEFINE_integer('class_num',6,'class num')
flags.DEFINE_float('keep_prob',0.5,'dropout rate')
flags.DEFINE_integer('num_epoch',60,'num epoch')
flags.DEFINE_integer('max_decay_epoch',30,'num epoch')
flags.DEFINE_integer('max_grad_norm',5,'max_grad_norm')
flags.DEFINE_integer('check_point_every',10,'checkpoint every num epoch ')


if isLocal:
    data_root = '/home/stansun/data/'
    training_device = "/cpu:0"
    flags.DEFINE_string('out_dir',os.path.abspath(os.path.join(os.path.curdir,"runs")),'output directory')
else:
    flags.DEFINE_string('out_dir',os.path.abspath(os.path.join("/fds/output/","runs")),'output directory')
