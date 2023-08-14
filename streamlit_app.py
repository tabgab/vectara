
import streamlit as st
from PIL import Image
import requests
import json
import os
import openai

st.cache_data.clear()
# Using Streamlit's caching mechanism to load environment variables and keep them in memory
@st.cache_data(ttl=36000)
def load_env_vars():
    
    load_dotenv("./.env")  # Replace with the actual path to your .env file
    return {
        "OPENAI_API_KEY": os.getenv('OPENAI_API_KEY'),
        "VECTARA_CUSTOMER_ID": os.getenv('VECTARA_CUSTOMER_ID'),
        "VECTARA_CORPUS_ID": os.getenv('VECTARA_CORPUS_ID'),
        "VECTARA_API_KEY": os.getenv('VECTARA_API_KEY')
    }



#Changed from env_vars to the streamlit secrets system for streamlit deployment.
#env_vars = load_env_vars()
OPENAI_API_KEY = st.secrets.OPENAI_API_KEY
VECTARA_CUSTOMER_ID = st.secrets.VECTARA_CUSTOMER_ID
VECTARA_CORPUS_ID = st.secrets.VECTARA_CORPUS_ID
VECTARA_API_KEY = st.secrets.VECTARA_API_KEY

if OPENAI_API_KEY==None:
    OPENAI_API_KEY = ""

# LOGGIG HERE
#logvar = "Init. OPENAI KEY IS NOW: "+ OPENAI_API_KEY

# Initialize the OpenAI API with the key
openai.api_key = OPENAI_API_KEY

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

# Streamlit interface


import base64

def image_to_base64(img_path):
    with open(img_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode('utf-8')

# Custom CSS to change the background color, position the image and title, and set the image size
st.markdown("""
    <style>
        body, .stApp, .stApp .stReportView, .stApp .stReportView .stPane, .stApp .stReportView .stBlock {
            background-color: #444654 !important;  # Change to your desired color
        }
        .header-container {
            display: flex;
            text-color:#FFFFFFFF
            align-items: center;  # Vertically center the title with the image
            position: absolute;
            top: 0px;
            left: 0px;
            z-index: 999;  # Ensure it's above other elements
        }
        .top-left-img {
            width: 50px;
            height: 50px;
            margin-right: 10px;  # Space between the image and the title
        }
        /* Optional: Remove Streamlit's default padding */
        .reportview-container {
            padding: 0px !important;
        }
    </style>
    """, unsafe_allow_html=True)

# Displaying the Image and Title in the top left corner
image_path = "./omnestlogo.jpg"  # Change to your image path
base64_img_str = image_to_base64(image_path)
header_html = f'''
<div class="header-container">
    <img src="data:image/jpeg;base64,{base64_img_str}" class="top-left-img">
    <h1>OMNEST / OMNeT++ Sage</h1>
</div>
'''
st.markdown(header_html, unsafe_allow_html=True)

#st.text_area(logvar)

#st.title("OMNEST / OMNeT++ Sage")

####################################################################
# Check if API keys are defined, and ask for them if they are not. #
####################################################################
if len(VECTARA_API_KEY)<2:
    VECTARA_API_KEY= st.text_input("Please enter a valid VECTARA API KEY to proceed.")
    st.text("If you provide an invalid key, this will not work and throw an error.")
if len(OPENAI_API_KEY)<2:
    OPENAI_API_KEY= st.text_input("Please enter a valid OPENAI KEY to proceed.")
    st.text("If you provide an invalid key, this will not work and throw an error.")

#Nesting question handling here to avoid calling "espensive" OpenAI without an API KEY.
if len(OPENAI_API_KEY)>5:
  openai.api_key=OPENAI_API_KEY
  
  ######################################
  #   # Text input for user's question #
  ######################################

  user_question = st.text_input("Enter your question:")
  #VERBOSE VECTARA OUTPUT HERE
  verbose = st.checkbox('Display verbose output with source text.')

  if st.button("Submit"):
      set_nested_query(querryarray, user_question)
      st.write("Questions is: " + get_nested_query(querryarray))

      # Sending query to Vectara here
      response = requests.request("POST", url, headers=headers, data=json.dumps(querryarray))
      data = response.json()

      # Filtering out the text from the response JSON received from Vectara
      text_contents = ' '.join([item['text'] for response in data['responseSet'] for item in response['response']])

      if verbose:
        if len(text_contents)>1:
            st.text_area(text_contents)

      # Assemble the query for the AI
      prelude = ("Give a detailed and factual answer of at least 150 words to the question"
                ",give the relevant section names in the documentation whenever possible: ")
      afterwords = "Do not make up anything, use the provided text prompt only! Please list the exact refrences you use."
      originalquestion = get_nested_query(querryarray)
      question = prelude + originalquestion + afterwords


      # Submit the question and document to ChatGPT (assuming you have the necessary openai setup done)
      response = openai.Completion.create(
        model="text-davinci-003",
        prompt=f"{text_contents}\n\nQ: {question}\nA:",
        max_tokens=1500,
        n=1,
        stop=None,
        temperature=0.0
      )

      # Extract and display the answer
      answer = response.choices[0].text.strip()
      st.text_area("Answer:", value=answer, height=600)

