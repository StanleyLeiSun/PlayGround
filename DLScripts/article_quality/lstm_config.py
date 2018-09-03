import os

import argparse
parser = argparse.ArgumentParser("lstm_training")
parser.add_argument('--iscloud', help="is running on cloud", default=False, action="store_true")
parser.add_argument('-n', dest = "name", help="package's name", default='', type=str)

parser.add_argument('--batch_size',     default=640,    help='the batch_size of the training procedure', type=int)
parser.add_argument('--lr',             default=0.1,    help='the learning rate', type=float)
parser.add_argument('--lr_decay',       default=0.5,    help='the learning rate decay', type=float)
parser.add_argument('--vocabulary_size',default=20000,   help='vocabulary_size', type=int)
parser.add_argument('--emdedding_dim',  default=32,     help='embedding dim', type=int)
parser.add_argument('--max_len',        default=40,     help='max_len of training sentence', type=int)
parser.add_argument('--valid_num',      default=100,    help='epoch num of validation', type=int)
parser.add_argument('--checkpoint_num', default=1000,   help='epoch num of checkpoint', type=int)
parser.add_argument('--init_scale',     default=0.1,    help='init scale', type=float)
parser.add_argument('--class_num',      default=6,      help='class num', type=int)
parser.add_argument('--keep_prob',      default=0.9,    help='dropout rate', type=float)
parser.add_argument('--num_epoch',      default=60,     help='num epoch', type=int)
parser.add_argument('--max_decay_epoch',default=30,     help='num epoch', type=int)
parser.add_argument('--max_grad_norm',  default=5,      help='max_grad_norm', type=int)
parser.add_argument('--hidden_layer_num',default=1,     help='LSTM hidden layer num', type=int)
parser.add_argument('--check_point_every',default=10,   help='checkpoint every num epoch ', type=int)
parser.add_argument('--hidden_neural_size',default=32,  help='LSTM hidden neural size', type=int)


#parser.add_argument('--emdedding_dim',128,'embedding dim')
#parser.add_argument('--hidden_neural_size',128,'LSTM hidden neural size')
#parser.add_argument('--hidden_layer_num',1,'LSTM hidden layer num')

args = parser.parse_args()

data_root = '/home/stansun/data/'
training_device = "/cpu:0"

if args.iscloud:
    data_root = '/fds/data/article_quality/'
    training_device = "/device:GPU:0"
    args.out_dir = os.path.abspath(os.path.join("/fds/output/","runs", args.name))   
else:
    data_root = '/home/stansun/data/'
    training_device = "/cpu:0"
    args.out_dir = os.path.abspath(os.path.join(os.path.curdir,"runs", args.name))


if __name__ == "__main__":
    print(args.name)
    print(os.path.abspath(os.path.join(os.path.curdir,"runs", args.name)))
    print(args.iscloud)
