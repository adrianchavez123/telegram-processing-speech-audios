from pydub import AudioSegment
from dotenv import load_dotenv
import logging
import os

load_dotenv()
log_file = os.environ['LOG_FILE']
logging.basicConfig(filename=log_file, level = logging.INFO,
format='%(asctime)s:%(levelname)s:%(message)s')

def save_audio_file(audio, file_name):
    audio.export(file_name, format="wav")

def save_audio_chunck(audio, file_name, counter):
    new_file_name = f"{file_name}_{counter}.wav"
    save_audio_file(audio, new_file_name)
    counter = counter + 1
    return counter, new_file_name

def remove_files(file_names):
    for file_name in file_names:
        remove_audio_file(file_name)

def remove_audio_file(file_name):
    try:
        os.remove(file_name)
    except:
        print(f"Error deliting file, ({file_name})")
