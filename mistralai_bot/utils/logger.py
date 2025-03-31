import logging


async def logger(message, text):
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    logging.info(f'\n      {user_id=}\n      {user_name=}\n'
                 f'     message_text={text}')
