import sqlalchemy as sa
from googletrans import Translator
from db_session import *
import logging
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler
from Users import User



logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)

logger = logging.getLogger(__name__)

TOKEN = '5296805065:AAEwF8fUJQ36bOxG6UdQIbwf4zwcjDxHE0g'
current_name = None
current_id = None
tr = Translator()


def start(update, context):
    pass


def help(update, context):
    update.message.reply_text(
        "Привет! Это бот-переводчик!\n"
        "Мои возможномти:\n"
        "/reg - мы настоятельно рекомендуем вам зарегестрироваться, для регистрации нужно только придумать никнейм;\n"
        "/enter - вход в учётную запись;\n"
        "/tr_to_ru - перевод слова или выражения с английского на русский;\n"
        "/tr_to_en - перевод слова или выражения с русского на английский;\n"
        "/translate_file - перевод содержимого файла, возвращает файл с переводом;\n"
        "/translate_from_file - бот с выбранной периодчностью будет давать перевод слова из отправленного файла;\n"
        "/game - игра: бот загадывает слово, пользователь даёт перевод;"
        )


def reg(update, context):
    global current_name, current_id
    name = ' '.join(context.args)
    print(name)
    user = User()
    user.nickname = name
    db_sess = create_session()
    look = db_sess.query(User).filter(User.nickname == name).first()
    if look:
        update.message.reply_text('Такая учётная запись уже существует')
    else:
        db_sess.add(user)
        db_sess.commit()
        update.message.reply_text('Поздравляю! Вы успешно прошли регистрацию')
        current_name = name
        current_id = user.id


def enter(update, context):
    global current_name, current_id
    name = ' '.join(context.args)
    db_sess = create_session()
    user = db_sess.query(User).filter(User.nickname == name).first()
    if user:
        current_name = user.nickname
        current_id = user.id
        update.message.reply_text('Вы вошли в свой аккаунт')
    else:
        update.message.reply_text('Такой учётной записи не существует')


def translate_to_ru(update, context):
    text = ' '.join(context.args)
    result = tr.translate(text, src='en', dest='ru')
    update.message.reply_text(result.text)


def translate_to_en(update, context):
    text = ' '.join(context.args)
    result = tr.translate(text, src='ru', dest='en')
    update.message.reply_text(result.text)


def translate_file(update, context):
    f = open('translate.txt', encoding='utf-8', mode='r')
    content = f.read()
    update.message.reply_text('en')
    if tr.detect(content).lang == 'en':
        result = tr.translate(content, dest='ru')
        with open('translate.txt', encoding='utf-8', mode='w') as f:
            f.write(result.text)
    else:
        result = tr.translate(content, dest='en')
        with open('translate.txt', encoding='utf-8', mode='w') as f:
            f.write(result.text)


def main():
    global_init("accounts.db")

    updater = Updater(TOKEN)

    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("reg", reg))
    dp.add_handler(CommandHandler("enter", enter))
    dp.add_handler(CommandHandler("tr_to_ru", translate_to_ru))
    dp.add_handler(CommandHandler("tr_to_en", translate_to_en))
    dp.add_handler(CommandHandler("translate_file", translate_file))

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()


