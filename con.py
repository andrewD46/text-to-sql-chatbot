import requests
import snowflake.connector


SNOWFLAKE_ACCOUNT = 'ky59805.east-us-2.azure'
SNOWFLAKE_USER = 'AIRFLOW_USER'
SNOWFLAKE_PASSWORD = 'weindweq!ifn21!4f35f8D2d'
SNOWFLAKE_ROLE = 'ACCOUNTADMIN'
SNOWFLAKE_WAREHOUSE = 'CORTEX_ANALYST_WH'
SNOWFLAKE_DATABASE = 'CORTEX_ANALYST_DEMO'
SNOWFLAKE_SCHEMA = 'DEMO_SCHEMA'



conn = snowflake.connector.connect(
            user=SNOWFLAKE_USER,
            password=SNOWFLAKE_PASSWORD,
            account=SNOWFLAKE_ACCOUNT,
            warehouse=SNOWFLAKE_WAREHOUSE,
            role=SNOWFLAKE_ROLE,  # Optional
            # _get_raw_cnx=True
)
# Get the session token

api = f"https://{conn.host}/api/v2/cortex/analyst/message"


token = conn.rest.token

headers = {
        "Authorization": f'Snowflake Token="{token}"',
        "Content-Type": "application/json",
        # "X-Snowflake-Authorization-Token-Type": "OAUTH"
    }


request_body = {'messages': [{'role': 'user', 'content': [{'type': 'text', 'text': 'What questions can I ask?'}], 'request_id': None}], 'semantic_models': [{'semantic_model_file': '@CORTEX_ANALYST_DEMO.DEMO_SCHEMA.RAW_DATA/promotion_model.yaml'}, {'semantic_model_file': '@CORTEX_ANALYST_DEMO.DEMO_SCHEMA.RAW_DATA/NUSASIT_Master_data_model.yaml'}, {'semantic_model_file': '@CORTEX_ANALYST_DEMO.DEMO_SCHEMA.RAW_DATA/NUSASIT_WG_model.yaml'}, {'semantic_model_file': '@CORTEX_ANALYST_DEMO.DEMO_SCHEMA.RAW_DATA/NUSASIT_RESULT_tables.yaml'}, {'semantic_model_file': '@CORTEX_ANALYST_DEMO.DEMO_SCHEMA.RAW_DATA/NUSASIT_AC_tables.yaml'}]}

response = requests.post(
        api,
        headers=headers,
        json=request_body,
)

response.raise_for_status()

cortex_response_data = response.json()

print(cortex_response_data)