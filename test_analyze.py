import os
from openai import OpenAI

client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key="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",
)
portfolio_data = {
    "cash": 5000,
    "holdings": [
        {"ticker": "AAPL", "quantity": 10, "price": 175.35},
        {"ticker": "TSLA", "quantity": 5, "price": 280.50},
    ]
}

completion = client.chat.completions.create(
    model="openai/gpt-oss-20b:together",
    messages=[
        {
            "role": "user",
            "content": f"Analyze this portfolio and provide insights:\n{portfolio_data}"
        }
    ],
)

print(completion.choices[0].message)

