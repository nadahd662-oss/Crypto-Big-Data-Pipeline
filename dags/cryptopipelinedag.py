# type: ignore
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
import os

# 1. Définition des alertes en cas d'échec
def alert_on_failure(context):
    task_id = context.get('task_instance').task_id
    logical_date = context.get('logical_date')  # Standardisé pour Airflow 3.0
    error = context.get('exception')
    print(f"🚨 ALERT: Task '{task_id}' failed on {logical_date}. Error: {error}")

# 2. Configuration par défaut du DAG (Retries et résilience)
default_args = {
    'owner': 'nada_data_engineer',
    'depends_on_past': False,
    'start_date': datetime(2026, 6, 1),  # Date de départ du scheduler
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,                        # En cas de crash, Airflow réessaie automatiquement 2 fois
    'retry_delay': timedelta(minutes=5), # Il attend 5 minutes entre chaque tentative
    'on_failure_callback': alert_on_failure # Déclenche notre fonction d'alerte si tout échoue
}

# 3. Initialisation du DAG avec planification quotidienne
with DAG(
    'cryptopipelinedag',
    default_args=default_args,
    description='Automated End-to-End Medallion Crypto Pipeline with Snowflake Cloud Loading',
    schedule='@daily',                  # ✨ Corrigé pour Airflow 3.0 (remplace schedule_interval)
    catchup=False,                      # N'exécute pas les jours passés au premier démarrage
    tags=['crypto', 'medallion', 'snowflake'],
) as dag:

    # Définition du chemin de base vers ton projet pour les scripts
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

    # Task 4: Chargement Snowflake (Star Schema Parquet -> Snowflake Cloud)
    load_snowflake = BashOperator(
        task_id='load_snowflake',
        bash_command=f'python {PROJECT_DIR}/scripts/load_snowflake.py',
    )

    # 4. Définition du Workflow (L'ordre des dépendances)
    ingest_bronze >> transform_silver >> build_gold_model >> load_snowflake