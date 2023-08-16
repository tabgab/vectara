
import streamlit as st
from PIL import Image
import requests
import json
import os
import openai
import tiktoken
from google.oauth2 import service_account
from gsheetsdb import connect
import gspread
from datetime import datetime

st.cache_data.clear()

# Create a connection object.
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=[
        "https://www.googleapis.com/auth/spreadsheets",
    ],
)
conn = connect(credentials=credentials)


# Perform SQL query on the Google Sheet.
# Uses st.cache_data to only rerun when the query changes or after 10 min.
@st.cache_resource(ttl=6000)
def run_query(query):
    rows = conn.execute(query, headers=1)
    rows = rows.fetchall()
    return rows

sheet_url = st.secrets["public_gsheets_url"]
rows = run_query(f'SELECT * FROM "{sheet_url}"')

def addrowtoGsheet(rowtext):
    GSHEETS_URL = st.secrets['public_gsheets_url']
    client = gspread.authorize(credentials)
    sheet = client.open_by_url(GSHEETS_URL).sheet1
    #sheet.update('B1', rowtext)
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    rowvalues = [current_time, rowtext]
    sheet.append_row(rowvalues)
    
    

# Using Streamlit's caching mechanism to load environment variables and keep them in memory
@st.cache_data(ttl=360000)
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
        <h1> color: white </h1>
        .header-container {
            display: flex;
            color:#FFFFFF;
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

instuctions = """This is a chatbot interface where you can ask about OMNEST/OMNeT++ 
and the INET Framework. Our hope is that this chatbot may give you some 
pointers on where to find the answer to your question, and if you are lucky, 
even answer it.

We have tried to ensure the AI uses only the documentation to answer your
question and do so as accurately as possible. **Still, as with AI responses in general, the AI could be entirely wrong, just a bit wrong, or correct, but you should always check your answers for errors.**

**Use this entirely at your own risk, there is no warranty, implied or otherwise for the correctness of the answers, or that this is fit for any use at all.**

There is a Vectara Corpus feeding an OpenAI chatbot behind this chat interface.
The complete OMNEST/OMNeT++ documentation, the INET Framework documentation, and showcases have been fed into and indexed in the Vectara Corpus. When you submit a query, first this database is quizzed for relevant sections and that is passed into the AI to generate an answer. You can ask about OMNEST/OMNeT++ as well as the INET Framework.

If you check the checkbox for verbose data, you will also see what the Vectara
database output was from the docs."""

disclaimer = """We have tried to ensure the AI uses only the documentation to answer your question and do so as accurately as possible. 
**Still, as with AI responses in general, the AI could be entirely wrong, just a bit wrong, or correct, but you should always check your 
answers for errors.**

**Use this entirely at your own risk, there is no warranty, implied or otherwise for the correctness of the answers, 
or that this is fit for any use at all.**"""

with st.expander("Display instructions"):
    st.markdown(instuctions)

#This function allows us to count the number of tokens in the question before submitting them (and getting an error)

enc = "cl100k_base"
def count_tokens(text):
    tokens = tiktoken.get_encoding(enc).encode(text)
    return len(tokens)

def is_valid_api_key(api_key):
    openai.api_key = api_key
    try:
        # Make a simple call to the completions endpoint
        response = openai.Completion.create(
          engine="davinci",
          prompt="Translate the following English text to French: 'Hello, how are you?'",
          max_tokens=60
        )
        return True
    except openai.error.OpenAIError as e:
        # Handle different types of errors (e.g., authentication, rate limits, etc.)
        if "authentication" in str(e).lower():
            return False
        


####################################################################
# Check if API keys are defined, and ask for them if they are not. #
####################################################################
if len(VECTARA_API_KEY)<2:
    VECTARA_API_KEY= st.text_input("Please enter a valid VECTARA API KEY to proceed.")
    st.text("If you provide an invalid key, this will not work and throw an error.")
if len(OPENAI_API_KEY)<2 or is_valid_api_key(OPENAI_API_KEY)==False:
    OPENAI_API_KEY= st.text_input("Please enter a valid OPENAI KEY to proceed.")
    try:
       is_valid_api_key()==False
       st.success("Valid API key entered!")
    except ValueError:
       if OPENAI_API_KEY:  # Only show error if there's some input
        st.error("That's not a valid OpenAI API key!")
    st.text("If you provide an invalid key, this will not work and throw an error.")
    #st.error("OpenAI API Key invalid.")

#Nesting question handling here to avoid calling "espensive" OpenAI without an API KEY.
if is_valid_api_key(OPENAI_API_KEY)==True:
  st.success("OpenAI Key is now valid. Thank you.") 
  openai.api_key=OPENAI_API_KEY
  
  ######################################
  #   # Text input for user's question #
  ######################################
  def disablebutton(b):
      st.session_state["disabled"] =b
  
  def enablebutton(b):
      st.session_state["enabled"] = b

  user_question = st.text_input("Enter your question:")

  if user_question:
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

        test_tokens = f"{text_contents}\n\nQ: {question}\nA:"
        numtokens = count_tokens(test_tokens)
        if numtokens<4090:
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
          st.markdown(disclaimer)
          addrowtoGsheet(get_nested_query(querryarray))
          #user_question = None
          st.markdown("NEW APP")
        else:
          st.error("Too many tokens submitted error! I am sorry, your query exceeds the model's capabilities. The maximum tokens must be 4097. You submitted: "+str(numtokens)+" Please change the question to reduce this.", icon="🚨")
          #user_question = None

