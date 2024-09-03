from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from routers.data import data_router
from routers.model import model_router

app = FastAPI()


@app.get("/")
async def read_root():
    """
    Redirect to the API documentation.

    This endpoint redirects the root URL to the FastAPI documentation page.

    Returns:
        RedirectResponse: A response that redirects to the /docs URL.
    """
    return RedirectResponse(url="/docs")


app.include_router(data_router)
app.include_router(model_router)
