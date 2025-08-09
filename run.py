"""
Run script for the Fitness Knowledge Base server.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Add the project root to Python path
project_root = Path(__file__).parent.absolute()
os.environ["PYTHONPATH"] = str(project_root)

# Load environment variables
load_dotenv()

# Import and run the FastAPI app
import uvicorn
from api.main import app

if __name__ == "__main__":
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    uvicorn.run(app, host=host, port=port)