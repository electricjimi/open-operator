import traceback
from contextlib import asynccontextmanager
from browser_use.browser.browser import Browser
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from browser_use import Agent
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

browser = Browser()
context = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global context
    context = await browser.new_context()
    logger.info("Browser context initialized")
    yield
    await context.close()
    logger.info("Browser context closed")


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TaskRequest(BaseModel):
    api_key: str
    task: str


# API routes
@app.post("/api/run-task")
async def run_task(request: TaskRequest):
    try:
        logger.info(f"Starting task: {request.task}")

        llm = ChatOpenAI(
            model="gpt-4o",
            api_key=request.api_key
        )

        agent = Agent(
            task=request.task,
            llm=llm,
            browser_context=context
        )

        try:
            result = await agent.run()
            logger.info("Task completed successfully")

            if result is None:
                return {"status": "success", "result": "Task completed but no results were returned"}

            if not isinstance(result, str):
                result = str(result.history[-1].result[0].extracted_content)

            return {"status": "success", "result": result}

        except Exception as agent_error:
            logger.error(f"Agent error: {str(agent_error)}")
            logger.error(f"Full error: {traceback.print_exc()}")
            raise HTTPException(status_code=500, detail=f"Agent error: {str(agent_error)}")

    except Exception as e:
        logger.error(f"API error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Serve static files
@app.get("/")
async def read_index():
    return FileResponse('index.html')


app.mount("/static", StaticFiles(directory="."), name="static")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)