from pathlib import Path
import pandas as pd
import requests
from prefect import flow, task, Flow
from prefect_gcp.cloud_storage import GcsBucket
from datetime import date, datetime
import os

class ETL:
    def __init__(self, cidade: str, anos: list[int], bucket_name: str):
        self.cidade = cidade
        self.anos = anos
        self.bucket_name = bucket_name
        self.key_weather = os.environ.get('WEATHERBIT_API')
        self.data_atual = datetime.now()

    @task(retries=3, log_prints=True)
    def fetch(self, url: str) -> pd.DataFrame:
        '''Read taxi data from web into pandas DF'''
        response = requests.get(url)
        data = response.json()
        df = pd.DataFrame(data["data"])
        return df

    @task(retries=3, log_prints=True)
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        '''Read taxi data from web into pandas DF'''
        df['datetime'] = pd.to_datetime(df['datetime'])
        df['year'] = df['datetime'].dt.year
        df['month'] = df['datetime'].dt.month
        return df

    @task()
    def write_local(self, df: pd.DataFrame, ano) -> str:
        '''Write DataFrame out locally as parquet file'''
        nome_arquivo = f'{ano}'
        folder_path = 'data'
        dir_path = os.path.join(folder_path, 'weatherbit')
        path = os.path.join(dir_path, nome_arquivo + '.parquet')

        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        df.to_parquet(path, compression='gzip')
        return path

    @task(log_prints=True)
    def write_gcs(self, path: str) -> None:
        '''Upload local parquet file to Google Cloud Storage'''
        path = path.replace('\\', '/')
        gcp_block = GcsBucket.load(self.bucket_name)
        gcp_block.upload_from_path(from_path=f'{path}', to_path=path)
        return None

    @flow(log_prints=True)
    def etl_web_to_gcs(self, ano: int) -> pd.DataFrame:
        ''' Main ETL funtion '''
        if ano == self.data_atual.year:
            url = f"https://api.weatherbit.io/v2.0/history/daily?city={self.cidade},BR&start_date={ano}-01-01&end_date={self.data_atual.strftime('%y-%m-%d')}&key={self.key_weather}"
        else:
            url = f"https://api.weatherbit.io/v2.0/history/daily?city={self.cidade},BR&start_date={ano}-01-01&end_date={ano}-12-31&key={self.key_weather}"
        
        df = self.fetch(url)
        df_clean = self.transform(df)
        path = self.write_local(df_clean, ano)
        self.write_gcs(path)
        return df

    def run(self):
        ''' Run ETL process for each year'''
        with Flow("ETL") as flow:
            for ano in self.anos:
                self.etl_web_to_gcs(ano)
                flow.run()


def etl_parent_flow(cidade: str = "Rio Grande", anos : list[int] = [2019,2020,2021,2022,2023]):
    etl_instance = ETL(cidade, anos, bucket_name='wecode')
    etl_instance.run()

if __name__ == '__main__':
    etl_parent_flow("Rio grande", [2019,2020,2021,2022,2023])