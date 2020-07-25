import sys
import requests

auth_params = {
    'key': "",   # вставте сюда свой ключ
    'token': "", # вставьте сюда свой токен
    }
board_id = ""    # вставьте сюда короткий id доски

base_url = "https://api.trello.com/1/{}"

def check(resp):
    '''
    Функция проверяет результат запроса от requests и если все хорошо,
    то пытается распарсить JSON в ответе и возвращает этот результат
    '''
    if not resp.ok:
        print("ERROR", resp.text, file=sys.stderr)
        sys.exit(1)

    try:
        return resp.json()
    except Exception as e:
        print("ERROR", e, file=sys.stderr)
        sys.exit(1)

######################################
############# api_ функции

def api_all_columns():
    '''
    Возвращает все колонки из доски
    '''
    column_data = check(
            requests.get(base_url.format('boards') + '/' + board_id + '/lists',
                         params=auth_params))
    return column_data

def api_all_tasks(column):
    # Получим данные всех задач в колонке:
    task_data = check(
            requests.get(base_url.format('lists') + '/' + column['id'] + '/cards',
                         params=auth_params))
    return task_data

def api_create_task(column, name):
    # Создадим задачу с именем _name_ в выбранной колонке
    res = check(
        requests.post(base_url.format('cards'),
                      data={'name': name, 'idList': column['id'], **auth_params}))
    return res

def api_move_task(column, task):
    # И выполним запрос к API для перемещения задачи в нужную колонку
    res = check(
        requests.put(base_url.format('cards') + '/' + task['id'] + '/idList',
                     data={'value': column['id'], **auth_params}))
    return res

def api_delete_task(task):
    # И выполним запрос к API для удаления задачи
    res = check(
        requests.delete(base_url.format('cards') + '/' + task['id'],
                     data={**auth_params}))
    return res

def api_create_column(column_name):
    # Создадим колоноку с именем column_name
    res = check(
        requests.post(base_url.format('boards') + '/' + board_id + '/lists',
                      data={'name': column_name, **auth_params}))
    return res

def api_close_column(column):
    # Выполним запрос к API для закрытие (удаление) колонки
    res = check(
        requests.put(base_url.format('lists') + '/' + column['id'] + '/closed',
                     data={'value': 'true', **auth_params}))
    return res

######################################
############# Вспомогательные функции

def select_item(data, name=None):
    '''
    Функция возвращает одни элемент из списка _data_ по выбору пользователя,
    предварительно отфильтровав список по совпадению поля _name_, если _name_ задано
    Если список пуст, то возвращает None
    Если список из одного элемента, то возвращает элемент не спрашивая пользователя
    Применима как для карточек, так и для колонок
    '''
    data_list = data

    # Если задано имя, то выберем только те, что подходят под это имя
    if name:
        data_list = [item for item in data if item['name'] == name]

    if not data_list:
        return None
    elif len(data_list) == 1:
        return data_list[0]
    else:
        for idx, item in enumerate(data_list):
            # Выводим елементы списак с из порядковыми номерами
            item_id = "shortLink: {}".format(item['shortLink']) if 'shortLink' in item \
                    else "id: {}".format(item['id'])
            print("{}) {}, {}".format(idx+1, item['name'], item_id))
        num = None
        while not num:
            try:
                num = int(input("Выберете номер: "))
                if not (0 < num <= len(data_list)):
                    num = None
            except ValueError:
                pass
            if not num:
                print("Некорректное значение")
        return data_list[num-1]

def print_columns(column_data):
    '''
    Выводит на печать задачи колонок из списка _column_data_
    Для каждой из колонок бедет дополнительный запрос на содержимое колонки
    '''
    for column in column_data:
        # Получим данные всех задач в колонке
        task_data = api_all_tasks(column)
        print('{}, tasks: {}, id: {}'.format(
            column['name'], len(task_data), column['id']))
        for task in task_data:
            print('   {}, shortLink: {}'.format(
                task['name'], task['shortLink']))
        print("")

######################################
############# Основные функции команд

def read():
    '''
    Получение и вывод всех колонок с задачами
    '''
    # Получим данные всех колонок на доске:
    column_data = api_all_columns()

    # Теперь выведем название каждой колонки и всех заданий, которые к ней относятся:
    print_columns(column_data)

