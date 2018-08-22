import tensorflow as tf
import numpy as np
import os
import time
import datetime
from lstm_model import *
import data_helper
import lstm_config

class Config(object):

    hidden_neural_size=lstm_config.args.hidden_neural_size
    vocabulary_size=lstm_config.args.vocabulary_size
    embed_dim=lstm_config.args.emdedding_dim
    hidden_layer_num=lstm_config.args.hidden_layer_num
    class_num=lstm_config.args.class_num
    keep_prob=lstm_config.args.keep_prob
    lr = lstm_config.args.lr
    lr_decay = lstm_config.args.lr_decay
    batch_size=lstm_config.args.batch_size
    num_step = lstm_config.args.max_len
    max_grad_norm=lstm_config.args.max_grad_norm
    num_epoch = lstm_config.args.num_epoch
    max_decay_epoch = lstm_config.args.max_decay_epoch
    valid_num=lstm_config.args.valid_num
    out_dir=lstm_config.args.out_dir
    checkpoint_every = lstm_config.args.check_point_every


def evaluate(model,session,data,global_steps=None,summary_writer=None):


    correct_num=0
    total_num=len(data[0])
    #print("total_num %i"%total_num)
    for step, (x,y,mask_x) in enumerate(data_helper.batch_iter(data,batch_size=lstm_config.args.batch_size)):

         fetches = model.correct_num
         #fetches = model.correct_item, model.target, model.prediction
         feed_dict={}
         feed_dict[model.input_data]=x
         feed_dict[model.target]=y
         feed_dict[model.mask_x]=mask_x
         model.assign_new_batch_size(session,len(x))
         state = session.run(model._initial_state)
         for i , (c,h) in enumerate(model._initial_state):
            feed_dict[c]=state[i].c
            feed_dict[h]=state[i].h
         count=session.run(fetches,feed_dict)
         correct_num+=count
         #correct, target, prediction  = session.run(fetches,feed_dict)
         #print("Correct_num: %i, batch_size: %i"%(correct_num, len(x)))
         #print("correct,target,prediciton")
         #print(correct)
         #print(target)
         #print(prediction)


    accuracy=float(correct_num)/total_num
    print("Accuracy: %d"%(accuracy*100))
    dev_summary = tf.summary.scalar('dev_accuracy',accuracy)
    dev_summary = session.run(dev_summary)
    if summary_writer:
        summary_writer.add_summary(dev_summary,global_steps)
        summary_writer.flush()
    return accuracy

def run_epoch(model,session,data,global_steps,valid_model,valid_data,train_summary_writer=None,valid_summary_writer=None):
    for step, (x,y,mask_x) in enumerate(data_helper.batch_iter(data,batch_size=lstm_config.args.batch_size)):

        feed_dict={}
        feed_dict[model.input_data]=x
        feed_dict[model.target]=y
        feed_dict[model.mask_x]=mask_x
        model.assign_new_batch_size(session,len(x))
        fetches = [model.cost,model.accuracy,model.train_op,model.summary]
        #fetches = [model.cost,model.accuracy,model.train_op]
        state = session.run(model._initial_state)
        for i , (c,h) in enumerate(model._initial_state):
            feed_dict[c]=state[i].c
            feed_dict[h]=state[i].h
        cost,accuracy,_, summary = session.run(fetches,feed_dict)
        train_summary_writer.add_summary(summary,global_steps)
        train_summary_writer.flush()
        valid_accuracy=evaluate(valid_model,session,valid_data,global_steps,valid_summary_writer)
        if(global_steps%100==0):
            print("the %i step, train cost is: %f and the train accuracy is %f and the valid accuracy is %f"%(global_steps,cost,accuracy,valid_accuracy))
        global_steps+=1

    return global_steps

def train_step():

    print("loading the dataset...")
    config = Config()
    eval_config=Config()
    eval_config.keep_prob=1.0

    train_data,valid_data,test_data = data_helper.load_data(lstm_config.args.max_len,batch_size=config.batch_size)

    print("begin training")

    # gpu_config=tf.ConfigProto()
    # gpu_config.gpu_options.allow_growth=True
    with tf.Graph().as_default(), tf.Session() as session:
        initializer = tf.random_uniform_initializer(-1*lstm_config.args.init_scale,1*lstm_config.args.init_scale)
        with tf.variable_scope("model",reuse=None,initializer=initializer):
            model = RNN_Model_Regression(config=config,is_training=True)

        with tf.variable_scope("model",reuse=True,initializer=initializer):
            valid_model = RNN_Model_Regression(config=eval_config,is_training=False)
            test_model = RNN_Model_Regression(config=eval_config,is_training=False)

        #add summary
        #train_summary_op = tf.merge_summary([model.loss_summary,model.accuracy])
        train_summary_dir = os.path.join(config.out_dir,"summaries","train")
        train_summary_writer =  tf.summary.FileWriter(train_summary_dir,session.graph)

        #dev_summary_op = tf.merge_summary([valid_model.loss_summary,valid_model.accuracy])
        dev_summary_dir = os.path.join(eval_config.out_dir,"summaries","dev")
        dev_summary_writer =  tf.summary.FileWriter(dev_summary_dir,session.graph)

        #add checkpoint
        checkpoint_dir = os.path.abspath(os.path.join(config.out_dir, "checkpoints"))
        checkpoint_prefix = os.path.join(checkpoint_dir, "model")
        if not os.path.exists(checkpoint_dir):
            os.makedirs(checkpoint_dir)
        saver = tf.train.Saver(tf.all_variables())


        tf.initialize_all_variables().run()
        global_steps=1
        begin_time=int(time.time())

        for i in range(config.num_epoch):
            print("the %d epoch training..."%(i+1))
            lr_decay = config.lr_decay ** max(i-config.max_decay_epoch,0.0)
            model.assign_new_lr(session,config.lr*lr_decay)
            global_steps=run_epoch(model,session,train_data,global_steps,valid_model,valid_data,train_summary_writer,dev_summary_writer)

            if i% config.checkpoint_every==0:
                path = saver.save(session,checkpoint_prefix,global_steps)
                print("Saved model chechpoint to{}\n".format(path))

        print("the train is finished")
        end_time=int(time.time())
        print("training takes %d seconds already\n"%(end_time-begin_time))
        test_accuracy=evaluate(test_model,session,test_data)
        print("the test data accuracy is %f"%test_accuracy)
        train_summary_writer.close()
        dev_summary_writer.close()
        print("program end!")



def main(_):
    train_step()


if __name__ == "__main__":
    tf.app.run()





