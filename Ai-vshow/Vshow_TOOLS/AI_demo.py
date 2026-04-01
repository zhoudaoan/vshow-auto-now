import openai

client = openai.OpenAI(
    api_key="sk-qmcloud-8_kdYDK_Ga4r9i2CUo-Pods8jXxP4pIOVpJCH-JAmMo",
    base_url="https://api.qianmian.ai/v1"
)

response = client.chat.completions.create(
    model="gpt-5.4",
    messages=[
        {"role": "user", "content": "Hello!"}
    ]
)

print(response.choices[0].message.content)