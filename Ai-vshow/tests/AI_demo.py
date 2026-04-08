from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()

resp = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "你是一个助手"},
        {"role": "user", "content": "你好"}
    ],
    temperature=0
)

print(resp)