import openai

from settings import GPT_TOKEN, logger

openai.api_key = GPT_TOKEN

completion = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
        {
            "role": "user",
            "content": "Tell the world about the ChatGPT API in the style of a pirate.",
        }
    ],
)

logger.debug(completion.choices[0].message.content)
