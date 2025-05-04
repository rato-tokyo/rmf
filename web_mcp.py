from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import sys
import os

app = FastAPI()

class TextRequest(BaseModel):
    text: str

class ToolRequest(BaseModel):
    tool: str
    arguments: dict

@app.get("/tools/list")
async def list_tools():
    return {
        "tools": [
            {
                "name": "to_uppercase",
                "description": "テキストを大文字に変換するツール",
                "parameters": {
                    "text": {
                        "type": "string",
                        "description": "変換したいテキスト"
                    }
                }
            }
        ]
    }

@app.post("/tools/call")
async def call_tool(request: ToolRequest):
    if request.tool == "to_uppercase":
        text = request.arguments.get("text", "")
        return {"content": [{"type": "text", "text": text.upper()}]}
    return {"content": [{"type": "text", "text": "Unknown tool"}]}

def main():
    uvicorn.run(app, host="127.0.0.1", port=8003, log_level="info")

if __name__ == "__main__":
    main() 