from telebot import TeleBot
import os
from dotenv import load_dotenv
import requests
import json
from typing import Any, List, Optional, Dict
import re

load_dotenv()


class Hotel:

    def __init__(self, name: str, address: str, price: str, photos: List[str] = None):
        self.name = name
        self.address = address
        self.price = price
        self.photos = photos

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
            result: List[Optional] = self.top_hotels(destination_id, self.user_data.get('command'))
            return result
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

    def top_hotels(self, code: str, command: str):
        """
        Метод получающий топ отелей из API.
        :param command:
        :param code:
        :return list:
        """
        url = "https://hotels4.p.rapidapi.com/properties/list"

        if command == 'lowprice':
            sort_order = "PRICE"
            querystring = {"destinationId": code, "pageNumber": "1", "pageSize": "25", "checkIn": "2021-08-21",
                           "checkOut": "2021-08-20", "adults1": "1", "sortOrder": sort_order, "locale": "en_US",
                           "currency": "USD"}
            hotels_num = int(self.user_data.get('data')[1])

        elif command == 'highprice':
            sort_order = "PRICE_HIGHEST_FIRST"
            querystring = {"destinationId": code, "pageNumber": "1", "pageSize": "25", "checkIn": "2021-08-21",
                           "checkOut": "2021-08-20", "adults1": "1", "sortOrder": sort_order, "locale": "en_US",
                           "currency": "USD"}
            hotels_num = int(self.user_data.get('data')[1])

        else:
            sort_order = "DISTANCE_FROM_LANDMARK"

            price_range = re.findall(r'\d+', self.user_data.get('data')[1])
            price_min = price_range[0]
            price_max = price_range[1]

            distance_range = re.findall(r'\d+', self.user_data.get('data')[2])
            distance_min = int(distance_range[0])
            distance_max = int(distance_range[1])

            hotels_num = int(self.user_data.get('data')[3])

            querystring = {"destinationId": code, "pageNumber": "1", "pageSize": "25", "checkIn": "2021-08-21",
                           "checkOut": "2021-08-20", "adults1": "1", "sortOrder": sort_order, "locale": "en_US",
                           "currency": "USD", "priceMin": price_min, "priceMax": price_max}

        response = requests.request("GET", url, headers=self.headers, params=querystring)

        result_dict = json.loads(response.text)
        data: List[dict] = result_dict['data']['body']['searchResults']['results']
        top_hotels = list(map(lambda hotel: self.hotels_data(hotel), data[:hotels_num]))
        return top_hotels

    def get_hotel_photos(self, hotel_id: str):
        url = "https://hotels4.p.rapidapi.com/properties/get-hotel-photos"
        querystring = {"id": hotel_id}
        headers = {
            'x-rapidapi-host': "hotels4.p.rapidapi.com",
            'x-rapidapi-key': "d157d36f35msh35f321ab5bcd130p1bea24jsn23c11cbf838e"
        }
        response = requests.request("GET", url, headers=headers, params=querystring)
        photos_num = int(self.user_data.get('data')[2])

        result_dict = json.loads(response.text)
        hotel_images = result_dict.get('hotelImages')
        photos = list(map(lambda hotel: hotel.get('baseUrl'), hotel_images[:photos_num]))

        return photos

    def hotels_data(self, hotel_dict: dict):
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

        if len(self.user_data.get('data')) == 3:
            hotel_id: str = hotel_dict['id']
            photos = self.get_hotel_photos(hotel_id)

            hotel: Optional = Hotel(name, address, price, photos)
        else:
            hotel: Optional = Hotel(name, address, price)

        return hotel


class Bot(TeleBot):

    def lowprice_highprice(self, chat_id: Any, command: str) -> None:
        """
        Метод обрабатывающий команду lowprice, запрашивает данные у пользователя.
        :param command:
        :param chat_id:
        :return None:
        """
        user_data: List[str] = list()

        def get_photos_num(message: Any) -> None:
            """
            Функция принимающая кол-во фото для каждого отеля.
            :param message:
            :return None:
            """
            user_data.append(message.text.lower())
            self.send_message(chat_id=chat_id, text='Выполняется поиск...')
            self.parse(command, user_data, chat_id)

        def get_photos(message: Any):
            """
            Функция обрабатывающая ответ пользователя.
            :param message:
            :return None:
            """

            if message.text.lower() == 'да':
                msg = self.send_message(chat_id=message.from_user.id, text='Введите пожалуйста кол-во фото отеля'
                                                                           '(от 2 до 10):')
                self.register_next_step_handler(msg, get_photos_num)
            else:
                self.send_message(chat_id=chat_id, text='Выполняется поиск...')
                self.parse('lowprice', user_data, chat_id)

        def get_num(message: Any) -> None:
            """
            Функция принимающая кол-во отелей от пользователя
            :param message:
            :return None:
            """
            user_data.append(message.text.lower())
            photo_msg = self.send_message(chat_id=message.from_user.id,
                                          text='Вывести фото для каждого отеля (Да/Нет)?')
            self.register_next_step_handler(photo_msg, get_photos)

        def get_city(message: Any) -> None:
            """
            Функция принимающая город для поиска
            :param message:
            :return None:
            """
            user_data.append(message.text)
            num_msg = self.send_message(chat_id=message.from_user.id, text='Введите пожалуйста кол-во отелей,'
                                                                           ' которые необходимо вывести(не более 23):')
            self.register_next_step_handler(num_msg, get_num)

        city_msg = self.send_message(chat_id=chat_id, text='Введите пожалуйста город(на английском):')
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
            self.output_info(search, chat_id)
            self.send_message(chat_id, "Список команд:\n"
                                       "/help\n"
                                       "/lowprice(топ дешёвых отелей в городе)\n"
                                       "/highprice(топ дорогих отелей в городе)")
        else:
            self.send_message(chat_id, 'Убедитесь в правильности ввода данных!\nПопробуйте еще раз!\n'
                                       '/lowprice\n'
                                       '/highprice')

    def output_info(self, hotels, chat_id: Any):
        """
        Метод выводящий информация пользователю
        :param hotels:
        :param chat_id:
        :return:
        """

        for i_num, i_hotel in enumerate(hotels):
            message = '{num}. {hotel}'.format(num=str(i_num + 1), hotel=i_hotel.output())
            self.send_message(chat_id, message)

            if i_hotel.photos is not None:

                photos_size = list(map(lambda photo: photo.format(size='d'), i_hotel.photos))
                for i_photo in photos_size:
                    self.send_photo(chat_id, i_photo)


my_token = os.getenv('bot_token')
bot = Bot(my_token)


@bot.message_handler(commands=['start', 'help', 'lowprice', 'highprice', 'bestdeal'])
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
        bot.lowprice_highprice(command.from_user.id, 'lowprice')

    elif command.text == '/highprice':
        bot.lowprice_highprice(command.from_user.id, 'highprice')

    elif command.text == '/help':
        bot.send_message(command.from_user.id, "Список команд:\n"
                                               "/help\n"
                                               "/lowprice(топ дешёвых отелей в городе)\n"
                                               "/highprice(топ дорогих отелей в городе)\n"
                                               "/bestdeal(топ дешёвых отелей и близких к центру")


bot.polling(none_stop=True, interval=0)
