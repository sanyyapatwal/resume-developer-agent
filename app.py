import streamlit as st
import os
import time
import langchain
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from tavily import TavilyClient
import pytesseract as pyt
import numpy as np
from langchain.messages import SystemMessage , HumanMessage
from langchain.agents import create_agent
import tempfile
from PIL import Image
import base64
  
st.set_page_config(layout="wide")
# streamlit is web based python frame work
st.title("AI RESUME MAKER & JOB APPLY AGENT")
st.image("https://media2.dev.to/dynamic/image/width=1000,height=420,fit=cover,gravity=auto,format=auto/https%3A%2F%2Fdev-to-uploads.s3.amazonaws.com%2Fuploads%2Farticles%2F217gvesbwwjbio4tgoji.png", width=300)
#================FRONJTEND======================

st.title("AI RESUME GENERATOR")

GOOGLE_API_KEY = st.sidebar.text_input("Google Api Key", type='password')
GROQ_API_KEY  = st.sidebar.text_input("Groq Api Key", type='password')
TAVILY_API_KEY  = st.sidebar.text_input("Tavily Api Key", type='password')

if not (GOOGLE_API_KEY) and not (GROQ_API_KEY) and not (TAVILY_API_KEY):
  st.sidebar.warning("Provide API keys")
else:
  st.success("API KEYS LOADED")


#============= MODEL AND AGENT CODE ==============

def search_latest_news_jobs(query):
  """ this function helps to get
  latest news or latest jobs
  related to user given query
  using tavily"""

  from tavily import TavilyClient
  client = TavilyClient(api_key = TAVILY_API_KEY)
  return client.search(query)


# step 4 : Model and Agent creation
model1 = ChatGoogleGenerativeAI(
    model = "gemini-3.5-flash-lite",
    google_api_key = GOOGLE_API_KEY
)
model2 = ChatGroq(
    model="qwen/qwen3.6-27b",
    api_key= GROQ_API_KEY
)
# ========== Agent with tool==========
agent = create_agent(
    model = model1,
    tools = [search_latest_news_jobs]
)


# prompt for resume
def prompt_generator():
 prompt = """"you are a helpful ai assistant  with a job resume maker , your task is to give html gormat resume ,
  with a proper designing using recent html js css code , with professional degsine format , 
  user will upload data and return html format resume make it diffrent colour scheme andthe resume should project m skill set  also make it look like professional , 
  create side margins table also make the text gradient for heddings like professional summary
  IMPORTANT: wherever the profile photo goes in the resume, output exactly this tag and nothing else:
  <img src="PROFILE_IMAGE_PLACEHOLDER" style="width:100px;height:100px;border-radius:50%;">
  do not draw or generate any other image tag or placeholder circle yourself"""

 response = model1.invoke(prompt)
 prompt_ans = response.content[-1]['text']

 file_name = 'prompt.txt'
 with open(file_name , 'w') as f:
  f.write(prompt_ans)

prompt_generator()


# tool 2
def prompt_reader():
  with open('prompt.txt','r') as f:
    prompt = f.read()
  return prompt

prompt = """ i want complete professional
resume with dynamic design using advance CSS and JS
and must show user input details
system instructions: only give HTML code as output"""

final_prompt = prompt + prompt_reader()
# ============upload image===================

FILE=st.sidebar.file_uploader(
  "choose an image file",
  type=["jpg","jpeg","png","webp"]
)
if FILE is not None:
  try:
    image=Image.open(FILE)
    st.sidebar.image(image,caption="uploaded image",
                     use_container_width=True)
    if image.mode in("RGBA","p"):
      image=Image.convert("RGB")
      
    base_name = os.path.splitext(FILE.name)[0]
    save_path= f"{base_name}.jpg"

    image.save(save_path,"JPEG")
    st.sidebar.success(f"image loaded and saved as '{save_path}'!")
  except Exception as e:
    st.error(f"Error processing image:{e}")

user_info = st.text_input("Give Your Information: ")
user_query=f"""user details:given below :
resume info {user_info}
DEFAULT IF NOT GIVEN : PYTHON DEVELOPER RESUME"""

final_query = final_prompt + user_query

OPTIONS = ["DELHI","NOIDA","GURGAON/GURUGRAM",
          'KANPUR','LUCKNOW','BANGLORE','PUNE']
           
LOCATION = st.sidebar.multiselect('SELECT LOCATION: ',
                                    options = OPTIONS )

JOB_PROFILE = ["PYTHON DEVELOPER",'GEN AI',
                'FULL-STACK DEVELOPER','DATA ANALYST']

PROFILE = st.sidebar.multiselect("SELECT JOB ROLE",
                options = JOB_PROFILE)


job_prompt = f"""Based on {PROFILE} jobs in {LOCATION}, I 
want latest job news in using tavily, 
try top 10 search or whatever available
and give result like naukri theme design with
job name, job desc, salary,
apply link and OUTPUT must be In HTML no markdowns"""
if st.button("Generate Resume"):
  with st.spinner("Agent creating Resume..."):
    response = agent.invoke({'messages':[{'role':'user',"content":final_query}]})
    code = response['messages'][-1].content[-1]['text']

  if FILE is not None:
    with open(save_path,"rb") as img_file:
      b64_image= base64.b64encode(img_file.read()).decode()
      data_url = f"data:image/jpeg;base64,{b64_image}"
      code = code.replace("PROFILE_IMAGE_PLACEHOLDER", data_url)

  st.html(code, width="stretch", unsafe_allow_javascript=True)
  
  #================apply jobs====================
  st.divider()
  response = agent.invoke({'messages':[{'role':'user',"content":job_prompt}]})
  job_code = response['messages'][-1].content[-1]['text']
  st.html(job_code, width="stretch", unsafe_allow_javascript=True)
