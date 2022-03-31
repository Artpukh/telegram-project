import sqlalchemy as sa
from db_session import *
import logging
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler, CallbackContext
from Users import User


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)

logger = logging.getLogger(__name__)

TOKEN = '5296805065:AAEwF8fUJQ36bOxG6UdQIbwf4zwcjDxHE0g'
current_name = None
current_id = None


def start(update, context):
    pass


def help(update, context):
    update.message.reply_text(
        "Привет! Это бот-переводчик!\n"
        "Мои возможномти:\n"
        "/reg - мы настоятельно рекомендуем вам зарегестрироваться, для регистрации нужно только придумать никнейм;\n"
        "/enter - вход в учётную запись;\n"
        "/translate - перевод слова или выражения;\n"
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


def main():
    global_init("accounts.db")

    updater = Updater(TOKEN)

    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("reg", reg))
    dp.add_handler(CommandHandler("enter", enter))

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()


