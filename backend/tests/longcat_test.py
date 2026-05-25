from openai import OpenAI

client = OpenAI(
    api_key="ak_24087r0Md5Hl19G7RM02X8pM0wy2e",
    base_url="https://api.longcat.chat/openai"
)

response = client.chat.completions.create(
    model="LongCat-Flash-Chat",
    messages=[
        {"role": "user", "content": "Hello!"}
    ],
    max_tokens=1000
)

print(response.choices[0].message.content)