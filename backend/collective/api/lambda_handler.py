"""
Lambda handler for FastAPI application using Mangum
"""

from mangum import Mangum
from .app import app

# Create Lambda handler
handler = Mangum(app, lifespan="off")
