import telebot
import json
import os
import re
import csv
from dotenv import load_dotenv
from student_subscription import subscribe, register
import logging

load_dotenv()
logging.basicConfig(filename='/home/ec2-user/auto-subscribe-students/logs/test.log', level = logging.DEBUG,
format='%(asctime)s:%(levelname)s:%(message)s')

telegram_token = os.environ['TELEGRAM_TOKEN']
success_response = os.environ.get('SUCCESS_RESPONSE', 'Assignment delivered successfully')
update_success_response = os.environ.get('UPDATE_SUCCESS_RESPONSE', 'Update successful!')
response_message = os.environ.get('RESPONSE_MESSAGE', 'Tarea recibida.')
failure_message = os.environ.get('FAILURE_MESSAGE', 'Algo salia mal con el envio de la tarea, por favor vuelva a intentarlo.')
analyze_speech_method = os.environ.get('ANALYZE_SPEECH_METHOD', 'AMPLITUDE_TO_DB')
audio_jobs = os.environ.get('AUDIO_JOBS_FILE', '/home/ec2-user/auto-subscribe-students/audio_jobs.csv')
bot = telebot.TeleBot(telegram_token)

def add_to_job(message,file_id):

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
			writer.writerow(["student_id", "date", "file_unique_id", "mime_type", "file_id"])
		writer.writerow([message.from_user.id, message.date, file_unique_id, mime_type, file_id])
		logging.info(f"Added to the queue ({message.from_user.id} - {file_id}) ")

@bot.message_handler(commands=['start','iniciar'])
def send_welcome(message):
	try:
		logging.info(f"Subscribing ({message.from_user.id} - {message.from_user.first_name}) ")
		subscribe(message.from_user.id, message.from_user.first_name)
		bot.reply_to(message, "Hola, por favor utiliza esta canal para enviar tus tareas, casi estamos listo por favor ingresa /registrar espacio y el numero de grupo que tu maestro compartio.")
	except:
		bot.reply_to(message, "Hola, ocurrio un error, por favor intenta iniciar más tarde escribiendo /iniciar en este canal.")
		logging.warning(f"the subscription of ({message.from_user.id} - {message.from_user.first_name}) failed.")

@bot.message_handler(commands=['registrar'])
def join_group(message):
	try:
		logging.info(f"join group ({message.from_user.id} - {message.from_user.first_name}) ")
		token = message.text.split()[1]
		response = register(message.from_user.id, token)
		register_response = "registered to group"
		if re.match(register_response,response['message']):
			bot.reply_to(message, "registrado :), por favor utiliza este chat para enviar tus tareas.")
		else:
			bot.reply_to(message, "no registrado, por favor intenta registrarte más tarde.")
			logging.warning(f"Registration of id: {message.from_user.id} failed.")
	except Exception as e:
		print(e)
		bot.reply_to(message, "error, por favor asegurate de escriber el numero de token.")
		logging.warning(f"Registration of id: {message.from_user.id} failed.")


@bot.message_handler(content_types=['audio'])
def handle_audio(message):

	try:
		logging.debug(f"audio recieved ({message.audio.file_id}) ")
		add_to_job(message, message.audio.file_id)
		bot.reply_to(message, response_message)
	except Exception as e:
		logging.warning(f" The audio was not added to the processing queue, error: {e} ")
		bot.reply_to(message, failure_message)

@bot.message_handler(content_types=['voice'])
def handle_voice(message):
	try:
		logging.debug(f"voice recieved ({message.voice.file_id}) ")
		file_info = bot.get_file(message.voice.file_id)
		add_to_job(message, message.voice.file_id)
		bot.reply_to(message, response_message)
	except Exception as e:
		logging.warning(f" The voice audio was not added to the processing queue, error: {e} ")
		bot.reply_to(message, failure_message)

logging.debug("Initizating telegram bot listener")
bot.polling()
