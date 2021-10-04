import boto3
import os
import json
import numpy as np

from spam_classifier_utilities import one_hot_encode
from spam_classifier_utilities import vectorize_sequences


def handler(event, context):
    sagemaker_client = boto3.client('runtime.sagemaker')
    firehouse_client = boto3.client('firehose')
    s3_client = boto3.client('s3')
    bucket = event['detail']['requestParameters']['bucketName']
    key = event['detail']['requestParameters']['key']
    vocabulary_length = 9013
    package_size = 20

    resp = s3_client.get_object(Bucket=bucket, Key=key)['Body']
    data = [json.loads(jline) for jline in resp.read().decode('utf-8').splitlines()]

    one_hot_test_messages = one_hot_encode([line['review'] for line in data], vocabulary_length)

    encoded_test_messages = vectorize_sequences(one_hot_test_messages, vocabulary_length)

    chunks = divide_chunks(encoded_test_messages, package_size)

    file_path = '/tmp/' + 'temp.csv'
    result = []
    for package in chunks:
        np.savetxt(file_path, package, delimiter=",", encoding='utf-8')

        response = sagemaker_client.invoke_endpoint(
            EndpointName='reviews-spam-classifier-2021-10-02-09-29-43-512',
            ContentType='text/csv',
            Body=open(file_path, 'rb')
        )

        partial_result = json.loads(response['Body'].read().decode())
        result.extend(line['predicted_label'] for line in partial_result['predictions'])

    filtered_data = [{'Data': json.dumps(remove_key(i, 'review')) + '\n'} for i, j in zip(data, result) if not j]

    # Output
    firehouse_delivery_stream = os.environ['FirehouseNoSpamReviewsDeliveryStreamName']
    firehouse_client.put_record_batch(DeliveryStreamName=firehouse_delivery_stream, Records=filtered_data)


def divide_chunks(json_dict, n):
    for i in range(0, len(json_dict), n):
        yield json_dict[i:i + n]

def remove_key(d, key):
    r = dict(d)
    del r[key]
    return r
