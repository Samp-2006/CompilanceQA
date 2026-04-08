import os 
import json 
import logging
from typing import Dict,Any,List

from azure.identity import DefaultAzureCredential
import requests

logger=logging.getLogger("VideoIndexer")

class VideoIndexerService:
    def __init__(self):
        self.account_id=os.getenv("AZURE_VI_ACCOUNT_ID ")
        self.location=os.getenv("AZURE_VI_LOCATION")
        self.subscription_id=os.getenv("AZURE_SUBSCRIPTION_ID")
        self.resource_group=os.getenv("AZURE_RESOURCE_GROUP")
        self.vi_name=os.getenv("AZURE_VI_NAME","project-brand-guardian-001")
        self.credentials=DefaultAzureCredential()

    def get_access_token(self)->str:
        '''
        Geneartes an ARM ACCESS TOKEN for the Video Indexer API using Azure Identity credentials.
        '''
        try:
            token=self.credentials.get_token("https://management.azure.com/.default")
            return token.token
        except Exception as e:
            logger.error(f"Error obtaining access token: {str(e)}")
            raise Exception("Failed to obtain access token for Video Indexer API")
    

    def get_account_token(self,arm_access_token:str)->str:
        '''
        Uses the ARM access token to get a Video Indexer account access token.
        '''
        try:
            url=f"https://api.videoindexer.ai/Auth/{self.location}/Accounts/{self.account_id}/AccessToken?allowEdit=true"
            headers={"Authorization":f"Bearer {arm_access_token}"}
            response=requests.get(url,headers=headers)
            response.raise_for_status()
            return response.text.strip('"')
        except Exception as e:
            logger.error(f"Error obtaining account access token: {str(e)}")
            raise Exception("Failed to obtain account access token for Video Indexer API")

   # function to the upload the youtube video 
     def youtube_video_upload(self,url,output_path="temp_video.mp4"):
        """
        Downloads a YouTube video using yt-dlp and saves it to the specified output path.
        """
        logger.info(f"Downloading YouTube video from URL: {url}")

        yd1_opts={
            "format":"bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "outtmpl":output_path,
            "quiet":True,
            "overwrites":True,
            "no_warnings":True,
        }

        try:
            with yt_dlp.YoutubeDL(yd1_opts) as ydl:
                ydl.download([url])
            logger.info(f"Video downloaded successfully and saved to: {output_path}")
            return output_path
        
        except Exception as e:
            logger.error(f"Error downloading YouTube video: {str(e)}")
            raise Exception("Failed to download YouTube video")
        
    #uplaod the video to the video indexer
    def upload_video(self,video_path:str,video_name):
        arm_token=self.get_access_token()
        vi_token=self.get_account_token(arm_token)

        api_url=f"https://api.videoindexer.ai/{self.location}/Accounts/{self.account_id}/Videos?name={video_name}&privacy=Private&videoUrl={video_path}"

        parms={
            "accessToken":vi_token,
            "name":video_name,
            "privacy":"Private",
            "indexingPreset":"Default",
        }

        logger.info(f"Uploading video to Video Indexer: {video_name}")

        # open the file in the binary and stream in azure 

        with open(video_path,"rb") as video_file:
            files={"file":(video_name,video_file,"application/octet-stream")}
            response=requests.post(api_url,params=parms,files=files)
        if response.status_code==200:
            logger.info(f"Video uploaded successfully: {video_name}")
            return response.json()
        
    def wait_for_processing(self,video_id:str):
        arm_token=self.get_access_token()
        vi_token=self.get_account_token(arm_token)

        api_url=f"https://api.videoindexer.ai/{self.location}/Accounts/{self.account_id}/Videos/{video_id}/Index?accessToken={vi_token}"

        while True:
            response=requests.get(api_url)
            if response.status_code==200:
                data=response.json()
                state=data.get("state")
                logger.info(f"Video processing state: {state}")
                if state=="Processed":
                    return data
                elif state in ["Failed","Error"]:
                    raise Exception(f"Video processing failed with state: {state}")
            else:
                logger.error(f"Error checking video processing status: {response.text}")
                raise Exception("Failed to check video processing status")
    
    def extract_data(self,vi_json):
        tarnscript_lines=[]
        for v in vi_json.get("videos",[]):
            for insights in v.get("insights",{}).get("transcript",[]):
                tarnscript_lines.append(transcript.get("text"))

        ocr_lines=[]
        for v in vi_json.get("videos",[]):
            for insights in v.get("insights",{}).get("ocr",[]):
                ocr_lines.append(insights.get("text"))
        return {
            "transcript":"\n".join(tarnscript_lines),
            "ocr":"\n".join(ocr_lines),
            "video_id":vi_json.get("id")
        }