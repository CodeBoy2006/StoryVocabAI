import logging
from typing import Callable, Any

from app import app
import openai
import os
from dotenv import load_dotenv
from backend import openai_ops, export

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

if __name__ == '__main__':
    app.run(debug=True)

