from pydub import AudioSegment
from pydub.silence import split_on_silence
from speechDetection import SpeechDetection
import librosa
import soundfile as sf
import numpy as np
import os

audios_dir = os.environ.get('AUDIOS_DIRECTORY', './audios')
max_size_audio_duration = os.environ.get('MAX_SIZE_AUDIO_DURATION', '180')
max_size_audio_chunk_duration = os.environ.get('MAX_SIZE_AUDIO_CHUNK_DURATION', '20')

def save_audio(file,user_id,date,unique_id,mime_type):
    format = get_format(mime_type)
    new_file_name = audios_dir + "/" + str(user_id) + "_" + str(date) + "_" + str(unique_id + "." + format)
    new_file_name_as_wav = audios_dir + "/" + str(user_id) + "_" + str(date) + "_" + str(unique_id + ".wav")
    with open(new_file_name, 'wb') as new_file:
        new_file.write(file)
    return convert_to_wav_format(new_file_name,format),new_file_name_as_wav

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

    if(sound.duration_seconds > int(max_size_audio_duration)):
        remove_audio_file(file)
        raise Exception(str(sound.duration_seconds) + ' exceed the max audio\'s duration  of "'+ str(max_size_audio_duration))
    make_louder = sound.apply_gain(30)
    make_louder = sound
    file_name = file[0:-4]
    file_name,_ = split_file_name_from_extension(file)
    #make_louder = make_louder.set_frame_rate(16000)
    make_louder.export(file_name+".wav", format="wav")
    remove_audio_file(file)
    return make_louder

def count_words(sound,method,file_name):
    if(method == 'AMPLITUDE_TO_DB'):
        return count_words_by_amplitude_level(file_name)
    elif(method == 'ENERGY_AND_TWO_STAGE_WIDE_BAND'):
        return count_words_by_energy_and_band_filters(file_name)
    return count_words_by_silence(sound,file_name)

def count_words_by_silence(sound, file_name):
    audio_chunks = split_on_silence(sound,
        min_silence_len=500,
        silence_thresh=-16,
        keep_silence=100,
        seek_step=1
    )
    chunk_file_names = save_chunks_of_audios(audio_chunks, file_name);
    recogonize(chunk_file_names) # return text
    return str(len(audio_chunks))

def count_words_by_amplitude_level(file_name):
    Signal,sr = librosa.load(file_name)
    n_fft = 2048
    coeffficients = librosa.stft(Signal,n_fft=n_fft, hop_length=n_fft//2)
    db = librosa.amplitude_to_db(np.abs(coeffficients),ref=np.max)
    fragments = librosa.effects.split(Signal, top_db=16) # audio above 20db
    print(str(len(fragments)))
    save_librosa_chunks_of_audios(fragments,Signal, file_name, sr)
    return str(len(fragments))

def count_words_by_energy_and_band_filters(file_name):
    detection = SpeechDetection(file_name)
    speech = detection.detect_speech()
    return str(len(speech))


def save_librosa_chunks_of_audios(fragments,Signal, file, sr):
    file_name,extension = split_file_name_from_extension(file)
    counter = 0
    for chunk in fragments:
        sf.write(f"{file_name}_{counter}.wav", Signal[chunk[0]:chunk[1]], sr)
        counter = counter + 1



def save_chunks_of_audios(audio_chunks, file_name):
    print("len "+str(len(audio_chunks)))
    chunk_file_names = []
    counter = 0
    for chunk in audio_chunks:
        duration_in_milliseconds = len(chunk)
        seconds = duration_in_milliseconds / 1000
        file_name_without_extension,_ = split_file_name_from_extension(file_name)
        #print(seconds)
        if(seconds < int(max_size_audio_chunk_duration)):
            # save_long file
            c, file_names = save_short_audio_chunck(chunk, file_name_without_extension, counter)
            # chunk_file_names append file_names
            counter = c
        else:
            # save_long file
            c, file_names = save_long_audio_chunck(chunk, file_name_without_extension, counter)
            # chunk_file_names append file_names
            counter = c
        #counter = counter + 1

def save_short_audio_chunck(audio, file_name, counter):
    duration_in_milliseconds = len(audio)
    seconds = duration_in_milliseconds / 1000
    chunk_file_names = []
    if(seconds > 10):
        print("if menor de 10s unir ")
        print("if too small join together ")
        # save_audio_file(chunk, f"{file_name}_{counter}.wav")
    else:
        save_audio_file(audio, f"{file_name}_{counter}.wav")
        counter = counter + 1
    return counter, chunk_file_names

def save_long_audio_chunck(audio, file_name, counter):
    duration_in_milliseconds = len(audio)
    seconds = duration_in_milliseconds / 1000
    chunk_file_names = []
    if(seconds < 40):
        save_audio_file(audio, f"{file_name}_{counter}.wav")
    else:
        print("if too long divide ")
    return counter, chunk_file_names


def save_audio_file(audio, file_name):
    # audio = audio.set_frame_rate(16000)
    audio.export(file_name, format="wav")

def remove_audio_file(file_name):
    try:
        os.remove(file_name)
    except:
        print("Error while deleting file ", file_name)

def split_file_name_from_extension(file):
    file_name = file[0:-4]
    extension = file[-4:]
    return file_name, extension
def recogonize(chunk_file_names):
    pass
