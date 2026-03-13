'''
This module defines the DAG:DIRECTED ACYCLIC GRAPH that orchestra the cideo compilance audit process
it connecst the nodes using the SateGraph from langchain

START->index_video_node-> audit_content_node->End
'''

from langgraph.graph import StateGraph,END
from backend.src.graph.state import VideoAuditState

from backend.src.graph.node import index_video_indexer,audio_content_node

def create_graph():
    '''
    Constructs and compile the Lnagrpagh Worflow 
    returns :
    Compiled Grapgh :runnable grapgh object for execution 
    '''

    workflow=StateGraph(VideoAuditState)
    #add the nodes
    workflow.add_node("indexer",index_video_indexer)
    workflow.add_node("auditor",audio_content_node)
    #define the entry point 
    workflow.set_entry_point("indexer")
    #define the edges 
    workflow.add_edge("indexer","auditor")
    #once the aduit is complete the worflow ends

    workflow.add_edge("auditor",END)
    #compile the graph
    app=workflow
    return app

#expose the runnable app
app=create_graph()