import uvicorn

if __name__ == "__main__":
    # Note: app is referenced by import path, not the object
    uvicorn.run(
        "app.app:app",
        host="127.0.0.1",
        port=5010,
        reload=True,
    )