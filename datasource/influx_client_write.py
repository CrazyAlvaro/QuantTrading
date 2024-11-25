# https://docs.influxdata.com/influxdb/v2/api-guide/client-libraries/python/
import influxdb_client
import pandas as pd
from influxdb_client.client.write_api import SYNCHRONOUS, ASYNCHRONOUS

# Read data from csv
target = "sh000001" 
file_path = target + ".csv"
data_frame = pd.read_csv(file_path, header=0)
print(data_frame.head())
# data_frame.set_index()



bucket ="start_bucket"
org = "AutoTrading"
token = "NLMvllFxtVEEpAp2Gxv3aCM8GkTXCdvRv2Gd0zxyAa6hNCZDlDY5nkr9jZZxZQhVN2Hg7EGgBIJCcFSZniTNDw=="

url="http://localhost:8086"


with influxdb_client.InfluxDBClient(url=url, token=token, org=org) as client:
    write_api = client.write_api(write_options = SYNCHRONOUS)

    # Write to influxdb
    write_api.write(
        bucket=bucket,
        org=org,
        token=token,
        record=data_frame,
        data_frame_measurement_name=target,
        data_frame_timestamp_column="datetime",
        data_frame_timestamp_timezone="Etc/GMT+8"
    )