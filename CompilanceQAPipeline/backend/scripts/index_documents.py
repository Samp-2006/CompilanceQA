import os
import glob
import logging
from dotenv import load_dotenv
load_dotenv(override=True)

#documents loader and splitter 
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSpiltter

from langchain_openai import AzureChatOpenAI,AzureOpenAIEmbeddings
from langchain_community.vectorstores import AzureSearch

#setup logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger=logging.getLogger("indexer")

def index_docs():
    '''
    This will read te pdf and chunks the data,and uploadto the azaure ai search 
    '''
    #define the paths,we look for the data
    current_dir=os.path.dirname(os.path.abspath(__file__))
    data_folder=os.path.join(current_dir,"../../backend/data")

    #check on the enviornment variabales
    logger.info("="*60)
    logger.info("Enviornmnet COnfig Chcek: ")
    logger.info(f"AZURE_OPENAI_ENDPOINT :{os.getenv('AZURE_OPENAI_ENDPOINT')}")
    logger.info(f"AZURE_OPENAI_API_VERSION :{os.getenv('AZURE_OPENAI_API_VERSION')}")
    logger.info(f"EMBEDDING DEPLOYMENT :{os.getenv('AZURE_OPENAI_EMBEDDING_DEPLOYMENT','txet-embedding-3-small')}")
    logger.info(f"AZURE_SEARCH_ENDPOINT :{os.getenv('AZURE_SEARCH_ENDPOINT')}")
    logger.info(f"AZURE_SEARCH_INDEX_NAME :{os.getenv('AZURE_SEARCH_INDEX_NAME')}")
    logger.info("="*60)

    #valodate the required enviornments 
    required_vars=[
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_API_VERSION",
        "AZURE_SEARCH_ENDPOINT",
        "AZURE_SEARCH_INDEX_NAME",
        "AZURE_SEARCH_API_KEY",
        "AZURE_SEARCH_API_KEY"
    ]

    missing_vars=[var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"missing Varaibales:{missing_vars}")
        logger.error("Please set the missing enviornment variables and rerun the script.")
        return 
    
    #initalize the embedding model 
    try:
        logger.info("Initializing Azure OpenAI Embeddings...")
        embeddings=AzureOpenAIEmbeddings(
            azure_deployment=os.getenv('AZURE_OPENAI_EMBEDDING_DEPLOYMENT','txet-embedding-3-small'),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION","2024-02-01")
        )
        logger.info("Azure OpenAI Embeddings initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing Azure OpenAI Embeddings: {str(e)}")
        logger.error("Please check your Azure OpenAI comfiguration and end point")
        return 
    
    #initalize the  Azure Serach 
    try:
        logger.info("Initializing Azure Search Vector Store...")
        vector_store=AzureSearch(
            azure_search_endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
            azure_search_key=os.getenv("AZURE_SEARCH_API_KEY"),
            index_name=os.getenv("AZURE_SEARCH_INDEX_NAME"),
            embedding_function=embeddings.embed_query
        )
        logger.info(f"Azure Search Vector Store :{index_name}initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing Azure Search Vector Store: {str(e)}")
        logger.error("Please check your Azure Search configuration and end point")
        return
    
    # find the pdf
    pdf_files=glob.glob(os.path.join(data_folder,"*.pdf"))
    if not pdf_files:
        logger.warning(f"No PDF files found in {data_folder}. Please add PDF documents to index.")
    logger.info(f"Found {len(pdf_files)} PDF files to process:{[os.path.basebame(f) for f in pdf_files]}")

    all_spilts=[]

    #process each pdf 
    for pdf_path in pdf_files
        try:
            logger.info(f"Processing PDF: {pdf_path}")
            loader=PyPDFLoader(pdf_path)
            raw_doc=loader.load()

            #chunks the data 
            text_splitter=RecursiveCharacterTextSpiltter(chunk_size=1000,chunk_overlap=200)
            splits=text_splitter.split_documents(raw_doc)
            for splits in spilts:
                splits.metadata["source"]=os.path.basename(pdf_path)
            all_spilts.extend(splits)
            logger.info(f"PDF {pdf_path} processed successfully with {len(splits)} chunks.")

        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {str(e)}")
        
    #upload the chunks to azure search
    if all_spilts:
        logger.info(f"Uploading {len(all_spilts)} chunks to Azure Search index:{os.getenv('AZURE_SEARCH_INDEX_NAME')}")
        try:
            # azure serach accepts the batches authomatially 
            vector_store.add_documents(documents=all_spilts)
            logger.info("="*60)
            logger.info("Documents uploaded to Azure Search successfully.")
            logger.info(f"Total Chunks Uploaded: {len(all_spilts)}")
            logger.info("="*60)
        except Exception as e:
            logger.error(f"Failed to upload the documents to Azure Search: {str(e)}")
            logger.error("Please check your Azure Search configuration and index status.")
        else:
            logger.warning("No document chunks to upload to Azure Search. Please check the PDF processing step for errors.")


if __name__=="__main__":
    index_docs()