import os
from langchain_community.vectorstores.chroma import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from modules.summarize_pdf import summary_query,get_summary
from utils.redis_utils import get_redis_summary, update_redis_summary
from utils.constants import LLM
from utils.utils_funcs import get_pdf_file
from utils.logger import FileLogs
from modules.produce_messages import produce_message
from utils.utils_funcs import get_topic_key
from utils.constants import TOPIC_NAME
import json
from utils.db_utils import get_db_summary,insert_db_summary
from utils.s3_utils import download_folder_from_s3, upload_folder_to_s3


logs = FileLogs().get_logger(os.path.basename(__file__))


async def get_answer(query,product_id):
    pdf_file_path = None
    download_status = False
    key = f"{product_id}"
    persist_directory = os.path.join(os.getcwd() , "chroma_files", key)
 
    if os.path.exists(persist_directory):
        logs.info(f"persist directory already exists :- {persist_directory}")
        db = Chroma(persist_directory = persist_directory,embedding_function=OpenAIEmbeddings())

    if not os.path.exists(persist_directory):
        logs.info("Downloading from s3 bucket")
        download_status = download_folder_from_s3(product_id)
        logs.info(f"Download status is {download_status}")
        db = Chroma(persist_directory = persist_directory,embedding_function=OpenAIEmbeddings())

    if not download_status:
        logs.info(f"creating new embedding file :- {persist_directory}")
        pdf_file_path = get_pdf_file(product_id)
        loader = PyPDFLoader(pdf_file_path)
        docs = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=500)
        documents = text_splitter.split_documents(docs)
        db = Chroma.from_documents(documents=documents, embedding=OpenAIEmbeddings(),
                                 persist_directory=persist_directory)
        upload_status = upload_folder_to_s3(product_id)
        logs.info(f"embedding file uploaded to s3 bucket status :- {upload_status}")
    
    retriever = db.as_retriever(search_type="similarity", search_kwargs={"k": 5})
    print(retriever.to_json())
        
    
    # Define Prompt Template
    prompt_template = """
    You are Competiscan's virtual assistant specialized in market analysis, 
    your main task is to understand in depth the client's needs and challenges. 
    During the conversation, the customer will ask you questions about the product and issue. Your approach should be detailed and solution oriented, making sure to gather relevant and complete information. Once you consider the conversation to be over, proceed to end the conversation in a courteous and professional manner. Here is the product you will be ask about:
    Please try to provide the answer only based on the context.

    {context}
    Question: {question}

    Helpful Answers:
    """
    prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])

    # Create RetrievalQA Chain
    retrievalQA = RetrievalQA.from_chain_type(
        llm=LLM,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": prompt}
    )

    summarize = summary_query(query)
    logs.info(f"summarize :- {summarize}")
    if eval(summarize):  # Check if input query relates to summary
        summary = get_db_summary(product_id)
        if not summary:
            logs.info(f"Generating fresh summary...")
            pdf_file_path = get_pdf_file(product_id)
            summary = await get_summary(pdf_file_path)
            status = insert_db_summary(product_id, summary)

        logs.info(f"summary is {summary}")
        
        chain = prompt | LLM | StrOutputParser()
        answer = chain.invoke({"context": summary, "question": query})
    else:
        print("retrieval query running")
        result = retrievalQA.invoke({"query": query})
        answer = result['result']

    logs.info(f"answer is {answer}")
    return answer

async def produce_and_generate_answer(question, user_id, product_id):
    answer = await get_answer(question , product_id)
    logs.info(f"answer in chat module {answer}")
    topic_key = get_topic_key(product_id, user_id)
    logs.info(f"topic_key in chat module {topic_key}")
    question_answer_data = {"question":question, "answer":answer}
    question_answer_data = json.dumps(question_answer_data)
    produce_message(topic=TOPIC_NAME, key=topic_key, message=question_answer_data)
    logs.info(f"message {question} produce to topic {TOPIC_NAME}")
    return question_answer_data
