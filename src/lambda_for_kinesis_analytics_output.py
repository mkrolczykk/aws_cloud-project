import boto3
import os
import base64
import json

SNS_TOPIC_ARN = os.environ['SNSTopic']
ITEMS_TABLE_NAME = os.environ['DynamoDBTop10ItemsResultTableName']
CATEGORIES_TABLE_NAME = os.environ['DynamoDBTop10CategoriesResultTableName']

def handler(event, context):
    sns_client = boto3.client('sns')
    VIEWS_LIMIT = 1000
    items_summed_views = 0
    output_result = []
    success_operations = 0
    failed_operations = 0

    for row in event["records"]:
        try:
            record = json.loads(base64.b64decode(row['data']))
            if 'ITEM_ID' in record:
                views = record['TOTAL_VIEWS']
                items_summed_views += views

                output_result.append(record)
            elif 'CATEGORY' in record:
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

    print("Result: {result}".format(result=output_result))
    print("Lambda summary: \nDelivered records: {0}\nFailed records: {1}".format(success_operations, failed_operations))
    return {'data': output_result}
