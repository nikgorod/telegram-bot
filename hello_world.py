import telebot

bot = telebot.TeleBot('1945615025:AAG-rdqoMMybxj4fzFdbFov2mOUNUptvNJ0')


@bot.message_handler(content_types=['text'])
def get_text_messages(message) -> None:

    """
    Функция для получения сообщения от пользователя
    и отправки соответствующего сообщения.

    :param message:
    :return None:
    """

    if message.text == "Привет":
        bot.send_message(message.from_user.id, "Привет, чем я могу тебе помочь?")
    elif message.text == "/hello_world":
        bot.send_message(message.from_user.id, "Привет Мир!")
    elif message.text == '/help':
        bot.send_message(message.from_user.id, "Напиши Привет\nСписок команд:\n/hello_world")
    else:
        bot.send_message(message.from_user.id, "Я тебя не понимаю. Напиши /help.")


bot.polling(none_stop=True, interval=0)
