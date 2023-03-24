import telebot
import settings
from telebot import types
import sqlite3

bot = telebot.TeleBot(settings.token)

############################################################################################################################
# СОЗДАНИЕ ГЛАВНОГО МЕНЮ
def buttons(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard = True, row_width = 1)
    issue = types.KeyboardButton('❔Вопрос по товару/доставке')
    want_review = types.KeyboardButton('Я бы хотела(а) оставить отзыв')
    done_review = types.KeyboardButton('Я уже оставила(а) отзыв')
    markup.add(issue, want_review, done_review)
    mess =  f'Приветствую,<b>{message.from_user.first_name}</b>!\n\n'\
            'Благодарим Вас за покупку  💚\n\n'\
            'У вас есть вопросы или замечания по товару '\
            'или вы хотели бы получить кэшбек за оставленный отзыв?☺️\n\n'\
            'Выберите интересующее вас действие в меню ниже'
    bot.send_message(message.chat.id, mess, parse_mode = 'html', reply_markup = markup)

############################################################################################################################
# ОТЛАВЛИВАЕМ ВЫЗОВЫ ИЗ ИНЛАЙН КЛАВИАТУРЫ
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data == 'cancel':
        bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        buttons(call.message)
############################################################################################################################
    elif call.data in ('send_screenshot', 'change_review'):
        bot.delete_message(call.message.chat.id, call.message.message_id)
        done_review_st2(call.message)
    elif call.data.startswith('send_review'):
        with sqlite3.connect('is_base.db') as base:
            cur = base.cursor()
            cur.execute('UPDATE users SET review == ? WHERE id_tg == ? AND ven_code == ?', (True, call.message.chat.id, int(call.data[12:])))
            mess = 'Ваша информация отправлена👍,'\
                    'ecли все указано верно вы получите кэшбэк в ближайшее время\n\n'\
                    'Всего Вам доброго и до новых встреч😊'
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(call.message.chat.id, mess, parse_mode = 'html')
            data = cur.execute('SELECT ven_code, name, screenshot_id FROM users WHERE id_tg == ?', (call.message.chat.id, )).fetchone()
        mess = '<b>Отзыв о товаре</b>\n\n'\
                f'Товар: <b>{data[0]}</b>\n'\
                f'Покупатель: <b>{data[1]}</b>'
        bot.send_photo(settings.admin, data[2], caption = mess, parse_mode = 'html')
    elif call.data == 'change_screenshot':
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, 'Выберите и отправьте другой скриншот сюда.')
        bot.register_next_step_handler(call.message, handle_screen)
    elif call.data == 'change_issue':
        bot.delete_message(call.message.chat.id, call.message.message_id)
        issue(call.message)
############################################################################################################################
    elif call.data == 'send_issue':
        mess = 'Ваша информация была передана продавцу, спасибо!'
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text = mess, reply_markup=None)
        with sqlite3.connect('is_base.db') as base:
            cur = base.cursor()
            data = cur.execute('SELECT name, ven_code, issue FROM users WHERE id_tg == ?', (call.message.chat.id, )).fetchone()
        mess = '<b>Вопрос/замечание о товаре</b>\n\n'\
                f'Товар: <b>{data[1]}</b>\n'\
                f'Покупатель: <b>{data[0]}</b>\n'\
                f'Текст:\n\n{data[2]}'
        bot.send_message(settings.admin, mess, parse_mode = 'html')
############################################################################################################################
# ВЫВОД ИНФОРМАЦИИ О ТОМ КАК ОСТАВИТЬ ОТЗЫВ
def make_review_info(message):
    bot.clear_step_handler_by_chat_id(chat_id=message.chat.id)
    mess = 'Отлично! ☺️\n\n'\
            'Для получения бонуса, Вам нужно оставить отзыв. Это очень простые 6 шагов :\n'\
            '▫️Зайдите в Личный кабинет\n'\
            '▫️Наведите мышкой на раздел "Профиль" и выберите "Покупки"\n'\
            '▫️Наведите мышкой на товар, который приобрели у нас и кликните на "Написать отзыв"\n'\
            '▫️Напишите отзыв, прикрепите фотографию товара, поставьте оценку\n'\
            '▫️Кликните "Отправить"\n'\
            '▫️Сделайте скриншот готового отзыва и прикрепите в наш чат-бот.'
    bot.send_message(message.chat.id, mess, parse_mode = 'html')

