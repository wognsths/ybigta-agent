from fastapi import FastAPI
from app.agents.database_agent.database.router.db_router import router

app = FastAPI(
    title="Database API",
    description="API for the database connection",
    version="1.0.0"
)

app.include_router(router, prefix="/db", tags=["database"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the Database API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)