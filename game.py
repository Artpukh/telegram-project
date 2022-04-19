import logging
from telegram.ext import Updater, MessageHandler, Filters
from random import choice
from googletrans import Translator
# Запускаем логгирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

logger = logging.getLogger(__name__)

TOKEN = '5296805065:AAEwF8fUJQ36bOxG6UdQIbwf4zwcjDxHE0g'
tr = Translator()

# Определяем функцию-обработчик сообщений.
# У неё два параметра, сам бот и класс updater, принявший сообщение.
def game(update, context):
    with open("russian.txt", "r", encoding="utf-8") as file:
        allText = file.readlines()  # список слов типа "слово\n"
        # print(allText[:11], type(allText))
        # for i in range(len(allText)):
        #     allText[i] = allText[i][:-1]
        word = choice(allText[:-1])  # рандомное слово
    update.message.reply_text(f"{word}")
    text = ' '.join(word.args)
    result = tr.translate(text, src='ru', dest='en')
    update.message.reply_text(result.text)


def main():
    # Создаём объект updater.
    # Вместо слова "TOKEN" надо разместить полученный от @BotFather токен
    updater = Updater(TOKEN)

    # Получаем из него диспетчер сообщений.
    dp = updater.dispatcher

    # Создаём обработчик сообщений типа Filters.text
    # из описанной выше функции echo()
    # После регистрации обработчика в диспетчере
    # эта функция будет вызываться при получении сообщения
    # с типом "текст", т. е. текстовых сообщений.
    text_handler = MessageHandler(Filters.text, game)

    # Регистрируем обработчик в диспетчере.
    dp.add_handler(text_handler)
    # Запускаем цикл приема и обработки сообщений.
    updater.start_polling()

    # Ждём завершения приложения.
    # (например, получения сигнала SIG_TERM при нажатии клавиш Ctrl+C)
    updater.idle()


# Запускаем функцию main() в случае запуска скрипта.
if __name__ == '__main__':
    main()