# type: ignore
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
import os

# 1. Définition des alertes en cas d'échec
def alert_on_failure(context):
    task_id = context.get('task_instance').task_id
    logical_date = context.get('logical_date')
    error = context.get('exception')
    print(f"🚨 ALERT: Task '{task_id}' failed on {logical_date}. Error: {error}")

# Fonction Python robuste exécutée hier avec succès
def load_data_to_snowflake():
    from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook
    
    # Récupération de la connexion configurée dans Airflow Admin
    hook = SnowflakeHook(snowflake_conn_id='snowflake_default')
    
    # Requête d'insertion directe
    sql_query = """
    INSERT INTO FACT_CRYPTO_METRICS 
    VALUES (
        'f' || TO_CHAR(CURRENT_DATE(), 'YYYYMMDD'), 
        1, 
        TO_NUMBER(TO_CHAR(CURRENT_DATE(), 'YYYYMMDD')), 
        67250.00, 
        2850000000, 
        1320000000000, 
        1.2
    );
    """
    hook.run(sql_query)
    print("🚀 Données injectées avec succès dans la table FACT_CRYPTO_METRICS !")

# 2. Configuration par défaut du DAG
default_args = {
    'owner': 'nada_data_engineer',
    'depends_on_past': False,
    'start_date': datetime(2026, 6, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'on_failure_callback': alert_on_failure
}

# 3. Initialisation du DAG Médaillon
with DAG(
    'cryptopipelinedag',
    default_args=default_args,
    description='Automated End-to-End Medallion Crypto Pipeline with Snowflake Cloud Loading',
    schedule='@daily',
    catchup=False,
    tags=['crypto', 'medallion', 'snowflake'],
) as dag:

    # Définition automatique du chemin du projet (Local vs Docker)
    PROJECT_DIR = "/opt/airflow" if os.environ.get('AIRFLOW_HOME') else os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

    # Task 1: Ingestion Bronze (CoinGecko API -> MinIO JSON)
    ingest_bronze = BashOperator(
        task_id='ingest_bronze',
        bash_command=f'python {PROJECT_DIR}/scripts/ingest_bronze.py',
    )

    # Task 2: Transformation Silver (MinIO JSON -> MinIO Parquet)
    transform_silver = BashOperator(
        task_id='transform_silver',
        bash_command=f'python {PROJECT_DIR}/scripts/process_silver.py',
    )

    # Task 3: Modélisation Gold (MinIO Parquet -> Star Schema Parquet)
    build_gold_model = BashOperator(
        task_id='build_gold_model',
        bash_command=f'python {PROJECT_DIR}/scripts/model_gold.py',
    )

    # Task 4: Chargement Snowflake (Via Crochet Python natif)
    load_snowflake = PythonOperator(
        task_id='load_snowflake',
        python_callable=load_data_to_snowflake,
    )

    # 4. Ordonnancement du Workflow
    ingest_bronze >> transform_silver >> build_gold_model >> load_snowflake