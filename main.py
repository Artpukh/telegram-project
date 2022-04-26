from googletrans import Translator
from db_session import *
import logging
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler, ConversationHandler, CallbackContext
from telegram import ReplyKeyboardMarkup, Update
from Users import User
from Words import Word
import os
import schedule
from swift import words
from random import choice
import datetime

symbs = words

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)

logger = logging.getLogger(__name__)

# токен тг-бота
TOKEN = '5296805065:AAEwF8fUJQ36bOxG6UdQIbwf4zwcjDxHE0g'
current_name = None
current_id = None

# виртуальная клавиатура
reply_keyboard = [['/start', '/help', "/reg"],
                  ['/enter', '/translate', "/translate_file"],
                  ["/game", "/unset"]]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
tr = Translator()

# обработка файла в список
res = ""
lst_words = []
with open("russian.txt", "r", encoding="utf-8") as file:
    allText = file.readlines()  # список слов типа "слово\n"
    for i in allText:
        lst_words.append(i[:-1])
    file.close()


# запуск бота
def start(update, context):
    update.message.reply_text(f"Используйте комманды '/reg <никнейм>' для регистрации и '/enter <никнейм>' для входа")


# памятка об использовании команд тг-бота
def help(update, context):
    update.message.reply_text(
        "RU\n"
        "Привет! Это бот-переводчик!\n"
        "Мои возможномти:\n"
        "/reg - мы настоятельно рекомендуем вам зарегестрироваться, для регистрации нужно только придумать никнейм;\n"
        "сообщение пользователя должно выглядеть так: '/reg <никнейм>'\n"
        "/enter - вход в учётную запись;\n"
        "сообщение пользователя должно выглядеть так: '/enter <никнейм>'\n"
        "/translate - перевод слова или выражения с английского на русский и наоборот;\n"
        "/translate_file - перевод содержимого файла, возвращает файл с переводом;\n"
        "/translate_from_file - бот с выбранной периодчностью будет давать перевод слова из отправленного файла;\n"
        "/game - игра: бот загадывает слово, пользователь даёт перевод;\n"
        "/send_words <время> - время, в которое каждый день будет приходить слово\n"
        "/unset - убрать таймер"
        "\n"
        "\n"
        "ENG\n"
        "Hello! This is a translate bot\n"
        "/reg - we strongly recommend you to register, you only need to come up with a nickname to register;\n"
        "the user's message should look like this: \n"
        "'/reg <nickname>'\n"
        "/enter - login to your account;\n"
        "the user's message should look like this: \n"
        "'/enter <nickname>'\n"
        "/translate - translation of a word or expression from English to Russian and vice versa;\n"
        "/translate_file - translation of the file contents, returns a file with translation;\n"
        "/translate_from_file - the bot with the selected frequency will translate the word from the sent file;\n"
        "/game - game: the bot makes a word, the user gives a translation;\n"
        "/send_words <time> - the time at which the word will come every day\n"
        "/unset - remove the timer"
    )


# регистрация аккаунта (внесение его данный в БД)
def reg(update, context):
    global current_name, current_id
    name = ' '.join(context.args)
    print(name)
    user = User()
    user.nickname = name
    db_sess = create_session()
    look = db_sess.query(User).filter(User.nickname == name).first()
    if name == "" or name == " ":
        update.message.reply_text('Никнейм не должен быть пустым')
    elif look:
        update.message.reply_text('Такая учётная запись уже существует')
    else:
        db_sess.add(user)
        db_sess.commit()
        update.message.reply_text('Поздравляю! Вы успешно прошли регистрацию')
        current_name = name
        current_id = user.id


# вход в аккаунт
def enter(update, context):
    reply_keyboard = [['/start', '/help', "/reg"],
                      ['/enter', '/translate', "/translate_file"],
                      ["/game", "/unset"]]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
    global current_name, current_id
    name = ' '.join(context.args)
    db_sess = create_session()
    user = db_sess.query(User).filter(User.nickname == name).first()
    if user:
        current_name = user.nickname
        current_id = user.id
        update.message.reply_text('Вы вошли в свой аккаунт', reply_markup=markup)
    else:
        update.message.reply_text('Такой учётной записи не существует')


