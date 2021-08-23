from telebot import TeleBot
import os
from dotenv import load_dotenv
import requests
import json
from typing import Any, List, Optional, Dict

load_dotenv()


class Hotel:

    def __init__(self, name: str, address: str, price: str):
        self.name = name
        self.address = address
        self.price = price

    def output(self):
        """
        Метод формирующий вывод информации по отелю
        :return str:
        """
        text = '{name}\n{address}\n{price}\n'.format(name=self.name, address=self.address, price=self.price)
        return text


class HotelsAPI:
    def __init__(self, command: str, data: list):
        self.user_data = {'command': command, 'data': data}
        self.headers = {
            'x-rapidapi-key': "d157d36f35msh35f321ab5bcd130p1bea24jsn23c11cbf838e",
            'x-rapidapi-host': "hotels4.p.rapidapi.com"
        }

    def get_hotels(self) -> Any:
        """
        Метод обработки информации в зависимости от команды
        :return Any:
        """
        destination_id: str = self.get_destination_id()
        if destination_id:
            if self.user_data.get('command') == 'lowprice':
                result: List[Optional] = self.top_hotels(destination_id)
                message = self.output(result)
                return message
        else:
            return False

    def get_destination_id(self) -> Any:
        """
        Метод получающий id города, в котором проводится поиск
        :return str:
        """
        url = "https://hotels4.p.rapidapi.com/locations/search"

        city: str = self.user_data.get('data')[0].title()

        querystring = {"query": city, "locale": "en_US"}

        response = requests.request("GET", url, headers=self.headers, params=querystring)

        city_dict: Dict = json.loads(response.text)
        suggestions = city_dict.get('suggestions')

        city_group = list(filter(lambda suggestion: suggestion['group'] == 'CITY_GROUP', suggestions))
        entity = list(filter(lambda x: x['name'].startswith(city),
                             city_group[0]['entities']))

        try:
            destination_id: str = entity[0]['destinationId']
        except IndexError:
            return False
        return destination_id

    def top_hotels(self, code: str):
        """
        Метод получающий топ отелей из API
        :param code:
        :return list:
        """
        url = "https://hotels4.p.rapidapi.com/properties/list"

        querystring = {"destinationId": code, "pageNumber": "1", "pageSize": "25", "checkIn": "2021-08-21",
                       "checkOut": "2021-08-20", "adults1": "1", "sortOrder": "PRICE", "locale": "en_US",
                       "currency": "USD"}

        response = requests.request("GET", url, headers=self.headers, params=querystring)

        result_dict = json.loads(response.text)
        data: List[dict] = result_dict['data']['body']['searchResults']['results']
        hotels_num = int(self.user_data.get('data')[1])
        top_hotels = list(map(lambda hotel: self.hotels_data(hotel), data[:hotels_num]))

        return top_hotels

    @classmethod
    def hotels_data(cls, hotel_dict: dict):
        """
        Метод создающий instance класса Hotel
        :param hotel_dict:
        :return Optional:
        """

        name: str = hotel_dict['name']
        try:
            address: str = hotel_dict['address']['streetAddress']
        except KeyError:
            address: str = hotel_dict['address']['locality']
        price: str = hotel_dict['ratePlan']['price']['current']

        hotel: Optional = Hotel(name, address, price)

        return hotel

    @classmethod
    def output(cls, hotels_list: list):
        """
        Формирование информации по всем отелям
        :param hotels_list:
        :return str:
        """
        message = ''
        for i_num, i_hotel in enumerate(hotels_list):
            info = i_hotel.output()
            message += '{num}. {info}\n'.format(num=i_num + 1, info=info)
        return message


class Bot(TeleBot):

    def lowprice(self, chat_id: Any) -> None:
        """
        Метод обрабатывающий команду lowprice, запрашивает данные у пользователя.
        :param chat_id:
        :return None:
        """
        user_data: List[str] = list()

        def get_num(message: Any) -> None:
            """
            Функция принимающая кол-во отелей от пользователя
            :param message:
            :return None:
            """
            user_data.append(message.text.lower())
            self.parse('lowprice', user_data, chat_id)

        def get_city(message: Any) -> None:
            """
            Функция принимающая город для поиска
            :param message:
            :return None:
            """
            user_data.append(message.text)
            num_msg = self.send_message(chat_id=message.from_user.id, text='Введите пожалуйста кол-во отелей,'
                                                                           ' которые необходимо вывести(не более 25):')
            self.register_next_step_handler(num_msg, get_num)

        city_msg = self.send_message(chat_id=chat_id, text='Введите пожалуйста город:')
        self.register_next_step_handler(city_msg, get_city)

    def parse(self, command: str, data: List[str], chat_id: Any) -> None:
        """
        Метод создающий объект класса HotelsApi, запрашивает инфоррмацию по отелям
        :param command:
        :param data:
        :param chat_id:
        :return None:
        """
        instance: Optional = HotelsAPI(command, data)
        search: Optional = instance.get_hotels()
        if search:
            self.send_message(chat_id, str(search))
        else:
            self.send_message(chat_id, 'Убедитесь в правильности ввода данных!\nПопробуйте еще раз!\n'
                                       '/lowprice')


my_token = os.getenv('bot_token')
bot = Bot(my_token)


@bot.message_handler(commands=['start', 'help', 'lowprice'])
def get_commands(command) -> None:
    """
    Функция для получения команды от пользователя
    и отправки соответствующего сообщения или запроса.

    :param command:
    :return None:
    """
    if command.text == '/start':
        bot.send_message(command.from_user.id, 'Привет! Напиши /help')

    elif command.text == "/lowprice":
        bot.lowprice(command.from_user.id)

    elif command.text == '/help':
        bot.send_message(command.from_user.id, "Список команд:\n"
                                               "/help\n"
                                               "/lowprice(топ дешёвых отелей в городе)")


bot.polling(none_stop=True, interval=0)
