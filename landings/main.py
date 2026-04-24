from fastapi import FastAPI

from landings.router import router

app = FastAPI(title="Landings Service")
app.include_router(router)
