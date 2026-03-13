import operator 
from typing import Annotated, Any, Dict, List, Optional, Tuple, TypedDict

# define the schema for a single compilance search 
#Errror report generated 
class CompilanceIssue(TypedDict):
    category:str
    description:str   #specific derailed description of the issue
    severity:str
    timestamp: Optional[str]

# define the global graph states 
class VideoAuditState(TypedDict):
    '''
    Defines the data schema for langgraph execution content 
    Main container:Which Holds all the intermediate information  from url till the report generation and final status.
    '''
    #input parameters
    video_url:str
    video_id:str

    #ingestipon and extraction data 
    local_file_path:Optional[str]
    video_metadata:Optional[Dict[str,Any]]
    transcript:Optional[str]  # converted text or speech from video 
    ocr_text:List[str]

    #analysis output
    compilance_results: Annotated[List[CompilanceIssue],operator.add]

    #final status 
    final_status:str  #pass or fail (1 ,0)
    final_report:str  #markdown format 

    #system observability
    errors:Annotated[list[str],operator.add]

