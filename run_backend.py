import uvicorn
uvicorn.run('backend.app.main:app', host='0.0.0.0', port=8001, reload=True)