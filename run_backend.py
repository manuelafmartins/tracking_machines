import uvicorn
from multiprocessing import freeze_support

if __name__ == "__main__":
    freeze_support()
    uvicorn.run('backend.app.main:app',reload=True)
