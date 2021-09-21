#!/usr/bin/env python3
import boto3
import os
import base64
import json

REGION_NAME = 'us-east-1'

def handler(event, context):
    dynamodb_client = boto3.resource('dynamodb')
    firehouse_client = boto3.client('firehose', region_name=REGION_NAME)
    curRecordSequenceNumber = ""
    records = event.get("Records")
    decoded_record = None
    output_data = []

    for record in records:
        try:
            decoded_record = json.loads(base64.b64decode(record['kinesis']['data']))
            suspicious = dynamodb_client.get_item(  # return empty dict if no ip found in dynamodb suspicious ids table
                TableName=os.environ['DynamoDB_table'],
                Key={'ip': {'S': decoded_record['user_ip']}}
            )
            if not suspicious:
                output_data \
                    .append(
                        {
                            "Data": json.dumps(decoded_record)
                        }
                    )
            curRecordSequenceNumber = record["kinesis"]["sequenceNumber"]
        except Exception as e:
            return {"batchItemFailures": [{"itemIdentifier": curRecordSequenceNumber}]}

    # output
    if ('review_title' or 'review_text' or 'review_stars' in decoded_record) and output_data:
        firehouse_reviews_stream = os.environ['FirehouseReviewsDeliveryStreamName']
        firehouse_client.put_record_batch(DeliveryStreamName=firehouse_reviews_stream, Records=output_data)
    elif output_data:
        firehouse_items_stream = os.environ['FirehouseItemsDeliveryStreamName']
        firehouse_client.put_record_batch(DeliveryStreamName=firehouse_items_stream, Records=output_data)

    return {"batchItemFailures": []}





