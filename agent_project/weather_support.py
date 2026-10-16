"""Given helpers for the real-weather exercise, exported as practice.weather_support."""
import csv
from pathlib import Path
from dotenv import dotenv_values

WEATHER_URL = 'https://eolink.o.apispace.com/456456/weather/v001/now'


def load_weather_config():
    values = dotenv_values('.env', interpolate=False)
    key = (values.get('WEATHER_API_KEY') or '').strip()
    if not key:
        raise ValueError('请在 .env 中填写 WEATHER_API_KEY。天气工具不需要模型密钥。')
    return {'api_key': key, 'url': values.get('WEATHER_API_URL') or WEATHER_URL}


def get_city_code(city):
    if not isinstance(city, str) or not city.strip():
        raise ValueError('城市名称不能为空')
    def normalize(value):
        for suffix in ('市', '区', '县'):
            value = value.removesuffix(suffix)
        return value
    name = normalize(city.strip())
    with Path(__file__).with_name('weather_cities.csv').open(encoding='utf-8', newline='') as handle:
        rows = list(csv.DictReader(handle))
    matches = {row['areacode'] for row in rows
               if name in {normalize(row['district']), row['city'] + normalize(row['district']),
                           row['city'] + '市' + normalize(row['district'])}}
    if not matches:
        raise ValueError(f'找不到城市“{city}”，请使用城市或区县全名')
    if len(matches) > 1:
        raise ValueError(f'“{city}”存在重名，请在区县名前加上城市名')
    return matches.pop()
