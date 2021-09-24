#!/usr/bin/env python3
import boto3
from botocore.waiter import WaiterModel, create_waiter_with_client
import os

REGION_NAME = 'us-east-1'

def handler(event, context):
    glue_crawler = os.environ['GlueCrawler']
    glue_database = os.environ['GlueDB']
    query_id = os.environ['AthenaItemsAverageRatingsQueryId']
    dynamodb_table = os.environ['DynamoDBAvgRatingsTableName']
    s3_bucket = os.environ['S3Bucket']

    update_glue_data_catalog(glue_crawler)
    query_result = athena_query(query_id=query_id, glue_db=glue_database, s3_bucket=s3_bucket)
    write_to_dynamodb(dynamodb_table, query_result)

def update_glue_data_catalog(glue_crawler: str):
    glue_client = boto3.client('glue')
    waiter_config = {
        'version': 2,
        'waiters': {
            'CrawlerStatusWaiter': {
                'delay': 30,
                'operation': 'GetCrawler',
                'maxAttempts': 10,
                'acceptors': [
                    {
                        'expected': True,
                        'matcher': 'path',
                        'state': 'success',
                        'argument': "Crawler.LastCrawl.Status == 'SUCCEEDED'"
                    },
                    {
                        'expected': True,
                        'matcher': 'path',
                        'state': 'failure',
                        'argument': "Crawler.LastCrawl.Status == 'CANCELLED'"
                    },
                    {
                        'expected': True,
                        'matcher': 'path',
                        'state': 'failure',
                        'argument': "Crawler.LastCrawl.Status == 'FAILED'"
                    }
                ]
            }
        }
    }

    try:
        glue_client.start_crawler(glue_crawler)
    except Exception as e:
        print("Crawler '{0}' already exists".format(glue_crawler))

    glue_waiter = create_waiter_with_client(
        waiter_name='CrawlerStatusWaiter',
        waiter_model=WaiterModel(waiter_config),
        client=glue_client
    )
    glue_waiter.wait(Name=glue_crawler)

def athena_query(query_id: str, glue_db: str, s3_bucket: str):
    athena_client = boto3.client('athena')
    S3_KEY = 'athena_queries'
    S3_URI = 's3://{bucket}/{key}'.format(bucket=s3_bucket, key=S3_KEY)
    query = athena_client.batch_get_named_query(NamedQueryIds=[query_id])['NamedQueries'][0]['QueryString']
    waiter_config = {
        'version': 2,
        'waiters': {
            'AthenaQueryStatusWaiter': {
                'delay': 30,
                'operation': 'GetQueryExecution',
                'maxAttempts': 10,
                'acceptors': [
                    {
                        'expected': True,
                        'matcher': 'path',
                        'state': 'success',
                        'argument': "QueryExecution.Status.State == 'SUCCEEDED'"
                    },
                    {
                        'expected': True,
                        'matcher': 'path',
                        'state': 'failure',
                        'argument': "QueryExecution.Status.State == 'QUEUED'"
                    },
                    {
                        'expected': True,
                        'matcher': 'path',
                        'state': 'failure',
                        'argument': "QueryExecution.Status.State == 'CANCELLED'"
                    },
                    {
                        'expected': True,
                        'matcher': 'path',
                        'state': 'failure',
                        'argument': "QueryExecution.Status.State == 'FAILED'"
                    }
                ]
            }
        }
    }

    scheduled_query = athena_client.start_query_execution(
        QueryString=query,
        QueryExecutionContext={'Database': glue_db},
        ResultConfiguration={'OutputLocation': S3_URI}
    )
    scheduled_query_id = scheduled_query['QueryExecutionId']

    waiter = create_waiter_with_client(
        waiter_name='AthenaQueryStatusWaiter',
        waiter_model=WaiterModel(waiter_config),
        client=athena_client
    )

    waiter.wait(QueryExecutionId=scheduled_query_id)

    query_result = athena_client.athena.get_query_results(QueryExecutionId=scheduled_query_id)

    return query_result

def write_to_dynamodb(table_name: str, data):
    dynamodb_client = boto3.resource('dynamodb')
    target_table = dynamodb_client.Table(table_name)

    try:
        for record in data['ResultSet']['Rows']:
            item = record['Data'][0]['VarCharValue']
            item_rating = record['Data'][1]['VarCharValue']

            target_table.put_item(Item={'item_id': item, 'rating_average': item_rating})
    except Exception as e:
        print("DynamoDB write operation failed - {log_message}".format(log_message=str(e)))

