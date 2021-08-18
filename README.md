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


## Install ffmpeg
`AudioSegment` is a library that manipulates audio files and for some operations `ffmpeg` is a requirement,it can be installed on different OS.
for instructions please check, [Installing-ffmped](https://github.com/adaptlearning/adapt_authoring/wiki/Installing-FFmpeg)

## Installing ffmpeg on aws LINUX AMI (t2.micro)

AWS Linux AMI utilizes a Linux version however `yum install ffmpeg` is not working so the library needs to be installed manually. this [gist note](https://gist.github.com/willmasters/382fe6caba44a4345a3de95d98d3aae5) describe very well the steps to follow.
*bot.py* was tested with ffmpeg 4.2.2 and it worked correctly just an additional command was executed.

```
ln -s /usr/local/bin/ffmpeg/ffprobe /usr/bin/ffprobe
```

## Excecution

Make sure python is installed and before starting the script, create *TELEGRAM_TOKEN* environment variable 
```
export TELEGRAM_TOKEN=__your_token__
```

Run `python bot.py` or `python3 bot.py` and enjoy your bot and start sending audios.
