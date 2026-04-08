import json 
import os
import re
from typing import Any,List,Dict,Annotated
import logging

from langchain_openai import AzureChatOpenAI,AzureOpenAIEmbeddings
from langchain_community.vectorstores import AzureSearch
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage,HumanMessage

#import the schema 
from backend.src.graph.state import VideoAuditState,CompilanceIssue

#import services 
from backend.src.services.video_indexer import VideoIndexerServices 

#Configuure the logger 
logger=logging.getLogger("brand-guardian")
logging.basicConfig(level=logging.INFO)

#NODE 1:INDEXER 
#function responsible from video to text 
def index_video_indexer(state:VideoAuditState)->Dict[str,Any]:
    '''
    This node is responsible for indexing the video content into Azure Search. It takes the video metadata, transcript, and OCR text as input and creates a searchable index in Azure Search. The function updates the state with the index information and any errors encountered during the indexing process.
    '''
    video_url=state.get("video_url")
    video_id_input=state.get("video_id","video_demo")
    logger.info(f"----[Node:Indexer] Processing :{video_url}")

    local_filename="temp_audio_video.mp4"

    try:
        vi_service=VideoIndexerServices()
        #dowload 
        if "youtube.com"in video_url or "youtu.be"in video_url:
            local_path=vi_service.download_youtube_video(video_url,output_path=local_filename)
        else:
            raise Exception("please provide a valid youtube url")
        # upload 
        azure_video_id=vi_service.upload_video(local_path,video_name=video_id_input)
        logger.info(f"Video uploaded to Azure with ID: {azure_video_id}")
        
        if os.path.exist(local_path):
            os.remove(local_path)
            logger.info(f"Local file {local_path} removed after upload.")
            
        # wait 
        raw_insigths=vi_service.wait_for_processing(azure_video_id)
        
        #extract
        clean_data=vi_service.extract_data(raw_insigths)
        logger.info("----[NODE:Indexer]Extraction complete .....")
        return clean_data
    
    except Exception as e:
        logger.error(f"Error in index_video_indexer: {str(e)}")
        return {
            "errors":[str(e)],
            "final_ststus":"failed",
            "transcript":"",
            "ocr_text":[]
        }

# Node 2 :Compilance Auditor
def audio_content_node(state:VideoAuditState)->Dict[str,Any]:
    '''
    PerfoRMS RAG to audit the video 
    '''
    logger.info(": ...[Node:Audiot]quering knowlege base &LLM")
    transcript=state.get("transcript","")
    if not transcript:
        logger.info("No transcript available for auditing.Skipping audit....")
        return{
            "final_stauts":"FAILED",
            "final_report":"Audit Skipped due to missing transcript",

        }
    # intalize the azure clients 
    llm=AzureChatOpenAI(
        azure_deployment=os.getenv("AZURE_OPENAI_CHAT_DEVELOPMENT"),
        openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        temperature=0.2,
    )

    embeddings=AzureOpenAIEmbeddings(
        azure_deployment="text-embedding-3-small",
        openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    )

    vectorstore=AzureSearch(
        azure_search_endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
        azure_search_key=os.getenv("AZURE_SEARCH_API_KEY"),
        index_name=os.getenv("AZURE_SEARCH_INDEX_NAME"),
        embedding_function=embeddings.embed_query
    )

    #RAG RETREVAL PART 
    ocr_text=state.get("ocr_text",[])
    query_tecxt=f"{transcript} {' '.join(ocr_text)}"
    docs=vector_store.similarity_search(query_tecxt,k=3)
    retrieved_rules="\n\n",join([doc.page_content for doc in docs])

    system_prompt=f"""
            you are a senior brand compilance auditor.
            OFFICAL REGULATORY RULES:
            {retrieved_rules}
            INSTRUCTION:
            1)Analze the Transcript and Ocr TeXT Below.
            2)Identify any violation of the rules.
            3)Return Striucly in the json format
            {{
                "compilance_issues":[
                    {{
                        "category":"Claim Validation",
                        "description":"detailed description of the issue",
                        "severity":"Critical",
                        "timestamp":"timestamp of the issue in the video"
                    }}
                ],
                "status":"pass or fail",
                "final_report":"Summary of findings....."            
                }} 
                
                If no Viloation are found ,set "status" to "PASS" and "compilance_issue" to [].
            """
    user_message=f""" 
    VIDEO_METADATA:(state.get("video_metadata",{}))
    TRANSCRIPT:{transcript}
    ONSCREEN TEXT(OCR):{ocr_text}
    """
    try:
        response=llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message)
        ])
        content=response.content
        # if "```" in content:
        #     content=re.search(r"```(?:json)?(.?)```",content,re.DOTALL).group(1)
        #     audit_data=json.loads(content.strip())
        #     return {
        #         "compilance_results":audit_data.get("compilance_issues",[]),
        #         "final_status":audit_data.get("status","FAIL"),
        #         "final_report":audit_data.get("final_report","No report generated.")
        #     }
    except Exception as e:
        logger.error(f"Error in audio_content_node: {str(e)}")
        #logging the raw data 
        logger.error(f"Raw LLM response: {response.content if 'response' in locals() else 'No response received'}")
        return{
            "errors":[str(e)],
            "final_status":"FAILED",
        }