# точка запуска сценария диалога переводчика
# переводчик
def translate(update, context):
    reply_keyboard = [["/stop_tr"]]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
    update.message.reply_text('Введите текст', reply_markup=markup)
    return 1


# обработчик сценария диалога переводчика
# перевод фразы, введённой пользователем, с русского на английский и наоборот
def translation(update, context):
    global reply_keyboard
    reply_keyboard = [['/stop_tr']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
    text = update.message.text
    if text == '/stop_tr':
        reply_keyboard = [['/start', '/help', "/reg"],
                          ['/enter', '/translate', "/translate_file"],
                          ["/game", "/unset"]]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
        update.message.reply_text('Всего доброго', reply_markup=markup)
        return ConversationHandler.END
    if tr.detect(text).lang == 'en':
        result = tr.translate(text, dest='ru')
    else:
        result = tr.translate(text, dest='en')
    update.message.reply_text(result.text, reply_markup=markup)
    return 1


# точка остановки сценария диалога переводчика
def stop_tr(update, context):
    update.message.reply_text('Всего доброго')
    return ConversationHandler.END


# точка запуска сценария диалога переводчика файла
def translate_file(update, context):
    reply_keyboard = [["/stop_fl"]]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
    update.message.reply_text('Отправьте файл', reply_markup=markup)
    return 1


# обработчик файла
# открывает файл переводит содержимое текста и зменяет содержимое файла
def translation_file(update, context):
    with open(update.message.document.file_name, mode='wb') as f:
        context.bot.get_file(update.message.document).download(out=f)
    with open(update.message.document.file_name, encoding='utf-8', mode='r') as f:
        content = f.read()
        print(content)
    if tr.detect(content).lang == 'en':
        result = tr.translate(content, dest='ru')
        with open(update.message.document.file_name, encoding='utf-8', mode='w') as f:
            f.write(result.text)
    else:
        result = tr.translate(content, dest='en')
        with open(update.message.document.file_name, encoding='utf-8', mode='w') as f:
            f.write(result.text)
    context.bot.send_document(chat_id=update.message.chat_id,
                              document=open(f'{update.message.document.file_name}', mode='rb'))
    os.remove(update.message.document.file_name)
    return ConversationHandler.END


# точка остановки сценария диалога переводчика файла
def stop_fl(update, context):
    reply_keyboard = [['/start', '/help', "/reg"],
                      ['/enter', '/translate', "/translate_file"],
                      ["/game", "/unset"]]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
    update.message.reply_text(f"Всего хорошего", reply_markup=markup)
    return ConversationHandler.END


# игра представляет собой следущее:
# программа выбирает случайное слово из списка allText
# выводит это слово и предлагает пользователю его перевести на английский
# после получения обратной связи тг-бот сравнивает сообщение пользователя и фактический перевод
# после обработки выводит соответствующее сообщение
# точка запуска сценария диалога "игры"
def start_game(update, context):
    global allText, res
    word = choice(lst_words)  # рандомное слово
    res = word
    update.message.reply_text(f"Переведи слово: {word}")
    return 1


# игра представляет собой следущее:
# программа выбирает случайное слово из списка allText
# выводит это слово и предлагает пользователю его перевести на английский
# после получения обратной связи тг-бот сравнивает сообщение пользователя и фактический перевод
# после обработки выводит соответствующее сообщение
# точка запуска сценария диалога "игры"
def game(update, context):
    global allText, res
    word = choice(allText[:-1])  # рандомное слово
    res = word
    reply_keyboard = [["/stop_game"]]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
    update.message.reply_text(f"Переведи слово: {word}", reply_markup=markup)
    return 1


# реализация "игры"
def time_game(update, context):
    global res
    text = update.message.text
    transl = tr.translate(res, dest="en")
    reply_keyboard = [["/game"]]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
    if text == "/stop_game":
        reply_keyboard = [['/start', '/help', "/reg"],
                          ['/enter', '/translate', "/translate_file"],
                          ["/game", "/unset"]]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
        update.message.reply_text('Всего доброго', reply_markup=markup)
        return ConversationHandler.END
    if text.lower() == transl.text.lower():
        update.message.reply_text('Поздравляю! Ты правильно написал перевод.\n'
                                  'Для продолжения нажмите "/game"', reply_markup=markup)
        return ConversationHandler.END
    if text == "yandex":
        update.message.reply_text('Привет из Яндекс Лицея 2021-2022 \U0001F44B',
                                  reply_markup=markup)
        return ConversationHandler.END
    
    else:
        update.message.reply_text(f'К сожалению, ты ошибся. Перевод твоего слова - {tr.translate(text, dest="ru").text}'
                                  f'\n'
                                  f'Правильно: {transl.text}. Попробуем другое слово.\n'
                                  f'Для продолжения нажмите "/game"', reply_markup=markup)
        return ConversationHandler.END


# точка остановки сценария диалога "игры"
def stop_game(update, context):
    update.message.reply_text('Всего доброго')
    return ConversationHandler.END


def remove_job_if_exists(name, context):
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


def job(context: CallbackContext):
    word = ''
    slova = Word()
    db_sess = create_session()
    spis = []
    for a in db_sess.query(Word).filter(Word.user_id == current_id):
        spis.append(a.words)
    while len(word) < 2 and word in spis:
        word = choice(symbs)
    slova.user_id = current_id
    slova.words = word
    db_sess.add(slova)
    db_sess.commit()
    word = tr.translate(word, dest='en')
    context.bot.send_message(chat_id=context.job.context, text=word.text)


def send_words(update: Update, context: CallbackContext):
    due = context.args[0].split(':')

    context.job_queue.run_daily(job, time=datetime.time(hour=int(due[0]) - 3, minute=int(due[1]), second=00),
                                days=(0, 1, 2, 3, 4, 5, 6),
                                context=update.message.chat_id)


def unset(update, context):
    chat_id = update.message.chat_id
    job_removed = remove_job_if_exists(str(chat_id), context)
    text = 'Таймер успешно отменён' if job_removed else 'Нет активных таймеров.'
    update.message.reply_text(text)


# главная функция, в которой регистрируются обраотчики в диспетчере
def main():
    global_init("accounts.db")

    updater = Updater(TOKEN, use_context=True)

    dp = updater.dispatcher
    jq = updater.job_queue

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))

    tr_conv = ConversationHandler(
        entry_points=[CommandHandler('translate', translate)],

        # Состояние внутри диалога.
        # Вариант с двумя обработчиками, фильтрующими текстовые сообщения.
        states={
            # Функция читает ответ на первый вопрос и задаёт второй.
            1: [MessageHandler(Filters.text, translation)]
        },

        # Точка прерывания диалога. В данном случае — команда /stop.
        fallbacks=[CommandHandler('stop_tr', stop_tr)]
    )

    game_conv = ConversationHandler(
        entry_points=[CommandHandler('game', game)],

        # Состояние внутри диалога.
        # Вариант с двумя обработчиками, фильтрующими текстовые сообщения.
        states={
            # Функция читает ответ на первый вопрос и задаёт второй.
            1: [MessageHandler(Filters.text, time_game)]
        },

        # Точка прерывания диалога. В данном случае — команда /stop.
        fallbacks=[CommandHandler('stop_game', stop_game)]
    )

    file_conv = ConversationHandler(
        entry_points=[CommandHandler('translate_file', translate_file)],

        # Состояние внутри диалога.
        # Вариант с двумя обработчиками, фильтрующими текстовые сообщения.
        states={
            # Функция читает ответ на первый вопрос и задаёт второй.
            1: [MessageHandler(Filters.document, translation_file)]
        },

        # Точка прерывания диалога. В данном случае — команда /stop.
        fallbacks=[CommandHandler('stop_fl', stop_fl)]
    )
    dp.add_handler(game_conv)
    dp.add_handler(tr_conv)
    dp.add_handler(CommandHandler("reg", reg))
    dp.add_handler(CommandHandler("enter", enter))
    dp.add_handler(file_conv)
    dp.add_handler(CommandHandler('send_words', send_words))
    dp.add_handler(CommandHandler("unset", unset))
    dp.add_handler(CommandHandler("game", game))

    updater.start_polling()

    updater.idle()
    while True:
        schedule.run_pending()


if __name__ == '__main__':
    main()
