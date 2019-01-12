import fasttext
import lstm_config
# Skipgram model
#model = fasttext.skipgram('tencent_fasttext.csv', 'model')
#print ("skip gram ===========>")
#print (model.words) # list of words in dictionary

# CBOW model
#model = fasttext.cbow('tencent_fasttext.csv', 'model')
#print ("cbow ===========>")
#print( model.words )# list of words in dictionary

classifier = fasttext.supervised(lstm_config.data_root+'tencent_fasttext.csv', 'tencent_quality_model',lr=0.01,epoch=3,dim=128, ws = 8, min_count = 5)

result = classifier.test(lstm_config.data_root+'tencent_fasttext_test.csv')
print ('P@1:', result.precision)
print ('R@1:', result.recall)
print ('Number of examples:', result.nexamples)

#texts = ['example very long text 1', 'example very longtext 2']
#labels = classifier.predict(texts)
#print (labels)

# Or with the probability
#labels = classifier.predict_proba(texts)
#print labels

