import boto3
import os
import base64
import json


def handler(event, context):
    dynamodb_client = boto3.resource('dynamodb').Table(os.environ['DynamoDB_table'])
    firehouse_client = boto3.client('firehose')
    curRecordSequenceNumber = ""
    records = event["Records"]
    decoded_record = None
    output_data = []

    for record in records:
        try:
            decoded_record = json.loads(base64.b64decode(record['kinesis']['data']))
            suspicious = dynamodb_client.get_item(  # return empty dict if no ip found in dynamodb suspicious ids table
                Key={'ip': decoded_record['user_ip']}
            )
            if 'Item' not in suspicious:
                line = {
                    'Data': json.dumps(decoded_record) + '\n'
                }
                output_data.append(line)
            curRecordSequenceNumber = record["kinesis"]["sequenceNumber"]
        except Exception as e:
            return {"batchItemFailures": [{"itemIdentifier": curRecordSequenceNumber}]}

    # output
    batch_size = len(output_data)
    if batch_size > 0 and 'review_title' in decoded_record:
        firehouse_reviews_stream = os.environ['FirehouseReviewsDeliveryStreamName']
        firehouse_client.put_record_batch(DeliveryStreamName=firehouse_reviews_stream, Records=output_data)
    elif batch_size > 0:
        firehouse_items_stream = os.environ['FirehouseItemsDeliveryStreamName']
        firehouse_client.put_record_batch(DeliveryStreamName=firehouse_items_stream, Records=output_data)
    else:
        return None

    return {"batchItemFailures": []}
