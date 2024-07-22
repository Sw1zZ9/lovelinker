import telebot
import logging
from telebot import types
from db import save_profile, get_profile, search_profiles, get_user_photo_path, db_lock,  get_db_cursor, \
    get_db_connection

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Токен бота
TOKEN = '7227497628:AAFLrW0jUivz7mHcpwtTsUs6bZ0GPfh8HRc'
bot = telebot.TeleBot(TOKEN)

def notify_user(user_id, liked_user_id):
    liked_user = get_profile(liked_user_id)
    if liked_user:
        liked_user_name = liked_user[1]
        bot.send_message(user_id, f"Вам понравился(ась) {liked_user_name}. Смотрите его(её) профиль по ссылке: https://4337-154-47-24-154.ngrok-free.app/profile/{liked_user_id}")

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    logging.info(f"Start command received from user {user_id}")
    profile = get_profile(user_id)
    if profile:
        bot.reply_to(message, f"Добро пожаловать обратно, {profile[1]}! Введите /profile чтобы посмотреть ваш профиль или /update чтобы обновить его.")
    else:
        bot.reply_to(message, "Привет! Давайте создадим ваш профиль. Введите ваше имя:")
        bot.register_next_step_handler(message, process_name_step)

def process_name_step(message):
    user_id = message.from_user.id
    name = message.text
    bot.reply_to(message, "Введите ваш возраст:")
    bot.register_next_step_handler(message, process_age_step, name)

def process_age_step(message, name):
    age = message.text
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    btn1 = types.KeyboardButton("Мужчина")
    btn2 = types.KeyboardButton("Женщина")
    btn3 = types.KeyboardButton("Не указано")
    markup.add(btn1, btn2, btn3)
    bot.reply_to(message, "Выберите ваш пол:", reply_markup=markup)
    bot.register_next_step_handler(message, process_gender_step, name, age)

def process_gender_step(message, name, age):
    gender = message.text.lower()
    if gender in ['мужчина', 'женщина', 'не указано']:
        bot.reply_to(message, "Введите информацию о себе:")
        bot.register_next_step_handler(message, process_bio_step, name, age, gender)
    else:
        bot.reply_to(message, "Неверный выбор. Пожалуйста, выберите 'мужчина', 'женщина' или 'не указано'.")
        bot.register_next_step_handler(message, process_gender_step, name, age)

def process_bio_step(message, name, age, gender):
    bio = message.text
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    btn1 = types.KeyboardButton("Аватарка из Telegram")
    btn2 = types.KeyboardButton("Загрузить свою")
    btn3 = types.KeyboardButton("Без аватарки")
    markup.add(btn1, btn2, btn3)
    bot.reply_to(message, "Выберите, как вы хотите загрузить аватарку:", reply_markup=markup)
    bot.register_next_step_handler(message, process_photo_step, name, age, gender, bio)

def process_photo_step(message, name, age, gender, bio):
    user_id = message.from_user.id
    photo_choice = message.text.lower()
    if photo_choice == 'аватарка из telegram':
        file_info = bot.get_user_profile_photos(user_id)
        if file_info.photos:
            file_id = file_info.photos[0][0].file_id
            file = bot.get_file(file_id)
            downloaded_file = bot.download_file(file.file_path)
            photo_path = get_user_photo_path(user_id)
            with open(photo_path, 'wb') as new_file:
                new_file.write(downloaded_file)
            save_profile(user_id, name, age, gender, bio, photo_path)
            bot.reply_to(message, "Ваш профиль создан! Введите /profile чтобы посмотреть ваш профиль.")
        else:
            bot.reply_to(message, "У вас нет фотографии профиля в Telegram. Пожалуйста, загрузите свою фотографию.")
            bot.register_next_step_handler(message, process_upload_photo_step, name, age, gender, bio)
    elif photo_choice == 'загрузить свою':
        bot.reply_to(message, "Пожалуйста, загрузите свою фотографию.")
        bot.register_next_step_handler(message, process_upload_photo_step, name, age, gender, bio)
    elif photo_choice == 'без аватарки':
        save_profile(user_id, name, age, gender, bio, 'no_photo')
        bot.reply_to(message, "Ваш профиль создан без аватарки! Введите /profile чтобы посмотреть ваш профиль.")
    else:
        bot.reply_to(message, "Неверный выбор. Пожалуйста, выберите один из предложенных вариантов.")
        bot.register_next_step_handler(message, process_photo_step, name, age, gender, bio)

