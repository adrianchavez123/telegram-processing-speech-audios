from pydub import AudioSegment
from pydub.silence import split_on_silence

def save_audio(file,user_id,date,unique_id,mime_type):
    format = get_format(mime_type)
    new_file_name = "./audios/"+str(user_id)+"_"+str(date)+"_"+str(unique_id+"."+format)
    with open(new_file_name, 'wb') as new_file:
        new_file.write(file)
    return convert_to_wav_format(new_file_name,format)  

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

def count_words(sound):
    duration_in_milliseconds = len(sound)
    seconds = duration_in_milliseconds / 1000
    audio_chunks = split_on_silence(sound, 
        min_silence_len=200,
        silence_thresh=-16,
        keep_silence=50,
        seek_step=1
    )
    return str(len(audio_chunks))