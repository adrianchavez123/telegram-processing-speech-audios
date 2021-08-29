import telebot
import json
import os
import re
from audio_helper import get_format, save_audio, count_words
from audio_details import save_audio_deliver

telegram_token = os.environ['TELEGRAM_TOKEN']
success_response = os.environ.get('SUCCESS_RESPONSE', 'Assignment delivered successfully')
response_message = os.environ.get('RESPONSE_MESSAGE', 'Tarea recibida.')
failure_message = os.environ.get('FAILURE_MESSAGE', 'Algo salia mal con el envio de la tarea, por favor vuelva a intentarlo.')
analize_speech_method = os.environ.get('ANALIZE_SPEECH_METHOD', 'AMPLITUDE_TO_DB')

bot = telebot.TeleBot(telegram_token)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
	bot.reply_to(message, "Hola, por favor envia tus tareas a este canal?")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
	bot.reply_to(message, message.text)

@bot.message_handler(content_types=['audio'])
def handle_audio(message):
	file_info = bot.get_file(message.audio.file_id)
	downloaded_file = bot.download_file(file_info.file_path)

	try:
		sound, file_name = save_audio(downloaded_file,message.from_user.id,message.date,message.audio.file_unique_id,message.audio.mime_type)
		count = count_words(sound, analize_speech_method, file_name)
		response = save_audio_deliver(60, message.from_user.id, file_info.file_path, count)
		if re.match(re.escape(success_response),response['message']):
			bot.reply_to(message, response_message)
		else:
			bot.reply_to(message, failure_message)
	except Exception as e:
		print(e)
		bot.reply_to(message, failure_message)

@bot.message_handler(content_types=['voice'])
def handle_voice(message):
	file_info = bot.get_file(message.voice.file_id)
	downloaded_file = bot.download_file(file_info.file_path)
	try:
		sound, file_name = save_audio(downloaded_file,message.from_user.id,message.date,message.voice.file_unique_id,message.voice.mime_type)
		count = count_words(sound, analize_speech_method, file_name)
		response = save_audio_deliver(60, message.from_user.id, file_info.file_path, count)
		if re.match(re.escape(success_response),response['message']):
			bot.reply_to(message, response_message)
		else:
			bot.reply_to(message, failure_message)
	except Exception as e:
		print(e)
		bot.reply_to(message, failure_message)
bot.polling()
