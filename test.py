import requests
import json
import os
from colorama import Fore

from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
VECTARA_CUSTOMER_ID = os.getenv('VECTARA_CUSTOMER_ID')
VECTARA_CORPUS_ID = os.getenv('VECTARA_CORPUS_ID')
VECTARA_API_KEY = os.getenv('VECTARA_API_KEY')

url = "https://api.vectara.io/v1/query"

querryarray = {
  "query": [
    {
      "query": "Default question?",
      "start": 0,
      "numResults": 10,
      "contextConfig": {
        "charsBefore": 30,
        "charsAfter": 30,
        "sentencesBefore": 3,
        "sentencesAfter": 3,
        "startTag": "<b>",
        "endTag": "</b>"
      },
      "corpusKey": [
        {
          "customerId": VECTARA_CUSTOMER_ID,
          "corpusId": VECTARA_CORPUS_ID,
          "semantics": "DEFAULT",
          "dim": [
            {
              "name": "string",
              "weight": 0
            }
          ],
          "metadataFilter": "part.lang = 'eng'",
          "lexicalInterpolationConfig": {
            "lambda": 0
          }
        }
      ],
      "rerankingConfig": {
        "rerankerId": 272725717
      },
      "summary": [
        {
          "summarizerPromptName": "string",
          "maxSummarizedResults": 0,
          "responseLang": "string"
        }
      ]
    }
  ]
}

payload = json.dumps(querryarray)

headers = {
  'Content-Type': 'application/json',
  'Accept': 'application/json',
  'customer-id': VECTARA_CUSTOMER_ID,
  'x-api-key': VECTARA_API_KEY
}

#Function to set the question in the JSON being sent to Vectara, replacing the default question in the querryarray.
def set_nested_query(data, value):
    # Ensure the first "query" key exists and is a list with at least one item
    if "query" not in data:
        data["query"] = [{}]
    elif not isinstance(data["query"], list) or len(data["query"]) == 0:
        data["query"] = [{}]

    # Set the value in the nested "query" key of the first item in the "query" list
    data["query"][0]["query"] = value

#Cannot stand the way this looks, wanted to make it human-readable. It just returns the question...
def get_nested_query(data):
    return data.get("query", [{}])[0].get("query")

#Set the question here.
set_nested_query(querryarray, "How can I use an external solver for TSN? Suggest code.")

print(Fore.GREEN+"Questions is: "+get_nested_query(querryarray)+Fore.RESET)

#Sending query to Vectara here
response = requests.request("POST", url, headers=headers, data=payload)
data = response.json()

#Filtering out the text from the response JSON received from Vectara.
text_contents = ' '.join([item['text'] for response in data['responseSet'] for item in response['response']])


import streamlit as st 
from langchain.embeddings import OpenAIEmbeddings
from langchain.embeddings import FakeEmbeddings
from langchain.llms import OpenAI 
from langchain.vectorstores import Vectara
from langchain.chains import RetrievalQA
from langchain.text_splitter import CharacterTextSplitter
from langchain.document_loaders import TextLoader
import openai

#comes from the .env as all other such values
openai_key = OPENAI_API_KEY


llm = OpenAI(temperature=0)
llm.model_name="text-davinci-003"
llm.top_p = 0.2
llm.max_tokens = 2500
llm.best_of = 5
embeddings = OpenAIEmbeddings()
text_splitter = CharacterTextSplitter(chunk_size=1500, chunk_overlap=100)

### We assemble the query for the AI here

#This is an instruction to the AI, passed in as part of the question. It precludes the question.
prelude = ("Give a detailed and factual answer of at least 150 words to the queston"
           ",give the relevant section names in the documentation whenever possible: ")

#This hopefully improves accuracy a bit...
afterwords = "Do not make up anything, use the provided text prompt only!"

#What the user wanted to ask
originalquestion = get_nested_query(querryarray)

question = prelude+originalquestion+afterwords

# Submit the question and document to ChatGPT
response = openai.Completion.create(
  model="text-davinci-003",
  prompt=f"{text_contents}\n\nQ: {question}\nA:",
  max_tokens=1500,
  n=1,
  stop=None,
  temperature=0.0
)

# Extract and print the answer
answer = response.choices[0].text.strip()

print(answer)
