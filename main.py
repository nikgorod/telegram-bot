from telebot import TeleBot
import os
from dotenv import load_dotenv
import requests
import json
from typing import Any, List, Optional, Dict
import re
import datetime


load_dotenv()


class Hotel:

    def __init__(self, name: str, address: str, price: str, center_distance: str, photos: List[str] = None):
        self.name = name
        self.address = address
        self.price = price
        self.photos = photos
        self.center_distance = center_distance

    def output(self) -> str:
        """
        Метод формирующий вывод информации по отелю
        :return str:
        """
        text = '{name}\nAddress: {address}\nPrice: {price}\nTo center: {dist}\n'.format(name=self.name,
                                                                                        address=self.address,
                                                                                        price=self.price,
                                                                                        dist=self.center_distance)
        return text


class HotelsAPI:
    def __init__(self, command: str, data: list):
        self.user_data = {'command': command, 'data': data}
        self.headers = {
            'x-rapidapi-key': "d157d36f35msh35f321ab5bcd130p1bea24jsn23c11cbf838e",
            'x-rapidapi-host': "hotels4.p.rapidapi.com"
        }
        self.query = list()

    def get_hotels(self) -> Any:
        """
        Метод возвращающий топ отелей в зависимости от команды.
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

        check_in = datetime.datetime.today().strftime("%Y-%m-%d")
        check_out = (datetime.datetime.today() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")

        if command == 'lowprice':
            sort_order = "PRICE"
            querystring = {"destinationId": code, "pageNumber": "1", "pageSize": "25", "checkIn": check_in,
                           "checkOut": check_out, "adults1": "1", "sortOrder": sort_order, "locale": "en_US",
                           "currency": "USD"}
            hotels_num = int(self.user_data.get('data')[1])

        elif command == 'highprice':
            sort_order = "PRICE_HIGHEST_FIRST"
            querystring = {"destinationId": code, "pageNumber": "1", "pageSize": "25", "checkIn": check_in,
                           "checkOut": check_out, "adults1": "1", "sortOrder": sort_order, "locale": "en_US",
                           "currency": "USD"}
            hotels_num = int(self.user_data.get('data')[1])

        else:
            sort_order = "DISTANCE_FROM_LANDMARK"

            price_range = re.findall(r'\d+', self.user_data.get('data')[1])
            price_min = price_range[0]
            price_max = price_range[1]

            distance_range = re.findall(r'[0-9]*[.]?[0-9]', self.user_data.get('data')[2])

            distance_min = float(distance_range[0])
            distance_max = float(distance_range[1])

            self.query.append(distance_min)
            self.query.append(distance_max)

            hotels_num = int(self.user_data.get('data')[3])

            querystring = {"destinationId": code, "pageNumber": "1", "pageSize": "25", "checkIn": check_in,
                           "checkOut": check_out, "adults1": "1", "sortOrder": sort_order, "locale": "en_US",
                           "currency": "USD", "priceMin": price_min, "priceMax": price_max}

        response = requests.request("GET", url, headers=self.headers, params=querystring)

        result_dict = json.loads(response.text)

        data = result_dict['data']['body']['searchResults']['results']
        if len(data) < hotels_num:
            search = data
        else:
            search = data[:hotels_num]

        top_hotels = list(map(lambda hotel: self.hotels_data(hotel), search))

        if not top_hotels:
            return False

        return top_hotels

    def get_hotel_photos(self, hotel_id: str) -> List[str]:
        """
        Метод запрашивающий URL для каждого фото.
        :param hotel_id:
        :return List:
        """
        url = "https://hotels4.p.rapidapi.com/properties/get-hotel-photos"
        querystring = {"id": hotel_id}
        headers = {
            'x-rapidapi-host': "hotels4.p.rapidapi.com",
            'x-rapidapi-key': "d157d36f35msh35f321ab5bcd130p1bea24jsn23c11cbf838e"
        }
        response = requests.request("GET", url, headers=headers, params=querystring)
        if self.user_data.get('command') == 'bestdeal':
            photos_num = int(self.user_data.get('data')[4])
        else:
            photos_num = int(self.user_data.get('data')[2])

        result_dict = json.loads(response.text)
        hotel_images = result_dict.get('hotelImages')
        photos = list(map(lambda hotel: hotel.get('baseUrl'), hotel_images[:photos_num]))

        return photos

    def hotels_data(self, hotel_dict: dict) -> Optional:
        """
        Метод создающий instance класса Hotel
        :param hotel_dict:
        :return Optional:
        """

        def check_distance(distance_to_center: str) -> bool:

            real_distance_float = float((re.findall(r"[0-9]*[.]?[0-9]+", distance_to_center)[0]))
            if self.query[0] <= real_distance_float <= self.query[1]:
                return True

        distance = hotel_dict.get("landmarks")[0].get('distance')

        if self.user_data.get('command') == 'bestdeal':
            if not check_distance(distance):
                return

        name: str = hotel_dict['name']
        try:
            address: str = hotel_dict['address']['streetAddress']
        except KeyError:
            address: str = hotel_dict['address']['locality']
        price: str = hotel_dict['ratePlan']['price']['current']

        if len(self.user_data.get('data')) == 3 or len(self.user_data.get('data')) == 5:
            hotel_id: str = hotel_dict['id']
            photos = self.get_hotel_photos(hotel_id)

            hotel: Optional = Hotel(name, address, price, distance, photos)
        else:
            hotel: Optional = Hotel(name, address, price, distance)

        return hotel


class Bot(TeleBot):

    def command_handler(self, chat_id: Any, command: str) -> None:
        """
        Метод обрабатывающий команды lowprice, highprice, bestdeal запрашивает данные у пользователя.
        :param command:
        :param chat_id:
        :return None:
        """
        user_data: List[str] = list()

        with open('history.txt', 'a') as file:
            text = '\nCommand: {command}\nDatetime: {time}\n'.format(command=command,
                                                                     time=datetime.datetime.today().strftime(
                                                                         "%d.%m.%Y %H:%M:%S"))
            file.write(text)

        def get_distance(message: Any) -> None:
            """
            Функция принимающая диапазон расстояния для поиска.
            :param message:
            :return:
            """
            if not re.findall(r'[0-9]*[.]?[0-9]', message.text):
                self.send_message(chat_id=message.from_user.id, text='Неверный ввод данных!!!')
                return
            user_data.append(message.text)
            num_msg = self.send_message(chat_id=message.from_user.id, text='Введите, пожалуйста, кол-во отелей, '
                                                                           'которые необходимо вывести'
                                                                           '(не более 23):')
            self.register_next_step_handler(num_msg, get_num)

        def get_price(message: Any) -> None:
            """
            Функция принимающая диапазон цен для поиска.
            :param message:
            :return:
            """
            if not re.findall(r'\d+', message.text):
                self.send_message(chat_id=message.from_user.id, text='Неверный ввод данных!!!')
                return
            user_data.append(message.text)
            msg = self.send_message(chat_id=message.from_user.id, text='Введите, пожалуйста, '
                                                                       'диапазон расстояния в милях, на котором '
                                                                       'находится '
                                                                       'отель от центра. '
                                                                       '(через -):')
            self.register_next_step_handler(msg, get_distance)

        def get_photos_num(message: Any) -> None:
            """
            Функция принимающая кол-во фото для каждого отеля.
            :param message:
            :return None:
            """
            try:
                int(message.text)
            except ValueError:
                self.send_message(chat_id=message.from_user.id, text='Неверный ввод данных!!!')
                return
            user_data.append(message.text.lower())
            self.send_message(chat_id=chat_id, text='Выполняется поиск...')
            self.parse(command, user_data, chat_id)

        def get_photos(message: Any) -> None:
            """
            Функция обрабатывающая ответ пользователя.
            :param message:
            :return None:
            """

            if message.text.lower() == 'да':
                msg = self.send_message(chat_id=message.from_user.id, text='Введите пожалуйста кол-во фото отеля:')
                self.register_next_step_handler(msg, get_photos_num)

            elif message.text.lower() == 'нет':
                self.send_message(chat_id=chat_id, text='Выполняется поиск...')
                self.parse(command, user_data, chat_id)

            else:
                self.send_message(chat_id=message.from_user.id, text='Неверный ввод данных!!!')
                return

        def get_num(message: Any) -> None:
            """
            Функция принимающая кол-во отелей от пользователя.
            :param message:
            :return None:
            """
            try:
                int(message.text)
            except ValueError:
                self.send_message(chat_id=message.from_user.id, text='Неверный ввод данных!!!')
                return
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

            if command == 'bestdeal':
                msg = self.send_message(chat_id=message.from_user.id, text='Введите, пожалуйста, '
                                                                           'диапазон цен в $ (через -):')
                self.register_next_step_handler(msg, get_price)
            else:
                num_msg = self.send_message(chat_id=message.from_user.id, text='Введите, пожалуйста, кол-во отелей, '
                                                                               'которые необходимо вывести\n'
                                                                               '(не более 23):')
                self.register_next_step_handler(num_msg, get_num)

        city_msg = self.send_message(chat_id=chat_id, text='Введите пожалуйста город\n(на английском):')
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
                                       "/highprice(топ дорогих отелей в городе)\n"
                                       "/bestdeal (топ дешёвых и близких отелей к центру)\n"
                                       "/history (история запросов)")
        else:
            self.send_message(chat_id, 'К сожалению, ничего не удалось найти!\nПопробуйте еще раз!\n'
                                       '/lowprice\n'
                                       '/highprice\n'
                                       '/bestdeal\n'
                                       '/history')

    def output_info(self, hotels: list, chat_id: Any) -> None:
        """
        Метод выводящий информацию пользователю
        :param hotels:
        :param chat_id:
        :return None:
        """
        text = str()
        for i_num, i_hotel in enumerate(hotels):
            if i_hotel is None:
                self.send_message(chat_id, 'По запрашиваемым данным ничего не найдено!\n'
                                           'Попробуйте изменить параметры запроса')
                return
            message = '{num}. {hotel}'.format(num=str(i_num + 1), hotel=i_hotel.output())
            text += message
            self.send_message(chat_id, message)

            if i_hotel.photos is not None:

                photos_size = list(map(lambda photo: photo.format(size='d'), i_hotel.photos))
                for i_photo in photos_size:
                    self.send_photo(chat_id, i_photo)
        with open('history.txt', 'a') as file:
            try:
                file.write(text)
            except UnicodeEncodeError:
                file.write('EncodeError\n')


my_token = os.getenv('bot_token')
bot = Bot(my_token)


@bot.message_handler(commands=['start', 'help', 'lowprice', 'highprice', 'bestdeal', 'history'])
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
        bot.send_message(command.from_user.id, "Список команд:\n"
                                               "/help\n"
                                               "/lowprice (топ дешёвых отелей в городе)\n"
                                               "/highprice (топ дорогих отелей в городе)\n"
                                               "/bestdeal (топ дешёвых и близких отелей к центру)\n"
                                               "/history (история запросов)")


bot.polling(none_stop=True, interval=0)