def process_upload_photo_step(message, name, age, gender, bio):
    user_id = message.from_user.id
    if message.photo:
        photo = message.photo[-1]
        file_info = bot.get_file(photo.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        photo_path = get_user_photo_path(user_id)
        with open(photo_path, 'wb') as new_file:
            new_file.write(downloaded_file)
        save_profile(user_id, name, age, gender, bio, photo_path)
        bot.reply_to(message, "Ваш профиль создан! Введите /profile чтобы посмотреть ваш профиль.")
    else:
        bot.reply_to(message, "Фотография не была загружена. Пожалуйста, попробуйте снова.")
        bot.register_next_step_handler(message, process_upload_photo_step, name, age, gender, bio)

@bot.message_handler(commands=['profile'])
def profile(message):
    user_id = message.from_user.id
    profile = get_profile(user_id)
    if profile:
        name = profile[1]
        age = profile[2]
        gender = profile[3]
        bio = profile[4]
        photo_path = profile[5]

        if photo_path == 'no_photo':
            bot.reply_to(message, f"Ваш профиль:\nИмя: {name}\nВозраст: {age}\nПол: {gender}\nО себе: {bio}\nАватарка: Не установлена")
        else:
            try:
                with open(photo_path, 'rb') as photo_file:
                    bot.send_photo(message.chat.id, photo_file,
                                   caption=f"Ваш профиль:\nИмя: {name}\nВозраст: {age}\nПол: {gender}\nО себе: {bio}")
            except FileNotFoundError:
                bot.reply_to(message, f"Ваш профиль:\nИмя: {name}\nВозраст: {age}\nПол: {gender}\nО себе: {bio}\nАватарка: Не установлена (ошибка при загрузке фото)")
    else:
        bot.reply_to(message, "У вас еще нет профиля. Введите /start чтобы создать его.")

@bot.message_handler(commands=['update'])
def update_profile(message):
    user_id = message.from_user.id
    profile = get_profile(user_id)
    if profile:
        bot.reply_to(message, "Введите ваше имя:")
        bot.register_next_step_handler(message, process_name_step)
    else:
        bot.reply_to(message, "У вас еще нет профиля. Введите /start чтобы создать его.")

def notify_user(user_id, liked_user_id):
    liked_user = get_profile(liked_user_id)
    if liked_user:
        liked_user_name = liked_user[1]
        bot.send_message(user_id, f"Вам понравился(ась) {liked_user_name}. Смотрите его(её) профиль по ссылке: https://example.com/profile/{liked_user_id}")


@bot.message_handler(commands=['like'])
def like_profile(message):
    user_id = message.from_user.id
    try:
        liked_user_id = int(message.text.split()[1])
        conn = get_db_connection()
        cursor = get_db_cursor(conn)
        with db_lock:
            cursor.execute('INSERT OR IGNORE INTO likes (user_id, liked_user_id) VALUES (?, ?)',
                           (user_id, liked_user_id))
            conn.commit()
            bot.reply_to(message, f"Вы понравились пользователю с ID {liked_user_id}.")
            cursor.execute('SELECT * FROM likes WHERE user_id = ? AND liked_user_id = ?', (liked_user_id, user_id))
            if cursor.fetchone():
                notify_user(liked_user_id, user_id)
                notify_user(user_id, liked_user_id)
        conn.close()
    except (IndexError, ValueError):
        bot.reply_to(message, "Неверный формат команды. Используйте /like <user_id>")

