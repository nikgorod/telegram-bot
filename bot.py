from telebot import TeleBot
from typing import Any, List, Optional
import datetime
import re
from rapidapi import HotelsAPI


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
                self.send_message(chat_id=message.from_user.id, text='Incorrect data entry!!!')
                return
            user_data.append(message.text)
            num_msg = self.send_message(chat_id=message.from_user.id, text='Please enter the number of hotels, '
                                                                           'that you need to output\n'
                                                                           '(no more than 23):')
            self.register_next_step_handler(num_msg, get_num)

        def get_price(message: Any) -> None:
            """
            Функция принимающая диапазон цен для поиска.
            :param message:
            :return:
            """
            if not re.findall(r'\d+', message.text):
                self.send_message(chat_id=message.from_user.id, text='Incorrect data entry!!!')
                return
            user_data.append(message.text)
            msg = self.send_message(chat_id=message.from_user.id, text='Please enter '
                                                                       'the range of the distance in miles at which '
                                                                       'located '
                                                                       'hotel from the center:')
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
                self.send_message(chat_id=message.from_user.id, text='Incorrect data entry!!!')
                return
            user_data.append(message.text.lower())
            self.send_message(chat_id=chat_id, text='Searching...')
            self.parse(command, user_data, chat_id)

        def get_photos(message: Any) -> None:
            """
            Функция обрабатывающая ответ пользователя.
            :param message:
            :return None:
            """

            if message.text.lower() == 'yes':
                msg = self.send_message(chat_id=message.from_user.id, text='Please enter the number '
                                                                           'of photos of the hotel:')
                self.register_next_step_handler(msg, get_photos_num)

            elif message.text.lower() == 'no':
                self.send_message(chat_id=chat_id, text='Searching...')
                self.parse(command, user_data, chat_id)

            else:
                self.send_message(chat_id=message.from_user.id, text='Incorrect data entry!!!')
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
                self.send_message(chat_id=message.from_user.id, text='Incorrect data entry!!!')
                return
            user_data.append(message.text.lower())
            photo_msg = self.send_message(chat_id=message.from_user.id,
                                          text='Output a photo for each hotel\n(Yes/No)?')
            self.register_next_step_handler(photo_msg, get_photos)

        def get_city(message: Any) -> None:
            """
            Функция принимающая город для поиска
            :param message:
            :return None:
            """

            user_data.append(message.text)

            if command == 'bestdeal':
                msg = self.send_message(chat_id=message.from_user.id, text='Please enter the price range '
                                                                           'in $ (via -):')
                self.register_next_step_handler(msg, get_price)
            else:
                num_msg = self.send_message(chat_id=message.from_user.id, text='Please enter the number of hotels, '
                                                                               'that you need to output\n'
                                                                               '(no more than 23):')
                self.register_next_step_handler(num_msg, get_num)

        city_msg = self.send_message(chat_id=chat_id, text='Enter the city please:')
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
            self.send_message(chat_id, "List of commands:\n"
                                       "/help\n"
                                       "/lowprice (top cheap hotels)\n"
                                       "/highprice (top expensive hotels)\n"
                                       "/bestdeal (top cheap and near with city's center)\n"
                                       "/history (get requests history)")
        else:
            self.send_message(chat_id, 'Unfortunately, nothing could be found!\nTry again!\n'
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
                self.send_message(chat_id, 'By the requested, was found {num} hotels!\n'
                                           'Try to change parameters'.format(num=i_num))
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
