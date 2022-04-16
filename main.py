import sqlalchemy as sa
from googletrans import Translator
from db_session import *
import logging
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler, ConversationHandler
from Users import User
import os



logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)

logger = logging.getLogger(__name__)

TOKEN = '5296805065:AAEwF8fUJQ36bOxG6UdQIbwf4zwcjDxHE0g'
current_name = None
current_id = None
tr = Translator()
chat_id = 720508763


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


def stop(update, context):
    return ConversationHandler.END


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


def translate(update, context):
    update.message.reply_text('Введите текст')
    return 1


def translation(update, context):
    text = update.message.text
    if tr.detect(text).lang == 'en':
        result = tr.translate(text, dest='ru')
    else:
        result = tr.translate(text, dest='en')
    update.message.reply_text(result.text)
    return ConversationHandler.END


def translate_file(update, context):
    update.message.reply_text('Отправьте файл')
    return 1


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
    context.bot.send_document(chat_id=chat_id, document=open(f'{update.message.document.file_name}', mode='rb'))
    os.remove(update.message.document.file_name)
    return ConversationHandler.END


def main():
    global_init("accounts.db")

    updater = Updater(TOKEN, use_context=True)

    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    tr_conv = ConversationHandler (
        entry_points=[CommandHandler('translate', translate)],

        # Состояние внутри диалога.
        # Вариант с двумя обработчиками, фильтрующими текстовые сообщения.
        states={
            # Функция читает ответ на первый вопрос и задаёт второй.
            1: [MessageHandler(Filters.text, translation)]
        },

        # Точка прерывания диалога. В данном случае — команда /stop.
        fallbacks=[CommandHandler('stop', stop)]
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
        fallbacks=[CommandHandler('stop', stop)]
    )
    dp.add_handler(tr_conv)
    dp.add_handler(CommandHandler("reg", reg))
    dp.add_handler(CommandHandler("enter", enter))
    dp.add_handler(file_conv)

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()


