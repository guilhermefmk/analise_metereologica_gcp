# Análise Meteorológica com Google Cloud Platform
Este repositório contém um conjunto de scripts que realizam a extração de dados meteorológicos do Weatherbit usando sua API REST, transformação e carregamento desses dados no Google Cloud Storage usando o Prefect.

Os dados extraídos são armazenados no formato parquet com compressão gzip em um diretório específico do Google Cloud Storage.

## Fluxo de trabalho
O fluxo de trabalho principal é executado pelo arquivo [etl_web_to_gcs.py](https://github.com/guilhermefmk/analise_metereologica_gcp/blob/main/etl_web_to_gcs.py), que realiza a extração, transformação e carregamento dos dados para o Google Cloud Storage.

O fluxo de trabalho é composto por quatro tarefas:

- **`fetch`**: essa tarefa é responsável por recuperar os dados meteorológicos brutos do Weatherbit usando sua API REST e transformá-los em um objeto pandas DataFrame.
- **`transform`**: essa tarefa é responsável por aplicar transformações no objeto DataFrame para prepará-lo para a carga no Google Cloud Storage.
- **`write_local`**: essa tarefa é responsável por escrever o objeto DataFrame em um arquivo parquet com compressão gzip em um diretório local específico.
- **`write_gcs`**: essa tarefa é responsável por carregar o arquivo parquet do diretório local para o Google Cloud Storage.

O fluxo de trabalho é executado para um determinado conjunto de anos e cidade passados como argumentos para a função etl_parent_flow, que chama a função etl_web_to_gcs para cada ano especificado.

## Dependências
Listadas no arquivo [requirements.txt](https://github.com/guilhermefmk/analise_metereologica_gcp/blob/main/requirements.txt).
```sh
pip install -r requirements.txt
```
- prefect-gcp[cloud_storage]==0.2.4
- pandas==1.3.3
- requests==2.26.0
- prefect==1.4.3

## Execução
 Para execução do ETL funcionar corretamente será necessária a configuração prévia dos BLOCKS no prefect para que a autenticação no GCP obtenha êxito, o blocos utilizados são:
 - [CGP Credentials](https://prefecthq.github.io/prefect-gcp/credentials/#prefect_gcp.credentials.GcpCredentials)
 - [GCS Bucket](https://prefecthq.github.io/prefect-gcp/cloud_storage/#prefect_gcp.cloud_storage.GcsBucket)
```sh
prefect orion start
prefect agent start -q 'default'
prefect deployment build etl_web_to_gcs.py:etl_parent_flow --name weatherapi_to_gcs --apply
```
 Após a execução dos comandos o flow criado irá aparecer na aba "deployments" da interface gráfica do Orion. Onde você poderá executar o flow com os parâmetros desejados.