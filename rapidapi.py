from typing import Any, List, Optional, Dict
import requests
import re
import datetime
import json

import loader


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
            'x-rapidapi-key': loader.api_key,
            'x-rapidapi-host': "hotels4.p.rapidapi.com"
        }

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

        try:
            response = requests.request("GET", url, headers=self.headers, params=querystring, timeout=15)
        except requests.exceptions.ReadTimeout:
            return

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
                           "currency": "USD", "landmarkIds": "City center"}
            hotels_num = int(self.user_data.get('data')[1])

        else:
            sort_order = "DISTANCE_FROM_LANDMARK"

            price_range = re.findall(r'\d+', self.user_data.get('data')[1])
            price_min = price_range[0]
            price_max = price_range[1]

            hotels_num = int(self.user_data.get('data')[3])

            querystring = {"destinationId": code, "pageNumber": "1", "pageSize": "25", "checkIn": check_in,
                           "checkOut": check_out, "adults1": "1", "sortOrder": sort_order, "locale": "en_US",
                           "currency": "USD", "priceMin": price_min, "priceMax": price_max}

        try:
            response = requests.request("GET", url, headers=self.headers, params=querystring, timeout=15)
        except TimeoutError:
            return

        result_dict = json.loads(response.text)

        try:
            data = result_dict['data']['body']['searchResults']['results']
        except KeyError:
            return

        if len(data) < hotels_num:
            search = data
        else:
            search = data[:hotels_num]

        top_hotels = list(map(lambda hotel: self.hotels_data(hotel), search))

        if not top_hotels:
            return False

        return top_hotels

    def get_hotel_photos(self, hotel_id: str) -> Any:
        """
        Метод запрашивающий URL для каждого фото.
        :param hotel_id:
        :return List:
        """
        url = "https://hotels4.p.rapidapi.com/properties/get-hotel-photos"
        querystring = {"id": hotel_id}

        try:
            response = requests.request("GET", url, headers=self.headers, params=querystring, timeout=10)
        except TimeoutError:
            return
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

            distance_float = float(self.user_data.get('data')[2])
            distance_to_center = float(re.findall(r"[0-9]*[.]?[0-9]+", distance_to_center)[0])
            if distance_to_center <= distance_float:
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
