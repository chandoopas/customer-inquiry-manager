import os
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

client = AzureOpenAI(
    api_key        = os.getenv("AZURE_OPENAI_KEY"),
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version    = "2024-02-01"
)

response = client.chat.completions.create(
    model    = os.getenv("AZURE_OPENAI_DEPLOYMENT"),
    messages = [
        {"role": "user", "content": "Say hello in one sentence."}
    ]
)

print("✅ Connected to Azure OpenAI!")
print(f"Response: {response.choices[0].message.content}")