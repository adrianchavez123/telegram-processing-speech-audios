import telebot
import json
import os
import re
import csv
from audio_helper import get_format, save_audio, analyze_audio
from audio_details import save_audio_deliver
from dotenv import load_dotenv
from student_subscription import subscribe, register

load_dotenv()

telegram_token = os.environ['TELEGRAM_TOKEN']
success_response = os.environ.get('SUCCESS_RESPONSE', 'Assignment delivered successfully')
update_success_response = os.environ.get('UPDATE_SUCCESS_RESPONSE', 'Update successful!')
response_message = os.environ.get('RESPONSE_MESSAGE', 'Tarea recibida.')
failure_message = os.environ.get('FAILURE_MESSAGE', 'Algo salia mal con el envio de la tarea, por favor vuelva a intentarlo.')
analyze_speech_method = os.environ.get('ANALYZE_SPEECH_METHOD', 'AMPLITUDE_TO_DB')
audio_jobs = os.environ.get('AUDIO_JOBS_FILE', './audio_jobs.csv')
bot = telebot.TeleBot(telegram_token)

def add_to_job(message,file_info):

	file_unique_id = None
	mime_type = None
	if hasattr(message, 'audio') and hasattr(message.audio, 'file_unique_id'):
		file_unique_id = message.audio.file_unique_id
		mime_type = message.audio.mime_type
	else:
		file_unique_id = message.voice.file_unique_id
		mime_type = message.voice.mime_type

	write_header = False
	if not os.path.isfile(audio_jobs):
		write_header = True
	with open(audio_jobs, "a+") as fp:
		writer = csv.writer(fp, delimiter=",")

		if write_header:
			writer.writerow(["student_id", "date", "file_unique_id", "mime_type", "file_path"])
		writer.writerow([message.from_user.id, message.date, file_unique_id, mime_type, file_info.file_path])

@bot.message_handler(commands=['start','iniciar'])
def send_welcome(message):
	try:
		subscribe(message.from_user.id, message.from_user.first_name)
		bot.reply_to(message, "Hola, por favor utiliza esta canal para enviar tus tareas, casi estamos listo por favor ingresa /registrar espacio y el numero de grupo que tu maestro compartio.")
	except:
		bot.reply_to(message, "Hola, ocurrio un error, por favor intenta iniciar más tarde escribiendo /iniciar en este canal.")

@bot.message_handler(commands=['registrar'])
def join_group(message):
	try:
		token = message.text.split()[1]
		response = register(message.from_user.id, token)
		register_response = "registered to group"
		if re.match(register_response,response['message']):
			bot.reply_to(message, "registrado :), por favor utiliza este chat para enviar tus tareas.")
		else:
			bot.reply_to(message, "no registrado, por favor intenta registrarte más tarde.")
	except Exception as e:
		print(e)
		bot.reply_to(message, "error, por favor asegurate de escriber el numero de token.")


@bot.message_handler(content_types=['audio'])
def handle_audio(message):
	file_info = bot.get_file(message.audio.file_id)

	try:
		#downloaded_file = bot.download_file(file_info.file_path)
		#sound, file_name = save_audio(downloaded_file,message.from_user.id,message.date,message.audio.file_unique_id,message.audio.mime_type)
		#words_amount, text = analyze_audio(sound, analyze_speech_method, file_name)
		#response = save_audio_deliver(message.from_user.id, file_info.file_path, words_amount, text)
		#if re.match(re.escape(success_response),response['message']) or re.match(re.escape(update_success_response),response['message']):
			#bot.reply_to(message, response_message)
		#else:
			#bot.reply_to(message, failure_message)
		add_to_job(message,file_info)
		bot.reply_to(message, response_message)
	except Exception as e:
		print(e)
		bot.reply_to(message, failure_message)

@bot.message_handler(content_types=['voice'])
def handle_voice(message):
	file_info = bot.get_file(message.voice.file_id)

	try:
		downloaded_file = bot.download_file(file_info.file_path)
		#sound, file_name = save_audio(downloaded_file,message.from_user.id,message.date,message.voice.file_unique_id,message.voice.mime_type)
		#words_amount, text = analyze_audio(sound, analyze_speech_method, file_name)
		#response = save_audio_deliver(message.from_user.id, file_info.file_path, words_amount, text)
		#if re.match(re.escape(success_response),response['message']) or re.match(re.escape(update_success_response),response['message']):
			#bot.reply_to(message, response_message)
		#else:
			#bot.reply_to(message, failure_message)
		add_to_job(message, file_info)
		bot.reply_to(message, response_message)
	except Exception as e:
		print(e)
		bot.reply_to(message, failure_message)
bot.polling()
