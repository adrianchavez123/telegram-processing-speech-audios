from pydub import AudioSegment
from pydub.silence import split_on_silence
from speechDetection import SpeechDetection
from speechToText import SpeechToText
import librosa
import soundfile as sf
import numpy as np
import os,json
from vosk import Model, KaldiRecognizer, SetLogLevel
import wave
from dotenv import load_dotenv
import logging
load_dotenv()
logging.basicConfig(filename='/home/ec2-user/auto-subscribe-students/logs/test.log', level = logging.WARNING,
format='%(asctime)s:%(levelname)s:%(message)s')

audios_dir = os.environ.get('AUDIOS_DIRECTORY', '/home/ec2-user/auto-subscribe-students/audios')
max_size_audio_duration = os.environ.get('MAX_SIZE_AUDIO_DURATION', '180')
max_size_audio_chunk_duration = os.environ.get('MAX_SIZE_AUDIO_CHUNK_DURATION', '20')
speech_to_text_model = os.environ.get('SPEECH_TO_TEXT_MODEL', 'google')

def save_audio(file,user_id,date,unique_id,mime_type):
    logging.info(f"executing save_audio(), file={file}, user_id={user_id}, date={date}")
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
    logging.warning('The format "'+mime_type+'" is not supported.')
    raise Exception('The format "'+mime_type+'" is not supported.')

def convert_to_wav_format(file,format):
    logging.info(f" executing convert_to_wav_format(), file={file}, format={format}")
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
    logging.info(f"converted to {file_name}.wav")
    return make_louder

def analyze_audio(sound,method,file_name):
    logging.info(f" executing analyze_audio(), method={method}, file_name={file_name}")
    if(method == 'AMPLITUDE_TO_DB'):
        return analyze_by_amplitude_level(file_name)
    elif(method == 'ENERGY_AND_TWO_STAGE_WIDE_BAND'):
        return analyze_by_energy_and_band_filters(file_name)
    return analyze_split_audio_by_silence(sound,file_name)

def analyze_split_audio_by_silence(sound, file_name):
    logging.info(f" executing analyze_split_audio_by_silence(), file_name={file_name}")
    audio_chunks = split_on_silence(sound,
        min_silence_len=500,
        silence_thresh=-16,
        keep_silence=100,
        seek_step=1
    )
    chunk_file_names = save_chunks_of_audios(audio_chunks, file_name);
    text = recognize(chunk_file_names)
    return str(len(audio_chunks)), text

def analyze_by_amplitude_level(file_name):
    logging.info(f" executing analyze_by_amplitude_level(), file_name={file_name}")
    Signal,sr = librosa.load(file_name)
    n_fft = 2048
    coeffficients = librosa.stft(Signal,n_fft=n_fft, hop_length=n_fft//2,window='hann', center=True)
    db = librosa.amplitude_to_db(np.abs(coeffficients),ref=np.max)
    fragments = librosa.effects.split(Signal, top_db=20) # audio above 20db
    #file_names = save_librosa_chunks_of_audios(fragments,Signal, file_name, sr)
    seconds = librosa.get_duration(y=Signal, sr=sr)

    #print("break by stft: ...\n\n")
    #recognize(file_names)
    #remove_files(file_names)
    #print("whole audio:  ...\n\n")
    #recognize([file_name])
    #print("split by size  ...\n\n")
    file_names = save_segment_of_audios(Signal, file_name, sr)
    text = recognize(file_names)
    remove_files(file_names)
    return str(len(fragments)), text

def analyze_by_energy_and_band_filters(file_name):
    logging.info(f" executing analyze_by_energy_and_band_filters(), file_name={file_name}")
    detection = SpeechDetection(file_name)
    speech = detection.detect_speech()
    return str(len(speech))

def save_segment_of_audios(Signal, file, sr):
    file_name,extension = split_file_name_from_extension(file)
    max_segment_size = int(10*sr)
    frame_size = 0
    chunk_counter = 0
    file_names = []
    while frame_size < len(Signal):
        name = f"{file_name}_segment_{chunk_counter}.wav"
        sf.write(name, Signal[frame_size : frame_size + max_segment_size], sr)
        file_names.append(name)
        frame_size += max_segment_size
        chunk_counter = chunk_counter + 1
    return file_names

def save_librosa_chunks_of_audios(fragments,Signal, file, sr):
    file_name,extension = split_file_name_from_extension(file)
    counter = 0
    chunk_counter = 0
    file_names = []
    max_segment_size = int(10*sr)
    framesSize = 0
    a = np.array(Signal[0:1])
    pad=0.400
    overlap = int(pad * sr)

    for chunk in fragments:
        start = chunk[0]
        # increase frame size to avoid choping sounds on one syllabel sound
        end = chunk[1]

        if(start - end < overlap):
            pad_duration = 0.200

        if(start - overlap > 0):
            start = chunk[0] + overlap
        if(end + 1000 < len(Signal)):
            end = chunk[1] + overlap

        silence = np.zeros(int(pad_duration*sr))
        frameSize = end - start
        framesSize = framesSize + frameSize

        a =  np.concatenate([a, Signal[start:end]])
        a =  np.concatenate([a, silence])
        if(framesSize > max_segment_size or chunk_counter == len(fragments) -1):
            name = f"{file_name}_{counter}.wav"
            sf.write(name, a, sr)
            framesSize = 0
            a = np.array(Signal[0:1])
            file_names.append(name)
            counter = counter + 1
        chunk_counter = chunk_counter + 1
    return file_names

def save_chunks_of_audios(audio_chunks, file_name):
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
        # save_audio_file(chunk, f"{file_name}_{counter}.wav")
        pass
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
        pass
    return counter, chunk_file_names

def save_audio_file(audio, file_name):
    # audio = audio.set_frame_rate(16000)
    audio.export(file_name, format="wav")

def remove_files(file_names):
    for file_name in file_names:
        remove_audio_file(file_name)

def remove_audio_file(file_name):
    try:
        os.remove(file_name)
    except:
        log.warning(f"Error deliting file, ({file_name})")

def split_file_name_from_extension(file):
    file_name = file[0:-4]
    extension = file[-4:]
    return file_name, extension

def recognize(file_names):
    logging.info(f"executing recognize(), model={speech_to_text_model}")
    speech_to_text = []
    for file_name in file_names:
        speechToText = SpeechToText(file_name,speech_to_text_model)
        text = speechToText.recognize()
        speech_to_text.append(text)
    return ' '.join(speech_to_text)
