from fastapi import FastAPI, Request
import uvicorn
from pydantic import BaseModel
from typing import List, Optional
import get_latest_news_script
from datetime import datetime

app = FastAPI()

class Message(BaseModel):
    content: str

class Metadata(BaseModel):
    article_id: str
    title: str
    source: str
    time: int
    by: str
    type: str
    text: str
    chunk_index: Optional[int] = None

class InputJSON(BaseModel):
    id: str
    vector: List[float]
    metadata: Metadata

@app.get("/api/")
async def root():
    return {"message": "API server is working"}

@app.get("/api/news")
async def getNews():    
    temp_update = datetime.now().strftime("%d-%m-%Y")
    lastest_update, output = get_latest_news_script.getLastestWithDate(temp_update)
    return {"date" : lastest_update, "output" : output}

@app.post("/api/prompt")
async def promptReq(message: Message):
    prompt = {message.content}
    output = f"TODO send the {prompt} message to the llm" # TODO send the prompt to the model and wait
    return {"output" : output}

@app.post("/api/add_data")
async def addDataReq(message: Message):
    output = f"This is our future plan"
    return {"output" : output}

@app.post("/api/add_json_data")
async def addDataJsonReq(json: InputJSON):
    prompt = {json.metadata.article_id}
    output = f"TODO send the {prompt} message to the llm" # TODO send the prompt to the model and wait
    return {"output" : output}

@app.get("/api/admin")
async def hacker(request: Request):
    client_host = request.client.host
    return {"message": "There's nothing here XD. and we may collect your ip " + client_host}

if __name__ == "__main__":
    
    uvicorn.run(app, host="127.0.0.1", port=2546)