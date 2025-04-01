from mistralai import Mistral
import telegramify_markdown
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()


async def api_get(model: str, content: str, api_key: str):
    client = Mistral(api_key=api_key)

    # Define the messages for the chat
    if content['url'] is not None:
        if "pdf" in content["url"]:
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": str(content['text'])
                        },
                        {
                            "type": "document_url",
                            "document_url": str(content['url'])
                        }
                    ]
                }
            ]
        else:
            ocr_response = client.ocr.process(
                model="mistral-ocr-latest",
                document={
                    "type": "image_url",
                    "image_url": content['url']
                }
            )
            print(ocr_response.pages[0].markdown)
            return
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": str(content['text'])
                        },
                        {
                            "type": "document_url",
                            "image_url": str(content['url'])
                        }
                    ]
                }
            ]
    else:
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": str(content['text'])
                    }
                ]
            }
        ]

    # Get the chat response
    res = await client.chat.complete_async(
        model=model,
        messages=messages
    )

    # stream content
    """async for chunk in chat_response:
        if chunk.data.choices[0].delta.content is not None:
            print(chunk.data.choices[0].delta.content, end="")
    print('\n')"""
    # complete content
    if res is not None:
        escape_text = telegramify_markdown.markdownify(
            res.choices[0].message.content, latex_escape=True, normalize_whitespace=False)
        return escape_text

if __name__ == "__main__":
    url = input('Введи url: ')
    text = input('Введи запрос: ')
    content = {
        "text": str(text),
        "url": str(url)
    }
    asyncio.run(api_get(api_key=os.getenv('Mistral_API'), model="mistral-large-latest", content=content))