############################################################################################################################
# ДИАЛОГ С ПОЛЬЗОВАТЕЛЕМ ОБ ОСТАВЛЕННОМ ОТЗЫВЕ
def done_review(message):
    bot.clear_step_handler_by_chat_id(chat_id=message.chat.id)
    mess = 'Класс! 😊 В таком случае, нам необходим скриншот отзыва,'\
            'имя (под которым Вы оставили отзыв на Wildberries), '\
            'артикул товара и номер телефона, на который мы отправим Вам бонус.\n\n'\
            '▫️Как найти отзыв?\n'\
            'В Личном кабинете Wildberries все оставленные Вами отзывы можно найти в разделе "Профиль" ➡️ "Покупки".\n'\
            'В примере выше, Вы можете найти наглядную инструкцию, как найти отзыв, чтобы сделать скриншот.\n\n'\
            'Если вы сделали скриншот, отправьте его сюда.'
    bot.send_message(message.chat.id, mess, parse_mode = 'html')
    bot.register_next_step_handler(message, handle_screen)

def done_review_st2(message):
    prev_mes = bot.send_message(message.chat.id, 'Укажите свое имя, под которым вы оставляли отзыв', reply_markup=cancel_markup())
    bot.register_next_step_handler(message, done_review_st3, prev_mes)

def done_review_st3(message, prev_mes):
    user_name = message.text
    mess = 'Введите артикул товара\n\n'\
            '▫️Как посмотреть?'\
            'В Личном кабинете Wildberries зайдите в разделе '\
            '"Профиль" ➡️ "Покупки". Нажмите на товар, чуть ниже вы найдете Артикул.'
    bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=prev_mes.message_id, reply_markup=None)
    prev_mes = bot.send_message(message.chat.id, mess, parse_mode = 'html', reply_markup = cancel_markup())
    bot.register_next_step_handler(message, done_review_st4, user_name, prev_mes)

def done_review_st4(message, user_name, prev_mes):
    ven_code = message.text
    bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=prev_mes.message_id, reply_markup=None)
    if not ven_code.isdecimal():
        prev_mes = bot.send_message(message.chat.id, 'Артикул должен состоять из цифр, повторите ввод', reply_markup=cancel_markup())
        bot.register_next_step_handler(message, done_review_st4, user_name, prev_mes)
        return False
    mess = f'Ваше имя: <b>{user_name}</b>\n'\
            f'Артикул товара: <b><u>{ven_code}</u></b>\n'\
            'Все верно? Отправляем?'
    with sqlite3.connect('is_base.db') as base:
        cur = base.cursor()
        is_review = cur.execute('SELECT review FROM users WHERE id_tg == ? AND ven_code == ?', (message.chat.id, ven_code)).fetchone()
        if is_review:
            if is_review[0]:
                bot.send_message(message.chat.id, 'Вы уже оставляли отзыв об этом товаре', parse_mode = 'html')
                buttons(message)
                return False
        cur.execute('UPDATE users SET name == ?, ven_code == ? WHERE id_tg == ?', (user_name, ven_code, message.chat.id))
        base.commit()
    markup = types.InlineKeyboardMarkup(row_width = 2)
    yes = types.InlineKeyboardButton('Да', callback_data = 'send_review' + str(ven_code))
    no = types.InlineKeyboardButton('Изменить', callback_data = 'change_review')
    cancel = types.InlineKeyboardButton('❌Отмена', callback_data = 'cancel')
    markup.add(yes, no, cancel)
    bot.send_message(message.chat.id, mess, parse_mode = 'html', reply_markup = markup)

############################################################################################################################
# ОТЛАВЛИВАЕМ СКРИНШОТЫ ОТ ПОЛЬЗОВАТЕЛЯ
# @bot.message_handler(content_types = ['photo'])
def handle_screen(message, prev_mes = 0):
    if prev_mes:
        bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=prev_mes.message_id, reply_markup=None)
    if not message.photo:
        prev_mes = bot.send_message(message.chat.id, 'Ожидается скриншот', parse_mode = 'html', reply_markup = cancel_markup())
        bot.register_next_step_handler(message, handle_screen, prev_mes)
        return False
    file_id = message.photo[-1].file_id
    with sqlite3.connect('is_base.db') as base:
        cur = base.cursor()
        if (cur.execute('SELECT id FROM users WHERE id_tg == ?', (message.chat.id, )).fetchone()):
            cur.execute('UPDATE users SET screenshot_id == ? WHERE id_tg == ?', (file_id, message.chat.id))
        else:
            cur.execute('INSERT INTO users(id_tg, screenshot_id) VALUES (?, ?)', (message.chat.id, file_id))
        base.commit()
    markup = types.InlineKeyboardMarkup(row_width = 1)
    ok = types.InlineKeyboardButton('✅Отправить', callback_data = 'send_screenshot')
    cancel = types.InlineKeyboardButton('❌Отмена', callback_data = 'cancel')
    change_screen = types.InlineKeyboardButton('🔄Заменить скриншот', callback_data = 'change_screenshot')
    markup.add(ok, change_screen, cancel)
    bot.send_photo(message.chat.id, file_id, caption = 'Скриншот получен', reply_markup = markup)

