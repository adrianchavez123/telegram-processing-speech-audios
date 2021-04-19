import telebot
import json
import os
from audio_helper import get_format, save_audio, count_words
telegram_token = os.environ['TELEGRAM_TOKEN']
bot = telebot.TeleBot(telegram_token)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
	bot.reply_to(message, "Hola, enviar un audio para contar las palabras detectadas?")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
	bot.reply_to(message, message.text)

@bot.message_handler(content_types=['audio'])
def handle_audio(message):
    bot.reply_to(message, "procesando audio ...")
    file_info = bot.get_file(message.audio.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    
    sound = save_audio(downloaded_file,message.from_user.id,message.date,message.audio.file_unique_id,message.audio.mime_type)
    count = count_words(sound)
    bot.reply_to(message, count + " palabras fueron detectadas")

@bot.message_handler(content_types=['voice'])
def handle_voice(message):
    bot.reply_to(message, "procesando voz ...")
    file_info = bot.get_file(message.voice.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    sound = save_audio(downloaded_file,message.from_user.id,message.date,message.voice.file_unique_id,message.voice.mime_type)
    count = count_words(sound)
    bot.reply_to(message, count + " palabras fueron detectadas")

bot.polling()

