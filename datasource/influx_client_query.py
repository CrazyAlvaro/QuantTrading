import influxdb_client
import pandas as pd

# Read data from csv
target = "sh000001" 

bucket ="start_bucket"
org = "AutoTrading"
token = "NLMvllFxtVEEpAp2Gxv3aCM8GkTXCdvRv2Gd0zxyAa6hNCZDlDY5nkr9jZZxZQhVN2Hg7EGgBIJCcFSZniTNDw=="

url="http://localhost:8086"


with influxdb_client.InfluxDBClient(url=url, token=token, org=org) as client:
    query_api = client.query_api()

    query = 'from(bucket:"{0}")\
        |> range(start: -30d)\
        |> filter(fn:(r) => r._measurement == "{1}")'.format(bucket, target)
    
    result = query_api.query(org=org, query=query)

    results = []
    for table in result:
        for record in table.records:
            results.append((record.get_field(), record.get_value()))

    print("original object:")
    print(result)

    print("\nprocessed results:")
    print(results)
