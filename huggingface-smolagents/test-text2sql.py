#%% load libs
from dotenv import load_dotenv
import os

load_dotenv()

print(os.getenv("HF_TOKEN")[:12] + "..." + os.getenv("HF_TOKEN")[-4:])
print(os.getenv("OPENAI_API_KEY")[:12] + "..." + os.getenv("OPENAI_API_KEY")[-4:])
print('* loaded the environment variables and libraries')


#%% setup the SQL environment
from sqlalchemy import (
    create_engine,
    MetaData,
    Table,
    Column,
    String,
    Integer,
    Float,
    insert,
    inspect,
    text,
)

engine = create_engine("sqlite:///:memory:")
metadata_obj = MetaData()

def insert_rows_into_table(rows, table, engine=engine):
    for row in rows:
        stmt = insert(table).values(**row)
        with engine.begin() as connection:
            connection.execute(stmt)

table_name = "receipts"
receipts = Table(
    table_name,
    metadata_obj,
    Column("receipt_id", Integer, primary_key=True),
    Column("customer_name", String(16), primary_key=True),
    Column("price", Float),
    Column("tip", Float),
)
metadata_obj.create_all(engine)

rows = [
    {"receipt_id": 1, "customer_name": "Alan Payne", "price": 12.06, "tip": 1.20},
    {"receipt_id": 2, "customer_name": "Alex Mason", "price": 23.86, "tip": 0.24},
    {"receipt_id": 3, "customer_name": "Woodrow Wilson", "price": 53.43, "tip": 5.43},
    {"receipt_id": 4, "customer_name": "Margaret James", "price": 21.11, "tip": 1.00},
    {"receipt_id": 5, "customer_name": "John Smith", "price": 80.01, "tip": 1.00},
    {"receipt_id": 6, "customer_name": "John Clark", "price": 12.21, "tip": 1.00},
]
insert_rows_into_table(rows, receipts)
print("* created the table with some data")


#%% take a look at the data
inspector = inspect(engine)
columns_info = [(col["name"], col["type"]) for col in inspector.get_columns("receipts")]

table_description = "Columns:\n" + "\n".join([f"  - {name}: {col_type}" for name, col_type in columns_info])
print(table_description)


#%% build agents
from smolagents import tool

@tool
def sql_engine(query: str) -> str:
    """
    Allows you to perform SQL queries on the table. Returns a string representation of the result.
    The table is named 'receipts'. Its description is as follows:
        Columns:
        - receipt_id: INTEGER
        - customer_name: VARCHAR(16)
        - price: FLOAT
        - tip: FLOAT

    Args:
        query: The query to perform. This should be correct SQL.
    """
    output = ""
    with engine.connect() as con:
        rows = con.execute(text(query))
        for row in rows:
            output += "\n" + str(row)
    return output

print('* defined the sql_engine tool')


#%% define the agent
from smolagents import CodeAgent, InferenceClientModel, OpenAIServerModel

agent = CodeAgent(
    tools=[sql_engine],
    # model=InferenceClientModel(model_id="Qwen/Qwen2.5-Coder-32B-Instruct"),
    model=OpenAIServerModel(
        model_id="gpt-4.1-nano",
        api_key=os.getenv("OPENAI_API_KEY"),
    ),
)
print('* defined the query agent')


#%% simple queries
agent.run("Can you give me the name of the client who got the most expensive receipt?")


# %% more complex queries
agent.run("There is a client named John, but I don't know his last name. He has spent more than 50 dollars. Can you give me his full name and tip on that receipt?")


# %% take a look at the agent prompt
print(agent.prompt_templates["system_prompt"])


#%% let's create an instrumentor
from phoenix.otel import register
from openinference.instrumentation.smolagents import SmolagentsInstrumentor

register()
SmolagentsInstrumentor().instrument()
print('* instrumented the agent')


#%% let's try the agent again
agent.run("Can you give me the name of the client who got the most expensive receipt?")
