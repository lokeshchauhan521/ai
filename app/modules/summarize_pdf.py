from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain.prompts import PromptTemplate
from langchain.chains.summarize import load_summarize_chain
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
# from utils.constants import LLM

import os
import sys

sys.path.append(os.path.dirname(os.path.realpath(__file__)))
import os
from dotenv import load_dotenv
import asyncio
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.summarize import load_summarize_chain
from utils.constants import LLM

load_dotenv()


def summary_query(query):
    question_prompt = """
        You will be given a question asked by a user. 
        Your task is to determine whether the question requires an answer from the document's content or if it is about the document itself (e.g., requests for summarization, highlights, numeric values, or a general overview of the PDF). 
        If the question is about the document, return True; otherwise, return False.
        Question:{question}
        """
    
    prompt = PromptTemplate(template=question_prompt, input_variables=["question"])
    # Set up the LLM chain with the model and the prompt template
    chain = prompt | LLM | StrOutputParser()

    # Run the chain with the input question to get an answer
    need_summary = chain.invoke(query)

    return need_summary

async def summarization_chain(documents):
    
    question_prompt = """
         Write a concise summary of the following text. 
         Ensure the summary includes only the most relevant information:
        {text}
        CONCISE SUMMARY:

        """
    prompt = PromptTemplate(template=question_prompt, input_variables=["text"])
    # Set up the LLM chain with the model and the prompt template
    chain = prompt | LLM | StrOutputParser()
    tasks = [chain.ainvoke(doc) for doc in documents]
    summaries = await asyncio.gather(*tasks)
    return summaries

async def get_summary(filepath):
    loader=PyPDFLoader(filepath)
    docs=loader.load()
    text_splitter=RecursiveCharacterTextSplitter(chunk_size=2000,chunk_overlap=500)
    documents=text_splitter.split_documents(docs)

    while True:
        print(f"iteration started :- {len(documents)}")
        summary_text = await summarization_chain(documents)
        summary_text = " ".join(summary_text)
        if len(documents) <= 50:
            break
        documents=text_splitter.split_text(summary_text)


    combine_prompt = """
    Please provide a concise, short and comprehensive summary of the following text, highlighting the key points and main ideas.
    The summary should be informative and capture the essential aspects of the original text, omitting less important details.

    ```{text}```
    CONCISE SUMMARY:
    """

    prompt = PromptTemplate(template=combine_prompt, input_variables=["text"])
    # Set up the LLM chain with the model and the prompt template
    chain = prompt | LLM | StrOutputParser()
    final_summary = chain.invoke(summary_text)

    return final_summary
        

if __name__ == "__main__":
    import time
    start = time.time()  

    summary = get_summary("/home/ravisrivastava/Documents/competiscan/csv2_ai_analysis/app/tmp_files/8466824.pdf")
    print(time.time()-start)
    print(summary)
