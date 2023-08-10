#This is a vectara example

import streamlit as st 
#from langchain.document_loaders import TextLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.embeddings import FakeEmbeddings
from langchain.llms import OpenAI 
#from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import Vectara
from langchain.chains import RetrievalQA
import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
VECTARA_CUSTOMER_ID = os.getenv('VECTARA_CUSTOMER_ID')
VECTARA_CORPUS_ID = os.getenv('VECTARA_CORPUS_ID')
VECTARA_API_KEY = os.getenv('VECTARA_API_KEY')


def langchain_func(file, question):
    loader = TextLoader(file, encoding='utf8')
    documents = loader.load()
    vectara = Vectara.from_documents(documents, embedding=None)
    qa = RetrievalQA.from_llm(llm=OpenAI(), retriever = vectara.as_retriever())
    answer = qa({"query": question})
    return answer

###
# Streamlit Code
###
st.title("Ask OMNEST / OMNeT++ Documentation Here")

def process_question(question):
    # This is a placeholder function. You can replace it with your processing logic.
    return f"Result for the question: {question}"

# Create a text input for users to enter their question
user_question = st.text_input("Enter your question:")

# Create a button that, when clicked, processes the user's question
if st.button('Submit'):
    result = process_question(user_question)
    
    # Display the result in a scrollable text area
    st.text_area("Result:", value=result, height=200)

#file_uploader = st.file_uploader("Upload your File", type=['txt'])

"""if file_uploader is not None:
    file_name = file_uploader.name
    with open(os.path.join(file_name),"wb") as f:
            f.write(file_uploader.getbuffer())
    question = st.text_area("Enter your Query")
    if st.button("Retrieve"):
        if len(question) > 0:
            answer = langchain_func(file_name, question)
            st.info("Your Question: "+ question)
            st.success("Your Answer: "+ answer['result'])"""
