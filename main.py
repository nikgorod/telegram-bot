from loader import bot


@bot.message_handler(commands=['start', 'help', 'lowprice', 'highprice', 'bestdeal', 'history'])
def get_commands(command) -> None:
    """
    Функция для получения команды от пользователя
    и отправки соответствующего сообщения или запроса.

    :param command:
    :return None:
    """
    if command.text == '/start':
        bot.send_message(command.from_user.id, 'Hi! Write /help')

    elif command.text == "/lowprice":
        bot.command_handler(command.from_user.id, 'lowprice')

    elif command.text == '/highprice':
        bot.command_handler(command.from_user.id, 'highprice')

    elif command.text == '/bestdeal':
        bot.command_handler(command.from_user.id, 'bestdeal')

    elif command.text == '/history':
        with open('history.txt', 'r') as file:
            message = file.read()
        bot.send_message(command.from_user.id, message)

    elif command.text == '/help':
        bot.send_message(command.from_user.id, "List of commands:\n"
                                               "/help\n"
                                               "/lowprice (top cheap hotels)\n"
                                               "/highprice (top expensive hotels)\n"
                                               "/bestdeal (top cheap and near with city's center)\n"
                                               "/history (get requests history)")


bot.polling(none_stop=True, interval=0)
