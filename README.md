# telegram-processing-speech-audios

__telegram-processing-speech-audios__ is a protototype of a telegram bot that listens to audio/video files and it returns the number of words identified.
The script is spliting the words by silences are lower than 200 miliseconds and the speech volum is lower than 16 dBit 
Currently, the application contains two files:
- *bot.py* a basic telegram bot that is listening for audios 
- *audio_helper.py* maniputes the audio files and it exports the audios to __wav__ format

## Installation
**The script depends depends heavily on: telebot and AudioSegment** but they can be installed with the next command.
the required dependecies are on `requirements.txt` and the command bellow will install the dependencies

```
pip install -r requirements.txt
```

__Note__ if you see a problem with soundfile library, that is used by librosa library and you are running the script in a rpm package management, you need to run this command. `yum install libsndfile`.


## Install ffmpeg
`AudioSegment` is a library that manipulates audio files and for some operations `ffmpeg` is a requirement,it can be installed on different OS.
for instructions please check, [Installing-ffmped](https://github.com/adaptlearning/adapt_authoring/wiki/Installing-FFmpeg)

## Installing ffmpeg on aws LINUX AMI (t2.micro)

AWS Linux AMI utilizes a Linux version however `yum install ffmpeg` is not working so the library needs to be installed manually. this [gist note](https://gist.github.com/willmasters/382fe6caba44a4345a3de95d98d3aae5) describe very well the steps to follow.
*bot.py* was tested with ffmpeg 4.2.2 and it worked correctly just an additional command was executed.

```
ln -s /usr/local/bin/ffmpeg/ffprobe /usr/bin/ffprobe
```

## Execution

Make sure python is installed and before starting the script, create *TELEGRAM_TOKEN* environment variable 
```
export TELEGRAM_TOKEN=__your_token__
```
An alternative is to create a __.env__ file with __TELEGRAM_TOKEN__ variable and additional environment variables.
At the root directory, you are going to find _env_ file with the common configuration, you can insert your tokens and secret api credentials there.

Run `python bot.py` or `python3 bot.py` and enjoy your bot and start sending audios.

## Schedule

This project works together with [word-counter-backend](https://github.com/adrianchavez123/word-counter-backend/) a backend service that stores the result of the analysis of the audios, the services can be consumed via api calls. Next to `bot.py`, you are going to find the `scheduler.py` file that depends on [schedule library](https://schedule.readthedocs.io/en/stable/), to manage schedule jobs.

Run `python schedule.py` or `python3 schedule.py` the script will keep running and its jobs will be executed once they met the criterion.

the schedule contains of two jobs `notify_group_new_assignment`and `close_pass_due_date_assignments`, they will be described below:
Internally, both jobs work together with the backend service to be synced.

#### notify_group_new_assignment
This job consults the backend service to know if any new assignment was created, the notification gets the notification template and notifies the members of the group.
The job runs every 10 seconds

#### close_pass_due_date_assignments
The closing pass due date process runs one day at `23:50` and its job is to close any assignment that is pass due date.


## Configure scripts to run as services
Linux services or daemons provides easy ways to start, restart and stop but also the services can be configure to run at startup and also restart if something goes wrong. this seccion is going give you an overflow of how to convert a python script to a service. Talking about this application the scripts **scheduler.py** and **bot.py** are good fit to become a service they need to be running all the time so they listen to updates or to run some features at a specific time. for more detail you can check [How To Use Systemctl to Manage Systemd Services and Units](https://www.digitalocean.com/community/tutorials/how-to-use-systemctl-to-manage-systemd-services-and-units) and the post [Setup a python script as a service through systemctl/systemd](https://medium.com/codex/setup-a-python-script-as-a-service-through-systemctl-systemd-f0cc55a42267)

Install systemd
```
sudo yum install systemd
```

Create a new service file, this project provides two examples of services, you can find the files under **service-files** directory.
```
vim /etc/systemd/system/telebot.service
```

Reload the service list
```
sudo systemctl daemon-reload
```

Configure the service to start at startup
```
sudo systemctl enable telebot.service
```
Start the service
```
sudo systemctl start telebot.service
```
Check service's status
```
sudo systemctl status telebot.service
```

Get more details of your service
```
journalctl -u telebot.service
```
## Analysis helper
The script that analizes and works with audio files is `audio_helper.py`, the script execute different audio processing tasks and some of them can be switched by environment files. The audio analisis can be group in the following tasks.

1. Download/Copy audio files and convert them to `wav` files, WAV files is the format that works better with python audio libraries. 
2. Transform the audio file increase the volume (make the sound louder)
3. Extract audio features (voice/no voice), divide the audio in segments excluding not voice signals.
⋅⋅ 3.1 Extract the audio features by amplitude db levels
⋅⋅ 3.2 Extract the audio features by energy levels
⋅⋅ 3.3 Extract the audio features by silence levels
4. Convert the audio to text to store the results, at this point this project depends of third party libraries, that the goal is to update once the data to work with is enough.
⋅⋅ 4.1 Recognize text (speech to text) by google api
⋅⋅ 4.2 Recognize text (speech to text) by ibm api
⋅⋅ 4.3 Recognize text (speech to text) by vosk
5. Send the results the backend service to store the data. 

#### Extract audio features

**Amplitude DB**
This audio segmentation is applying __stft__ to get the audio coefficients, and it uses as parameter _hann_ method for the windowing (overlapping) of the segments, after that _amplitude_to_db_ method is applied, at the end the split methods is applied.
Environment variable:_AMPLITUDE_TO_DB_ 

**Audio energy**
This implementation is based on two stage wide filters (a higher and lower filter are aplied to exclude pieces of audio that are not interested on analyze). Internally, it is calculating the amplitude and energy and based a threshold, it splits and keeps the audios that contain voice frames.
Environment variable:_ENERGY_AND_TWO_STAGE_WIDE_BAND_

**Non silence**
This audio segments are split by audio silences, the method recieves different parameters such as the threshold (values smaller that threshold are considered silence), the minimum length of a silence, leave some silence on the chunks to do not hear cut off.
Environment variable:_SPLIT_BY_SILENCE_

#### Recognize text

**By google**
audio_helper.py uses [Speech Recognition](https://pypi.org/project/SpeechRecognition/) library to convert the audio to text, to get a better analysis, you can use google cloud platform and create a speech to text service and the credential can be added. current implentation is using speech recognition with out credentials.

**By ibm**
ibm cloud also provides speech to text services, you can see the api reference [here](https://cloud.ibm.com/apidocs/speech-to-text), once you create the service you need set the environment variables `IBM_SPEECH_TO_TEXT_API_KEY` and `IBM_SPEECH_TO_TEXT_URL`.


**By vosk**
[vosk](https://alphacephei.com/vosk/) is another alternative speech to text service that can be used to convert audio to text with the advantage that it can run offline what it means is better performance and also the most popular speech to text services has some rate limiting or the cost is based on calls per month.

The feature extraction and recognize methods can be turn on and off by environment variables.
