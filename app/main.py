from fastapi import FastAPI

from app.model import Base, engine
from app.routers.petitions import router as petitions_router
from app.routers.security import router as security_router

Base.metadata.create_all(bind=engine)

api = FastAPI(
    title="DDDC Petition API",
    description="Restful API for the Petition of the DDDC pilot project",
    version="0.2.0",
    redoc_url=None,
)

api.include_router(petitions_router, prefix="/petitions")
api.include_router(security_router)
