from mistralai import Mistral
from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole
import telegramify_markdown
import asyncio
import os

from dotenv import load_dotenv

load_dotenv()


async def get_mistral_api(model: str, content: dict, api_key: str):
    client = Mistral(api_key=api_key)

    content_dict = [
        {"role": "system", "content": str(content.get('system'))},
        {"role": "user", "content": str(content.get('user'))}]

    # Get the chat response
    res = await client.chat.complete_async(
        model=model,
        messages=content_dict
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


async def get_gigachat_api(model: str, content: dict, api_key: str):

    client = GigaChat(credentials=api_key, verify_ssl_certs=False, model=model)

    prompt = str(content.get('system'))
    text_user = str(content.get('user'))

    payload = Chat(
        messages=[
            Messages(
                role=MessagesRole.SYSTEM,
                content=prompt,
            )
        ],
        temperature=0.2
    )

    payload.messages.append(Messages(role=MessagesRole.USER, content=text_user))
    res = client.chat(payload)

    if res is not None:
        escape_text = telegramify_markdown.markdownify(
            res.choices[0].message.content, latex_escape=True, normalize_whitespace=False)
        return escape_text


if __name__ == "__main__":

    # acces_token = get_gigachat_accesstoken()

    text = input('Введи запрос: ')
    prompt = (
        'Ты профессиональный зоолог, рассказывай о животных краткие'
        ' 5 фактов и в конце каждго своего сообщения пиши слово "курочка"')

    content = {'system': prompt, 'user': text}

    response_mistral = asyncio.run(
        get_mistral_api(
            api_key=os.getenv('Mistral_API'),
            model="mistral-small-latest", content=content))

    print(f'Mistral:\n{response_mistral}')

    response_gigachat = asyncio.run(
        get_gigachat_api(
            api_key=os.getenv('GIGACHAT_KEY'),
            model="GigaChat", content=content))

    print(f'Gigachat:\n{response_gigachat}')
