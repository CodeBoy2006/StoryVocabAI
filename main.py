import os

import openai
from dotenv import load_dotenv

from app import app

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

if __name__ == '__main__':
    app.run(debug=True)
