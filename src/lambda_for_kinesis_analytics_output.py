#!/usr/bin/env python3
import boto3
import os
import base64
import json

SNS_TOPIC_ARN = os.environ['SNSHighTrafficTopic']
ITEMS_TABLE_NAME = os.environ['DynamoDBTop10ItemsResultTableName']
CATEGORIES_TABLE_NAME = os.environ['DynamoDBTop10CategoriesResultTableName']

def handler(event, context):
    TOP_ITEMS_TABLE = boto3.resource('dynamodb').Table(ITEMS_TABLE_NAME)
    TOP_CATEGORIES_TABLE = boto3.resource('dynamodb').Table(CATEGORIES_TABLE_NAME)
    sns_client = boto3.client('sns')
    VIEWS_LIMIT = 1000
    items_summed_views = 0
    output_result = []
    success_operations = 0
    failed_operations = 0

    for row in event.get("Records"):
        try:
            record = json.loads(base64.b64decode(row['data']))
            if 'item_id' in record:
                items_summed_views += record['total_views']
                TOP_ITEMS_TABLE.put_item(Item=record)

                output_result.append(record)
            elif 'category' in record:
                TOP_CATEGORIES_TABLE.put_item(Item=record)

                output_result.append(record)

            success_operations += 1
        except Exception as e:
            failed_operations += 1

    if items_summed_views > VIEWS_LIMIT:
        sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject='Views high traffic notification',
            Message='Warning: Number of views exceeds 1000 for top 10 items'
        )

    print("Lambda summary: \nDelivered records: {0}\nFailed records: {1}".format(success_operations, failed_operations))
    return {'data': output_result}
