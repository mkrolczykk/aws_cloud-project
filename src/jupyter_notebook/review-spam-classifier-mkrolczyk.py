#!/usr/bin/env python
# coding: utf-8

# In[200]:


from sagemaker import get_execution_role

bucket_name = 'mkrolczyk-project-resources'

role = get_execution_role()
bucket_key_prefix = 'sagemaker'
vocabulary_length = 9013


# In[201]:


get_ipython().system('mkdir -p dataset')


# In[202]:


import pandas as pd
import numpy as np
from spam_classifier_utilities import one_hot_encode
from spam_classifier_utilities import vectorize_sequences
import boto3

s3 = boto3.resource('s3')
s3_key = 'review_texts.tsv' # s3 file key
local_file_name = 'dataset/work_review_texts.tsv'

try:
    s3.Bucket(bucket_name).download_file(s3_key, local_file_name)
except botocore.exceptions.ClientError as e:
    if e.response['Error']['Code'] == "404":
        print("The object does not exist.")
    else:
        raise

df = pd.read_csv(local_file_name, sep='\t', header=None)
df[df.columns[0]] = df[df.columns[0]].map({'ham': 0, 'spam': 1})

targets = df[df.columns[0]].values
messages = df[df.columns[1]].values

# one hot encoding for each text
one_hot_data = one_hot_encode(messages, vocabulary_length)
encoded_messages = vectorize_sequences(one_hot_data, vocabulary_length)

df2 = pd.DataFrame(encoded_messages)
df2.insert(0, 'spam', targets)

# Split into training and validation sets (80%/20% split)
split_index = int(np.ceil(df.shape[0] * 0.8))
train_set = df2[:split_index]
val_set = df2[split_index:]

train_set.to_csv('dataset/text_train_set.csv', header=False, index=False)
val_set.to_csv('dataset/text_val_set.csv', header=False, index=False)


# In[203]:


target_bucket = s3.Bucket(bucket_name)

with open('dataset/text_train_set.csv', 'rb') as data:
    target_bucket.upload_fileobj(data, '{0}/train_data/train_set.csv'.format(bucket_key_prefix))
    
with open('dataset/text_val_set.csv', 'rb') as data:
    target_bucket.upload_fileobj(data, '{0}/validation_data/val_set.csv'.format(bucket_key_prefix))


# In[204]:


import boto3

container = sagemaker.image_uris.retrieve('linear-learner', boto3.Session().region_name)


# In[86]:


import sagemaker

output_path = 's3://{0}/{1}/output'.format(bucket_name, bucket_key_prefix)

linear = sagemaker.estimator.Estimator(
    container,
    role, 
    instance_count=1, 
    instance_type='ml.c5.2xlarge',
    output_path=output_path,
    base_job_name='reviews-spam-classifier'
)

linear.set_hyperparameters(
    feature_dim=vocabulary_length,
    predictor_type='binary_classifier',
    mini_batch_size=100
)

train_config = sagemaker.inputs.TrainingInput(
    s3_data='s3://{0}/{1}/train_data/{2}'.format(bucket_name, bucket_key_prefix, 'train_set.csv'), 
    content_type='text/csv'
)

test_config = sagemaker.inputs.TrainingInput(
    s3_data='s3://{0}/{1}/validation_data/{2}'.format(bucket_name, bucket_key_prefix, 'val_set.csv'), 
    content_type='text/csv'
)

linear.fit({'train': train_config, 'test': test_config })


# In[130]:


from sagemaker.serializers import CSVSerializer
from sagemaker.deserializers import JSONDeserializer

pred = linear.deploy(
    initial_instance_count=1,
    instance_type='ml.m5.large',
    serializer=CSVSerializer(),
    deserializer=JSONDeserializer()
)


# In[207]:


# for testing
import json

sagemaker_client = boto3.client('runtime.sagemaker')

test_messages = ["FreeMsg: Txt: CALL to No: 86888 & claim your reward of 3 hours talk time to use from your phone now! ubscribe6GBP/ mnth inc 3hrs 16 stop?txtStop",
                "As per your request 'Melle Melle (Oru Minnaminunginte Nurungu Vettam)' has been set as your callertune for all Callers.",
                 "WINNER!! As a valued network customer you have been selected to receivea £900 prize reward! To claim call 09061701461. Claim code KL341. Valid 12 hours only.",
                ]

one_hot_test_messages = one_hot_encode(test_messages, vocabulary_length)
encoded_test_messages = vectorize_sequences(one_hot_test_messages, vocabulary_length)

np.savetxt("foo.csv", encoded_test_messages, delimiter=",", encoding='utf-8')

response = sagemaker_client.invoke_endpoint(
    EndpointName='<endpoint_name>',
    ContentType='text/csv',
    Body=open("foo.csv", 'rb')
)

result = json.loads(response['Body'].read().decode())

print(result)


# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:




