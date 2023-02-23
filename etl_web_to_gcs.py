import pandas as pd
import requests
from prefect import flow, task
from prefect_gcp.cloud_storage import GcsBucket
from datetime import datetime
import os

@task(retries=3,log_prints=True)
def fetch(url: str) -> pd.DataFrame:
    '''Read taxi data from web into pandas DF'''
    response = requests.get(url)
    data = response.json()
    df = pd.DataFrame(data["data"])
    return df

@task(retries=3,log_prints=True)
def transform(df: pd.DataFrame) -> pd.DataFrame:
    '''Read taxi data from web into pandas DF'''
    df['datetime'] = pd.to_datetime(df['datetime'])
    df['year'] = df['datetime'].dt.year
    df['month'] = df['datetime'].dt.month
    return df

@task()
def write_local(df: pd.DataFrame, ano) -> str:
    '''Write DataFrame out locally as parquet file'''
    nome_arquivo = f'{ano}'
    folder_path = 'data'
    dir_path = os.path.join(folder_path, 'weatherbit')
    path = os.path.join(dir_path, nome_arquivo + '.parquet')


    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    df.to_parquet(path, compression='gzip')
    return path
    #df.to_parquet(path, engine='pyarrow', partition_cols=['year', 'month'])

@task(log_prints=True)
def write_gcs(path: str) -> None:
    '''Upload local parquet file to Google Cloud Storage'''
    path = path.replace('\\', '/')
    gcp_block = GcsBucket.load("wecode")
    gcp_block.upload_from_path(from_path=f'{path}',to_path=path)
    return None


@flow()
def etl_web_to_gcs(cidade: str, ano: int) -> pd.DataFrame:
    ''' Main ETL funtion '''
    key_weather = os.environ.get('WEATHERBIT_API')
    data_atual = datetime.now()

    if ano == data_atual.year:
        url = f"https://api.weatherbit.io/v2.0/history/daily?city={cidade}&start_date={ano}-01-01&end_date={data_atual.strftime('%y-%m-%d')}&key={key_weather}"
    else:
        url = f"https://api.weatherbit.io/v2.0/history/daily?city={cidade}&start_date={ano}-01-01&end_date={ano}-12-31&key={key_weather}"
    
    df = fetch(url)
    df_clean = transform(df)
    path = write_local(df_clean, ano)
    write_gcs(path)
    return df

@flow(log_prints=True)
def etl_parent_flow(cidade: str = "Rio Grande", anos : list[int] = [2019,2020,2021,2022,2023]):
    for ano in anos:
        etl_web_to_gcs(cidade,ano)


if __name__ == '__main__':
    etl_parent_flow("Rio grande", [2019,2020,2021,2022,2023])