from datetime import datetime
import random

def translit_to_eng(s: str) -> str:
    d = {'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd',
         'е': 'e', 'ё': 'yo', 'ж': 'zh', 'з': 'z', 'и': 'i','й': 'iy', 'к': 'k',
         'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r',
         'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'h', 'ц': 'c', 'ч': 'ch',
         'ш': 'sh', 'щ': 'shch', 'ь': 'i', 'ы': 'y', 'ъ': 'i', 'э': 'r', 'ю': 'yu', 'я': 'ya'}

    return "".join(map(lambda x: d[x] if d.get(x, False) else x, s.lower()))


def create_acronym(phrase: str) -> str:
    """
    Создает аббревиатуру из первых букв слов в строке.

    Args:
        phrase: Входная строка со словами.

    Returns:
        Строка, представляющая собой аббревиатуру в верхнем регистре.
        Возвращает пустую строку, если входная строка пуста или не содержит слов.
    """
    if not phrase:
        return ""

    words = phrase.split()  # Разделяем строку на слова по пробелам
    if not words: # Если после split список слов пуст (например, строка из одних пробелов)
        return ""

    acronym = ""
    for word in words:
        if word:  # Убедимся, что слово не пустое (на случай нескольких пробелов подряд)
            acronym += word[0].upper()  # Берем первую букву и переводим в верхний регистр
    return acronym

def make_smart_raion(raion):

    if raion.find("район") > -1:
        smartraion = raion.replace("район ","")
        smartraion = smartraion.replace(" район", "")
        smartraion = "р-н " + smartraion
    else:
        smartraion = raion

    return smartraion

def get_intdate_from_string(string_date):
    date_out = datetime.strptime(string_date, '%d.%m.%Y').toordinal()
    # print(date_out)
    return  date_out

def get_isodate_from_string(string_date):
    string_date = string_date.replace(' 0:00:00','')
    dateobject =  datetime.strptime(string_date, '%d.%m.%Y')
    date_out = dateobject.strftime('%Y-%m-%d')
    # print(date_out)
    return  date_out

def get_date_from_iso(string_date):
    dateobject =  datetime.strptime(string_date, '%Y-%m-%d')
    date_out = dateobject.strftime('%d.%m.%Y')
    # print(date_out)
    return  date_out

def rnd_time( mint = 2 , maxt = 7):
    return random.random()*(maxt-mint)+mint



def main():
    x = get_intdate_from_string("01.02.2024").toordinal() - get_intdate_from_string("01.01.2024").toordinal()
    print(x)


if __name__ == '__main__':
    main()
