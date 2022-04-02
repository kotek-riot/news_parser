from pyrogram import Client

import config

import requests
from bs4 import BeautifulSoup

from loggers.init import logger

import time

# id канала, в который уйдут новости /
# id of a target channel to send news to
channel = config.channel_id

# запускаем клиент с помощью библиотеки pyrogram /
# start client session with a pyrogram library
bot = Client(
    session_name="news_parser_bot",
    bot_token=config.bot_token,
    api_id=config.api_id,
    api_hash=config.api_hash,
    parse_mode='html'
)

# ссылка на ресурс /
# link to a resource
URL = "https://your-resource/something"


# функция для формирования текста поста /
# functions to form a text to post
def get_last_post() -> str:
    # запрос страницы ресурса /
    # get page from resource
    page = requests.get(URL)
    soup = BeautifulSoup(page.content, "html.parser")
    post = soup.find("div", class_="feed__item l-island-round")
    content = post.find("div", class_="content-container")

    # классы страницы могут быть другими, из-за чего появится ошибка 'NoneType' object is not callable --
    # в таком случае нужно поискать на странице свои названия контейнеров /
    # if you get a 'NoneType' object is not callable error -- check the containers names
    # and look for correct ones for your resource

    # заголовок поста / header of a post
    post_title = content.find("div", class_="content-title content-title--short l-island-a").text.strip()
    # описание поста / description of a post
    description = content.find("p").text.strip()
    # ссылка на пост / link to a post
    url = post.find("a", class_="content-link", href=True)["href"].strip()

    # формируем текст поста / form a text to send
    text_to_send = (
        f'<b>{post_title}</b>\n\n'
        f'{description}\n\n'
        f'Читать далее: '
        f'{url}'
    )

    return text_to_send


# функция для отправки поста / function to send post
@bot.on_message()
async def send_post(client, message):
    try:
        logger.info('SEND POST START')
        if message.text == "start":
            text_to_send = get_last_post()
            # формируем первый пост, который отправим сразу же пользователю
            # form the first post to send to a user

            await bot.send_message(channel, text_to_send)
            logger.info(f'SEND TEXT: [{text_to_send}]')

            # фиксируем, какой пост был последним
            # fix what post was the last
            posts_list = [text_to_send]

            while True:
                # берем верхний пост в ленте
                # take the latest post
                text_to_send = get_last_post()

                # проверяем, что пост новый
                # check if the post is new
                if text_to_send != posts_list[-1]:
                    await bot.send_message(channel, text_to_send)
                    # если да, то пусть заменит собой содержимое листа
                    # if so, make it replace list content
                    posts_list[-1] = text_to_send
                    logger.info(f'SEND TEXT: [{text_to_send}]')
                else:
                    # если пост старый, фиксируем в логер, что постов нет
                    # if the post is old, write about it with the logger
                    logger.info('NO NEWS BY NOW')
                    # ждем 15 минут перед следующей проверкой
                    # check again in 15 min
                    time.sleep(900)

    except Exception as e:
        logger.error(f'SEND POST ERROR: {e}')


bot.run()
