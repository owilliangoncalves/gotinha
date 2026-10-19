import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_openrouter import ChatOpenRouter

load_dotenv()

OPENROUTER_KEY = os.getenv('OPENROUTER_API_KEY')
MODEL = os.getenv('MODEL')
BASEURL= os.getenv('BASE_URL')

assert MODEL is not None
llm = ChatOpenRouter(model=MODEL, api_key=OPENROUTER_KEY, base_url=BASEURL)

gotinha = create_agent(model=llm)

resposta = gotinha.invoke({'messages': [{'role': 'user', 'content': 'O que você pode fazer?'}]})

print(resposta['messages'][-1].content)
