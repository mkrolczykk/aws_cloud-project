import boto3
import os

def handler(event, context):
    REGION_NAME = 'us-east-1'
    DYNAMO_DB_TABLE_NAME = os.environ['DynamoDBSuspiciousIdsTable']

    S3_RESOURCES_BUCKET = os.environ['S3ResourcesBucketName']
    S3_RESOURCES_KEY = 'spark_emr_job/main.py'
    S3_RESOURCES_URI = 's3://{bucket}/{key}'.format(bucket=S3_RESOURCES_BUCKET, key=S3_RESOURCES_KEY)

    S3_DATA_BUCKET = event['Records'][0]['s3']['bucket']['name']
    S3_DATA_KEY = event['Records'][0]['s3']['object']['key']
    S3_DATA_URI = 's3://{bucket}/{key}'.format(bucket=S3_DATA_BUCKET, key=S3_DATA_KEY)

    client = boto3.client('emr', region_name=REGION_NAME)

    return client.run_job_flow(
        Name=os.environ['emrClusterName'],
        ReleaseLabel=os.environ['emrReleaseLabel'],
        Applications=[
            {
                'Name': 'Spark'
            }
        ],
        Instances={
            'Ec2KeyName': os.environ['EC2KeyName'],
            'InstanceCount': int(os.environ['emrMasterInstanceCount']),
            'MasterInstanceType': os.environ['emrInstanceType'],
            'SlaveInstanceType': os.environ['emrInstanceType'],
            'KeepJobFlowAliveWhenNoSteps': True,
            'TerminationProtected': bool(os.environ['emrTerminationProtected']),
            'Ec2SubnetId': os.environ['emrSubnetId']
        },
        VisibleToAllUsers=True,
        JobFlowRole=os.environ['emrEc2Role'],
        ServiceRole=os.environ['emrRole'],
        LogUri=os.environ['logUri'],
        Tags=[
            {
                'Key': 'owner',
                'Value': 'mkrolczyk'
            }
        ],
        BootstrapActions=[
            {
                'Name': 'Maximize Spark Default Config',
                'ScriptBootstrapAction': {'Path': 's3://support.elasticmapreduce/spark/maximize-spark-default-config'}
            },
            {
                'Name': 'Install boto3 before running spark job',
                'ScriptBootstrapAction': {'Path': 's3://' + S3_RESOURCES_BUCKET + '/install_boto3.sh'}
            }
        ],
        Steps=[
            {
                'Name': 'Run Spark job',
                'ActionOnFailure': 'TERMINATE_CLUSTER',
                'HadoopJarStep': {
                    'Jar': 'command-runner.jar',
                    'Args': ['spark-submit', S3_RESOURCES_URI, S3_DATA_URI, DYNAMO_DB_TABLE_NAME]
                }
            }
        ],
    )
