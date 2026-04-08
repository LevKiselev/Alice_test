from flask import Flask, request, jsonify
import logging
from waitress import serve
from random import choice
import json

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

pics = ['1540737/22bc03a0b5c437503ea7', '1540737/00c3849b8c8031529f89', '1540737/32110ea8a8a301156156',
        '1030494/6e74d93d8cb63c838913', '1540737/20b64de5289956963219', '997614/4e6489965e71a1be1f8f',
        '213044/9e5f95f977ae846c2f3c', '1521359/f7f74ecd5d7825cfad63', '1521359/76960f62908e4fbdbd63',
        '937455/a8ad21d2b129d7e1fc8c', '1533899/f10e9edd4032654505b5', '997614/0b930ef41bc6b00fa1cb',
        '937455/560d04e8a9d6cda798ec', '937455/f5fea7c589fc9e8016ec']

# Создадим словарь, чтобы для каждой сессии общения с навыком хранились подсказки, которые видел пользователь.
# Это поможет нам немного разнообразить подсказки ответов (buttons в JSON ответа).
# Когда новый пользователь напишет нашему навыку, то мы сохраним в этот словарь запись формата
# sessionStorage[user_id] = { 'suggests': ["Не хочу.", "Не буду.", "Отстань!" ] }
# Такая запись говорит, что мы показали пользователю эти три подсказки. Когда он откажется купить слона,
# то мы уберем одну подсказку. Как будто что-то меняется :)
sessionStorage = {}

@app.route('/')
# Функция нужна для публикации на replit.com.
# Сервис проверяет работоспособность приложения по ответу на этот запрос
def replit_ping():
        return 'Ok'

@app.route('/post', methods=['POST'])
# Функция получает тело запроса и возвращает ответ.
# Внутри функции доступен request.json - это JSON, который отправила нам Алиса в запросе POST
def main():
    logging.info('Request: %r', request.json)

    # Начинаем формировать ответ, согласно документации
    # мы собираем словарь, который потом при помощи библиотеки json преобразуем в JSON и отдадим Алисе
    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }

    # Отправляем request.json и response в функцию handle_dialog. Она сформирует оставшиеся поля JSON, которые отвечают
    # непосредственно за ведение диалога
    handle_dialog(request.json, response)

    logging.info('Response: %r', request.json)

    return jsonify(response)

def get_first_name(req):
    # перебираем сущности
    for entity in req['request']['nlu']['entities']:
        # находим сущность с типом 'YANDEX.FIO'
        if entity['type'] == 'YANDEX.FIO':
            # Если есть сущность с ключом 'first_name', то возвращаем её значение.
            # Во всех остальных случаях возвращаем None.
            return entity['value'].get('first_name', None)


def handle_dialog(req, res):
    user_id = req['session']['user_id']

    if req['session']['new']:
        # Это новый пользователь.
        # Инициализируем сессию и поприветствуем его.
        # Запишем подсказки, которые мы ему покажем в первый раз

        sessionStorage[user_id] = {
            'suggests': [
                "Не хочу.",
                "Нет.",
                "Отстань!",
            ]
        }
        res['response']['text'] = 'Привет! Назови свое имя!'
        # создаем словарь в который в будущем положим имя пользователя
        sessionStorage[user_id] = {
            'first_name': None
        }
        return

    # если пользователь не новый, то попадаем сюда.
    # если поле имени пустое, то это говорит о том,
    # что пользователь еще не представился.
    if sessionStorage[user_id]['first_name'] is None:
        # в последнем его сообщение ищем имя.
        first_name = get_first_name(req)
        # если не нашли, то сообщаем пользователю что не расслышали.
        if first_name is None:
            res['response']['text'] = 'Не расслышала имя. Повтори, пожалуйста!'
        # если нашли, то приветствуем пользователя.
        # И спрашиваем какой город он хочет увидеть.
        else:
            sessionStorage[user_id]['first_name'] = first_name
            res['response']['text'] = 'Привет, ' + first_name + '. Ты хочешь приехать в Тулу?'
            res['response']['buttons'] = get_suggests(user_id)
            return

    # Сюда дойдем только, если пользователь не новый, и разговор с Алисой уже был начат
    # Обрабатываем ответ пользователя.
    # В req['request']['original_utterance'] лежит весь текст, что нам прислал пользователь
    # Если он написал 'ладно', 'куплю', 'покупаю', 'хорошо', то мы считаем, что пользователь не согласился.
    # Подумайте, все ли в этом фрагменте написано "красиво"?
    if req['request']['original_utterance'].lower() in [
        'ладно',
        'согласен',
        'приеду',
        'хорошо',
        'да',
        'уговорила'
    ]:
        # Пользователь согласился, прощаемся.
        res['response']['text'] = 'Хорошо, ждем тебя в Туле!'
        res['response']['end_session'] = True
        return

    # Если нет, то убеждаем!
    tula_brands = ['ПРЯНИКИ','САМОВАРЫ', 'ТОЛСТОЙ', 'ПАСТИЛА', 'музей оружия']
    res['response']['text'] = f'Тут {choice(tula_brands)}, может все-таки приедешь?'
    # Выводим картинку
    res['response']['card'] = {}
    res['response']['card']['type'] = 'BigImage'
    res['response']['card']['title'] = f'Тут {choice(tula_brands)}, может все-таки приедешь?'
    res['response']['card']['image_id'] = choice(pics)
    # Кнопка
    res['response']['buttons'] = [
        {
            'title': 'Фото-Тула',
            'hide': False,
            'url': 'https://foto-tula.ru/',
        },
        {
            'title': 'Тульский политех',
            'hide': False,
            'url': 'https://tulsu.ru/',
        }
    ]


# Функция возвращает две подсказки для ответа.
def get_suggests(user_id):
    session = sessionStorage[user_id]

    # Выбираем две первые подсказки из массива.
    suggests = [
        {'title': suggest, 'hide': True}
        for suggest in session['suggests'][:2]
    ]

    # Убираем первую подсказку, чтобы подсказки менялись каждый раз.
    session['suggests'] = session['suggests'][1:]
    sessionStorage[user_id] = session

    # Если осталась только одна подсказка, предлагаем подсказку
    # со ссылкой на Яндекс.Маркет.
    if len(suggests) < 2:
        suggests.append({
            "title": "Ладно",
            "url": "https://market.yandex.ru/search?text=Тульский пряник",
            "hide": True
        })

    return suggests


if __name__ == '__main__':
    serve(app, host='0.0.0.0', port=8000)
