# test.py
import sys
import faiss
import numpy as np
import torch
import torchvision
import sentence_transformers
import transformers
import fastapi
import uvicorn
import requests
import pydantic
import nltk
from dotenv import load_dotenv

try:
    # Example usage
    load_dotenv()  # Loads environment variables from a .env file

    print("✅ All main packages imported successfully!")
    print(f"Python: {sys.version}")
    print(f"Numpy: {np.__version__}")
    print(f"FAISS: {faiss.__version__}")
    print(f"Torch: {torch.__version__}")
    print(f"Sentence-Transformers: {sentence_transformers.__version__}")
    print(f"FastAPI: {fastapi.__version__}")
except Exception as e:
    print("❌ Something went wrong!")
    print(e)
