import uvicorn
from multiprocessing import freeze_support

def run():
    """
    Runs the Uvicorn server for the FastAPI app in 'backend.app.main'.
    """
    freeze_support()
    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",    
        port=8000,      
        reload=False,    
        workers=4          
    )

if __name__ == "__main__":
    run()
