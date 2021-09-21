#!/usr/bin/env python3
import boto3
import sys
from pyspark.sql import SparkSession
from pyspark.sql import DataFrame
from pyspark.sql.functions import col, avg

def main(s3_uri: str, write_table_name: str):
    spark = SparkSession \
    .builder \
    .appName("Identify suspicious IPs, based on item’s views") \
    .getOrCreate()

    data_df = get_data(spark, s3_uri)
    result = identify_ids(data_df)

    write_to_db(result, write_table_name)

def get_data(spark: SparkSession, uri: str):
    return spark.read.option("header", "true").csv(uri)

def identify_ids(df: DataFrame):
    return df \
        .groupBy("user_ip", "ts") \
        .count() \
        .groupBy("user_ip") \
        .agg(avg("count").alias("ip_average")) \
        .filter(col("ip_average") > 5) \
        .select("user_ip")


def write_to_db(df: DataFrame, table_name: str):
    dynamodb_table = boto3.resource('dynamodb').Table(table_name)
    for each_row in df.collect():
        dynamodb_table.put_item(
            Item={'ip': each_row['user_ip']}
        )


if __name__ == "__main__":
    main(s3_uri=sys.argv[3], write_table_name=sys.argv[4])
