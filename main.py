from pathlib import Path
import telebot
from telebot.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    InputMediaPhoto
)
from configparser import ConfigParser

parser = ConfigParser()
parser.read(Path('init.ini').absolute())
telegram_api_token = parser['telegram']['telegram_api_token']
sl_chat_id = parser['telegram']['sl_chat_id']
bot = telebot.TeleBot(token=telegram_api_token)


def build_menu(buttons, n_cols, header_buttons='', footer_buttons=''):
    menu = [buttons[item:item + n_cols] for item in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)
    return menu


@bot.message_handler(commands=['new'])
def ad_init_message(message):
    if message.chat.type != "private":
        bot.send_message(message.chat.id, "Используйте данную команду только в личных сообщениях боту")
        return 0
    keyboard = ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    button = KeyboardButton(text="Отмена")
    keyboard.add(button)
    bot.send_message(message.chat.id, "Отправьте изображение", reply_markup=keyboard)
    bot.register_next_step_handler(message, ad_image)


def ad_image(message):
    keyboard = ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    button = KeyboardButton(text="Отмена")
    keyboard.add(button)
    medias = message.photo[-1].file_id  # _________________
    bot.send_message(message.chat.id, "Отправьте отформатированный текст", reply_markup=keyboard)
    bot.register_next_step_handler(message, ad_text, ad_photo=medias)


def ad_text(message, ad_photo):
    keyboard = ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
    button = KeyboardButton(text="Не требуется")
    keyboard.add(button)
    button = KeyboardButton(text="Отмена")
    keyboard.add(button)
    ad_text = message.text
    entities = message.entities
    bot.send_message(message.chat.id, 'Отправьте текст кнопки и ссылку через запятую',
                     reply_markup=keyboard)
    bot.register_next_step_handler(message, ad_inline, ad_photo=ad_photo, ad_text=ad_text, entities=entities)


def ad_inline(message, ad_photo, ad_text, entities):
    buttons = []
    have_inline = 0
    if message.text != "Не требуется":
        have_inline = 1
        text, url = message.text.split(',')
        buttons.append(InlineKeyboardButton(text=text.lstrip().rstrip(), url=url.lstrip().rstrip()))

    call_data_msg = f"{have_inline}_addition"
    buttons.extend([InlineKeyboardButton("Опубликовать",
                                         callback_data=f"publish_{call_data_msg}"),
                    InlineKeyboardButton("Удалить",
                                         callback_data=f"delete_{call_data_msg}")])
    keyboard = InlineKeyboardMarkup(build_menu(buttons, n_cols=1))

    bot.send_photo(message.chat.id, photo=ad_photo, caption=ad_text, reply_markup=keyboard,
                   caption_entities=entities)


@bot.callback_query_handler(func=lambda call: call.data.endswith('addition'))
def add_service_message(call):
    bot.answer_callback_query(callback_query_id=call.id, text='')
    action, have_inline, _ = call.data.split('_')
    if action == 'publish':
        if have_inline != '0':
            keyboard = call.message.reply_markup.keyboard[0]
            markup = InlineKeyboardMarkup(row_width=1)
            buttons = [
                InlineKeyboardButton(text=keyboard[0].text, url=keyboard[0].url)
            ]
            markup.add(*buttons)
            bot.copy_message(
                from_chat_id=call.message.chat.id,
                chat_id=sl_chat_id,
                message_id=call.message.id,
                reply_markup=markup,
                parse_mode="Markdown"
            )
        else:
            bot.copy_message(
                from_chat_id=call.message.chat.id,
                chat_id=sl_chat_id,
                message_id=call.message.id,
                parse_mode="Markdown"
            )
        bot.edit_message_caption(
            caption=f"Запись опубликована\n\n{call.message.caption}",
            chat_id=call.message.chat.id,
            message_id=call.message.id,
            reply_markup=InlineKeyboardMarkup([])
        )
    else:
        bot.edit_message_text(
            text="Публикация отменена",
            chat_id=call.message.chat.id,
            message_id=call.message.id
        )


bot.infinity_polling()