def create(name, column_name):
    '''
    Создание новой задачи
    '''
    # Получим данные всех колонок на доске
    column_data = api_all_columns()

    # Выберем колонку
    column = select_item(column_data, column_name)
    if not column:
        print("Колонка '{}' не найдена".format(column_name))
        return

    # Создадим задачу с именем _name_ в выбранной колонке
    api_create_task(column, name)
    # Печатаем всю колонку, в которой создали задачу
    print_columns([column])

def move(name, column_name):
    '''
    Перемещение задачи
    '''
    # Получим данные всех колонок на доске
    column_data = api_all_columns()

    # Среди всех колонок нужно найти все задачи по имени
    task_list = []
    for column in column_data:
        column_tasks = api_all_tasks(column)
        task_list.extend([task for task in column_tasks if task['name'] == name])

    # Выберем задачу из составленного списка
    task = select_item(task_list)
    if not task:
        print("Задача '{}' не найдена".format(name))
        return

    # Теперь, когда у нас есть задача, которую мы хотим переместить
    # выберем колонку, в которую мы будем перемещать задачу
    column = select_item(column_data, column_name)
    if not column:
        print("Колонка '{}' не найдена".format(column_name))
        return

    # Перемещаем задачу в выбранную колонку
    api_move_task(column, task)
    # Печатаем всю колонку, в которую переместили
    print_columns([column])

def destroy(name):
    '''
    Удаление задачи
    '''
    # Получим данные всех колонок на доске
    column_data = api_all_columns()

    # Среди всех колонок нужно найти все задачи по имени
    task_list = []
    col_by_task = {} # тут будем хранить колонки по id задачи
    for column in column_data:
        column_tasks = [task for task in api_all_tasks(column) if task['name'] == name]
        for task in column_tasks:
            col_by_task[task['id']] = column
        task_list.extend(column_tasks)

    # Выберем задачу из составленного списка
    task = select_item(task_list)
    if not task:
        print("Задача '{}' не найдена".format(name))
        return

    confirm = input("Удалить задачу? (y/n): ").lower()

    if confirm == 'y':
        # Удаляем задачу
        api_delete_task(task)
        # Печатаем всю колонку, из которой удалили задачу
        print_columns([col_by_task[task['id']]])

def add(column_name):
    '''
    Добавление новой колонки
    '''
    # Создадим колоноку с именем column_name
    column = api_create_column(column_name)
    # Печатаем всю колонку, которую создали
    print_columns([column])

def close(column_name):
    '''
    Закрытие колонки, функционала удаления в сервисе нет
    '''
    # Получим данные всех колонок на доске
    column_data = api_all_columns()

    # Выберем колонку
    column = select_item(column_data, column_name)
    if not column:
        print("Колонка '{}' не найдена".format(column_name))
        return

    confirm = input("Закрыть (удалить) колонку? (y/n): ").lower()

    if confirm == 'y':
        # Удаляем колонку
        api_close_column(column)
        # Печатаем все колонки после удаления
        read()

ATTENTION="""
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!! Для работы скрипта в самом начале кода нужно заполнить   !!
!! вашими значениями переменные:                            !!
!! - auth_params{key, token}                                !!
!! - board_id                                               !!
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
""" if not board_id or not auth_params['key'] or not auth_params['token'] else ""

HELP="""Использовать:
python {prog} [command] [parametr1] [parametr2]
commmand: add, close, create, move, destroy

Если command не задано, то будет вывод всех задач из всех колонок

Добавление колонки
python {prog} add "Новая колонка"

Закрытие (удаление) колонки
python {prog} close "Имя колонки"

Создание новой задачи в существующей колонке
python {prog} create "Новая задача" "Имя колонки"

Перемещение задачи в другую колонку
python {prog} move "Имя задачи" "Имя колонки, куда переместить"

Удаление задачи 
python {prog} destroy "Имя задачи"

""".format(prog=sys.argv[0])

if __name__ == "__main__":
    if ATTENTION:
        print(HELP)
        print(ATTENTION)
    elif len(sys.argv) == 1:
        read()
    elif len(sys.argv) == 2 or sys.argv[1] == 'help':
        print(HELP)
    elif len(sys.argv) == 3:
        if sys.argv[1] == 'destroy':
            destroy(sys.argv[2])
        elif sys.argv[1] == 'add':
            add(sys.argv[2])
        elif sys.argv[1] == 'close':
            close(sys.argv[2])
        else:
            print("Команда " + sys.argv[1]  + " не опознана")
    elif sys.argv[1] == 'create':
        create(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == 'move':
        move(sys.argv[2], sys.argv[3])
    else:
        print("Команда " + sys.argv[1]  + " не опознана")
