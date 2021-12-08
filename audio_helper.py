from pydub import AudioSegment
from pydub.silence import split_on_silence
from pydub.utils import make_chunks
from speechDetection import SpeechDetection
from speechToText import SpeechToText
from vosk import Model, KaldiRecognizer, SetLogLevel
from scipy import signal
from dotenv import load_dotenv
from audio_io import save_audio_file, save_audio_chunck, remove_files, remove_audio_file
import librosa
import soundfile as sf
import numpy as np
import os,json
import wave
import logging

load_dotenv()

log_file = os.environ['LOG_FILE']
logging.basicConfig(filename=log_file, level = logging.INFO,
format='%(asctime)s:%(levelname)s:%(message)s')

audios_dir = os.environ['AUDIOS_DIRECTORY']
max_size_audio_duration = os.environ.get('MAX_SIZE_AUDIO_DURATION', '180')
max_size_audio_chunk_duration = os.environ.get('MAX_SIZE_AUDIO_CHUNK_DURATION', '15')
speech_to_text_model = os.environ.get('SPEECH_TO_TEXT_MODEL', 'google')

def save_audio(file, mime_type, file_name, tags = None, extension = "wav"):
    logging.info(f"executing save_audio(), file_name={file_name}")
    format = get_format(mime_type)
    new_file_name = audios_dir + "/" + file_name + "." + format
    new_file_name_as_wav = audios_dir + "/" + file_name + "." + extension
    logging.info(f"original audio ({new_file_name})")
    logging.info(f"original saved on wav format ({new_file_name_as_wav})")
    with open(new_file_name, 'wb') as new_file:
        new_file.write(file)

    return convert_format(new_file_name,format,new_file_name_as_wav, tags, extension), new_file_name_as_wav

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

def convert_format(file,format,file_name_as_wav, tags, extension):
    logging.info(f" executing convert_format(), file={file}, format={format}")
    sound = AudioSegment.from_file(file,format)

    if(sound.duration_seconds > int(max_size_audio_duration)):
        remove_audio_file(file)
        raise Exception(str(sound.duration_seconds) + ' exceed the max audio\'s duration  of "'+ str(max_size_audio_duration))
    make_louder = sound.apply_gain(30)
    make_louder = sound
    file_name = file[0:-4]
    file_name,_ = split_file_name_from_extension(file)
    logging.info("tags")
    logging.info(tags)
    logging.info(f"extension = {extension}")
    make_louder.export(file_name + "." + extension, format=extension, tags=tags)
    if file_name + "." + extension != file_name_as_wav:
        logging.info(f"remove original file ({file})and keep wav format")
        remove_audio_file(file)
    logging.debug(f"converted to {file_name}.{extension}")
    return make_louder

def analyze_audio(sound,method,file_name):
    logging.info(f" executing analyze_audio(), method={method}, file_name={file_name}")
    if(method == 'AMPLITUDE_TO_DB'):
        return analyze_by_amplitude_level(file_name)
    elif(method == 'ENERGY_AND_TWO_STAGE_WIDE_BAND'):
        return analyze_by_energy_and_band_filters(file_name)
    elif(method == 'ZERO_CROSSING_RATE'):
        return analyze_split_audio_by_zero_crossing_rate(sound,file_name)
    return analyze_split_audio_by_silence(sound,file_name)

def analyze_split_audio_by_zero_crossing_rate(sound, file_name):
    logging.info(f" executing analyze_split_audio_by_zero_crossing_rate(), file_name={file_name}")
    chunk_length_ms = 400 # in millisec
    chunks = make_chunks(sound, chunk_length_ms) #Make chunks
    audio_chunks_total = []
    for i, chunk in enumerate(chunks):
        samples = chunk[i].get_array_of_samples()
        audioData = np.array(samples)
        suma =  ((audioData[:-1] * audioData[1:]) < 0).sum()
        if(suma > 20):
            audio_chunks_total.append(suma)

    # better option to construct audio segments
    Signal,sr = librosa.load(file_name)
    file_names = save_segment_of_audios(Signal, file_name, sr)
    text = recognize(file_names)
    remove_files(file_names)
    return str(len(audio_chunks_total)), text

def analyze_split_audio_by_silence(sound, file_name):
    logging.info(f" executing analyze_split_audio_by_silence(), file_name={file_name}")
    audio_chunks = split_on_silence(sound,
        min_silence_len=100,
        silence_thresh=-35,
        keep_silence=60,
        seek_step=1
    )
    # when the signal is reconstructed, the sound is chopping
    #chunk_file_names = save_chunks_of_audios(audio_chunks, file_name)
    #text = recognize(chunk_file_names)
    #return str(len(audio_chunks)), text

    # better option to construct audio segments
    Signal,sr = librosa.load(file_name)
    file_names = save_segment_of_audios(Signal, file_name, sr)
    text = recognize(file_names)
    remove_files(file_names)
    return str(len(audio_chunks)), text

def analyze_by_amplitude_level(file_name):
    logging.info(f" executing analyze_by_amplitude_level(), file_name={file_name}")

    Signal,sr = librosa.load(file_name)
    #n_fft = 512
    #coeffficients = librosa.stft(Signal,n_fft=n_fft, hop_length=n_fft//4,window=signal.windows.hamming, center=True)
    #db = librosa.amplitude_to_db(np.abs(coeffficients),ref=np.max)


    fragments = librosa.effects.split(Signal, top_db=16) # audio above 16db
    #file_names = save_librosa_chunks_of_audios(fragments,Signal, file_name, sr)
    seconds = librosa.get_duration(y=Signal, sr=sr)

    file_names = save_segment_of_audios(Signal, file_name, sr)
    text = recognize(file_names)
    remove_files(file_names)
    return str(len(fragments)), text

def analyze_by_energy_and_band_filters(file_name):
    logging.info(f" executing analyze_by_energy_and_band_filters(), file_name={file_name}")
    detection = SpeechDetection(file_name)
    signal, rate = detection.get_data()
    speech = detection.detect_speech()
    print(f" fragmentos: {str(len(speech))}")
    file_names = save_segment_of_audios(signal, file_name, rate)
    text = recognize(file_names)
    remove_files(file_names)
    return str(len(speech)), text

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
    temp = None
    i = 0
    for chunk in audio_chunks:
        file_name_without_extension,_ = split_file_name_from_extension(file_name)
        if temp is None:
            temp = chunk
        else:
            temp = temp.append(chunk, crossfade=80)

        duration_in_milliseconds = len(temp)
        seconds = duration_in_milliseconds / 1000

        if(seconds > int(max_size_audio_chunk_duration) or i == len(audio_chunks) -1 ):
            # save_long file
            c, chunk_file_name = save_audio_chunck(temp, file_name_without_extension, counter)
            # chunk_file_names append file_names
            counter = c
            temp = None
            chunk_file_names.append(chunk_file_name)
            print(chunk_file_name)
        i = i + 1
    return chunk_file_names

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
