from pydub import AudioSegment
from pydub.silence import split_on_silence
import librosa
import numpy as np
import os

audiosDir = os.environ.get('AUDIOS_DIRECTORY', './audios')

def save_audio(file,user_id,date,unique_id,mime_type):
    format = get_format(mime_type)
    new_file_name = audiosDir + "/" + str(user_id)+"_"+str(date)+"_"+str(unique_id+"."+format)
    with open(new_file_name, 'wb') as new_file:
        new_file.write(file)
    return convert_to_wav_format(new_file_name,format),new_file_name

def get_format(mime_type):
    if mime_type == "audio/x-m4a":
        return "m4a"
    elif mime_type == "audio/mpeg3":
        return "mp3"
    elif mime_type == "audio/ogg":
        return "ogg"
    elif mime_type ==  "audio/x-wav":
        return "wav"

    raise Exception('The format "'+mime_type+'" is not supported.')

def convert_to_wav_format(file,format):
    sound = AudioSegment.from_file(file,format)
    make_louder = sound.apply_gain(30)
    filename = file[0:-4]
    make_louder.export(filename+".wav", format="wav")
    return make_louder

def count_words(sound,method,file_name):
    if(method == 'AMPLITUDE_TO_DB'):
        return count_words_by_amplitude_level(file_name)
    return count_words_by_silence(sound)

def count_words_by_silence(sound):
    duration_in_milliseconds = len(sound)
    seconds = duration_in_milliseconds / 1000
    audio_chunks = split_on_silence(sound,
        min_silence_len=500,
        silence_thresh=-16,
        keep_silence=50,
        seek_step=1
    )
    return str(len(audio_chunks))

def count_words_by_amplitude_level(file_name):
    Signal,sr = librosa.load(file_name)
    n_fft = 2048
    coeffficients = librosa.stft(Signal,n_fft=n_fft, hop_length=n_fft//2)
    db = librosa.amplitude_to_db(np.abs(coeffficients),ref=np.max)
    fragments = librosa.effects.split(Signal, top_db=20) # audio above 20db
    return str(len(fragments))
