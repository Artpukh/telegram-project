from googletrans import Translator
from db_session import *
import logging
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler, ConversationHandler, CallbackContext
from telegram import ReplyKeyboardMarkup, Update
from Users import User
from Words import Word
import os
from swift import words
symbs = words
from random import choice
import datetime

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)

logger = logging.getLogger(__name__)

TOKEN = '5296805065:AAEwF8fUJQ36bOxG6UdQIbwf4zwcjDxHE0g'
current_name = None
current_id = None
# клавиатура
reply_keyboard = [['/start', '/help', "/reg"],
                  ['/enter', '/translate', "/translate_file"]]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
tr = Translator()  # класс, отвечающий за перевод


def start(update, context):
    pass


def help(update, context):
    update.message.reply_text(
        "RU\n"
        "Привет! Это бот-переводчик!\n"
        "Мои возможномти:\n"
        "/reg - мы настоятельно рекомендуем вам зарегестрироваться, для регистрации нужно только придумать никнейм;\n"
        "/enter - вход в учётную запись;\n"
        "/translate - перевод слова или выражения с английского на русский и наоборот;\n"
        "/translate_file - перевод содержимого файла, возвращает файл с переводом;\n"
        "/send_words - бот с выбранной периодчностью будет давать перевод слова из отправленного файла;\n"
        "/game - игра: бот загадывает слово, пользователь даёт перевод;"
        "\n"
        "\n"
        "ENG\n"
        "Hello! This is a translate bot\n"
        "/reg - we strongly recommend you to register, you only need to come up with a nickname to register;\n"
        "/enter - login to your account;\n"
        "/translate - translation of a word or expression from English to Russian and vice versa;\n"
        "/translate_file - translation of the file contents, returns a file with translation;\n"
        "/translate_from_file - the bot with the selected frequency will translate the word from the sent file;\n"
        "/send_words - the bot with the selected frequency will give the translation of the word from the sent file;\n"
        "/game - game: the bot makes a word, the user gives a translation;",
        reply_markup=markup
        )


# функция, оканчивающая сценарией с переводом файлов
def stop_fl(update, context):
    return ConversationHandler.END


# функция отвечает за регистрацию в системе
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


# функция отвечает за вход в систему
def enter(update, context):
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


# команда для начала сценария перевода слов и выражений
def translate(update, context):
    update.message.reply_text('Введите текст')
    return 1


# функция, выполняющая перевод выражений
def translation(update, context):
    global reply_keyboard
    reply_keyboard = [['/stop_tr']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
    text = update.message.text
    if text == '/stop_tr':
        reply_keyboard = [['/start', '/help', "/reg"],
                          ['/enter', '/translate', "/translate_file"]]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
        update.message.reply_text('Всего доброго', reply_markup=markup)
        return ConversationHandler.END
    if tr.detect(text).lang == 'en':
        result = tr.translate(text, dest='ru')
    else:
        result = tr.translate(text, dest='en')
    update.message.reply_text(result.text, reply_markup=markup)
    return 1


# отвечает за остановку сценария с переводом слов и выражений (на деле - чистая формальность)
def stop_tr(update, context):
    return ConversationHandler.END


# команда для начала сценария перевода файлов
def translate_file(update, context):
    update.message.reply_text('Отправьте файл')
    return 1


# функция, выполняющая перевод файлов
def translation_file(update, context):
    global reply_keyboard
    reply_keyboard = [['/start', '/help', "/reg"],
                      ['/enter', '/translate']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
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
    context.bot.send_document(chat_id=update.message.chat_id, document=open(f'{update.message.document.file_name}',
                                                                            mode='rb'), reply_markup=markup)
    os.remove(update.message.document.file_name)
    return ConversationHandler.END


# функция отвечает за удаление существующих таймеров
def remove_job_if_exists(name, context):
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


# функция отвечает за отправку новых слов из swift.py
def job(context: CallbackContext):
    word = ''
    slova = Word()
    db_sess = create_session()
    spis = []
    for a in db_sess.query(Word).filter(Word.user_id == current_id):
        spis.append(a.words)
    while len(word) <= 4 and word in spis:
        word = choice(symbs)
    slova.user_id = current_id
    slova.words = word
    db_sess.add(slova)
    db_sess.commit()
    word_tr = tr.translate(word, dest='en')
    context.bot.send_message(chat_id=context.job.context, text=f'{word} - {word_tr.text}')


# команда отвечает за начало сценария по отправке слов из swift.py
def send_words(update: Update, context: CallbackContext):
    due = context.args[0].split(':')

    context.job_queue.run_daily(job, time=datetime.time(hour=int(due[0]) - 3, minute=int(due[1]), second=00),
                                days=(0, 1, 2, 3, 4, 5, 6),
                                context=update.message.chat_id, name=str(update.message.chat_id))


# функиця убирает существующие таймеры, нераздельно связано
def unset(update, context):
    chat_id = update.message.chat_id
    job_removed = remove_job_if_exists(str(chat_id), context)
    text = 'Таймер успешно отменён' if job_removed else 'Нет активных таймеров.'
    update.message.reply_text(text)


def main():
    global_init("accounts.db")

    updater = Updater(TOKEN, use_context=True)

    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    # сценарий по переводу слов и выражений
    tr_conv = ConversationHandler(
        entry_points=[CommandHandler('translate', translate)],

        states={
            1: [MessageHandler(Filters.text, translation)]
        },

        fallbacks=[CommandHandler('stop_tr', stop_tr)]
    )
    # сценарий по переводу файлов
    file_conv = ConversationHandler(
        entry_points=[CommandHandler('translate_file', translate_file)],

        states={
            1: [MessageHandler(Filters.document, translation_file)]
        },

        fallbacks=[CommandHandler('stop_fl', stop_fl)]
    )
    dp.add_handler(tr_conv)
    dp.add_handler(CommandHandler("reg", reg))
    dp.add_handler(CommandHandler("enter", enter))
    dp.add_handler(file_conv)
    dp.add_handler(CommandHandler('send_words', send_words))
    dp.add_handler(CommandHandler("unset", unset))

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()