############################################################################################################################
# ФУНКЦИЯ СОЗДАНИЯ КНОПКИ ОТМЕНЫ ПРИ ДИАЛОГЕ С ПОЛЬЗОВАТЕЛЕМ
def cancel_markup():
    markup = types.InlineKeyboardMarkup()
    cancel = types.InlineKeyboardButton('❌Отмена', callback_data='cancel')
    markup.add(cancel)
    return markup


############################################################################################################################
# ДИАЛОГ О ВОПРОСЕ\ПРЕТЕНЗИИ К ТОВАРУ ИЛИ ДОСТАВКЕ
def issue(message):
    bot.clear_step_handler_by_chat_id(chat_id=message.chat.id)
    mess = 'Введите имя, под которым вы совершали заказ'
    prev_mes = bot.send_message(message.chat.id, mess, parse_mode = 'html', reply_markup=cancel_markup())
    bot.register_next_step_handler(message, issue_st2, prev_mes)

def issue_st2(message, prev_mes):
    user_name = message.text
    mess = 'Введите артикул товара\n\n'\
            '▫️Как посмотреть?'\
            'В Личном кабинете Wildberries зайдите в разделе '\
            '"Профиль" ➡️ "Покупки". Нажмите на товар, чуть ниже вы найдете Артикул.'
    bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=prev_mes.message_id, reply_markup=None)
    prev_mes = bot.send_message(message.chat.id, mess, parse_mode = 'html', reply_markup=cancel_markup())
    bot.register_next_step_handler(message, issue_st3, user_name, prev_mes)

def issue_st3(message, user_name, prev_mes):
    ven_code = message.text
    bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=prev_mes.message_id, reply_markup=None)
    if not ven_code.isdecimal():
        prev_mes = bot.send_message(message.chat.id, 'Артикул должен состоять из цифр, повторите ввод', reply_markup=cancel_markup())
        bot.register_next_step_handler(message, issue_st3, user_name, prev_mes)
        return False
    mess = f'<b>{user_name}</b>, опишите пожалуйста проблему или вопрос '\
            f'о товаре <u>{ven_code}</u> в подробностях в одном сообщении'
    prev_mes = bot.send_message(message.chat.id, mess, parse_mode = 'html', reply_markup=cancel_markup())
    bot.register_next_step_handler(message, issue_st4, user_name, ven_code, prev_mes)

def issue_st4(message, user_name, ven_code, prev_mes):
    issue_text = message.text
    bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=prev_mes.message_id, reply_markup=None)
    mess = f'Ваше имя: <b>{user_name}</b>\n'\
            f'Артикул товара: <b><u>{ven_code}</u></b>\n\n'\
            f'Ваше сообщение:\n{issue_text}\n\n'\
            'Все верно? Отправляем?'
    with sqlite3.connect('is_base.db') as base:
        cur = base.cursor()
        if cur.execute('SELECT id FROM users WHERE id_tg == ?', (message.chat.id,)).fetchone():
            cur.execute('UPDATE users SET name == ?, ven_code == ?, issue == ? WHERE id_tg == ?', (user_name, ven_code, issue_text, message.chat.id))
        else:
            cur.execute('INSERT INTO users(id_tg, name, ven_code, issue) VALUES (?, ?, ?, ?)', (message.chat.id, user_name, ven_code, issue_text))
        base.commit()
    markup = types.InlineKeyboardMarkup(row_width = 2)
    yes = types.InlineKeyboardButton('Да', callback_data = 'send_issue')
    no = types.InlineKeyboardButton('Изменить', callback_data = 'change_issue')
    cancel = types.InlineKeyboardButton('❌Отмена', callback_data = 'cancel')
    markup.add(yes, no, cancel)
    bot.send_message(message.chat.id, mess, parse_mode = 'html', reply_markup = markup)

############################################################################################################################
# ОТЛАВЛИВАЕМ ТЕКСТОВЫЕ СООБЩЕНИЯ ОТ ПОЛЬЗОВАТЕЛЯ
@bot.message_handler(content_types = ['text'])
def check_messages(message):
    if message.text == '❔Вопрос по товару/доставке':
        issue(message)
    elif message.text == 'Я бы хотела(а) оставить отзыв':
        make_review_info(message)
    elif message.text == 'Я уже оставила(а) отзыв':
        done_review(message)
    else:
        buttons(message)
############################################################################################################################
# ТОЧКА ВХОДА
if __name__ == '__main__':
    bot.infinity_polling()