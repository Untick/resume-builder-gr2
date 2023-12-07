from telegram.ext import Application, CommandHandler, MessageHandler, filters
from dotenv import load_dotenv
import openai
import os
import asyncio
import whisper
import numpy as np
from pydub import AudioSegment
from pydub.utils import make_chunks
import io
import soundfile as sf
from io import BytesIO
from gtts import gTTS, gTTSError


load_dotenv()

TOKEN = os.environ.get("TOKEN")
GPT_SECRET_KEY = os.environ.get("GPT_SECRET_KEY")

openai.api_key = GPT_SECRET_KEY

# Укажите полный путь к каталогу с FFmpeg
ffmpeg_directory = r"D:\ffmpeg-master-latest-win64-gpl\bin"
os.environ["PATH"] += os.pathsep + ffmpeg_directory

async def convert_to_wav(voice_file):
    # Загрузка аудио в формате ogg
    byte_audio = await voice_file.download_as_bytearray()
    input_path = "input.ogg"
    with open(input_path, "wb") as input_file:
        input_file.write(byte_audio)

    # Путь к выходному файлу WAV
    output_path = "output.wav"

    # Конвертация в WAV с помощью soundfile
    ogg_audio, sample_rate = sf.read(input_path)
    sf.write(output_path, ogg_audio, sample_rate)

    return output_path

async def transcribe_audio(audio_data, model_name='large'):
    # Загружаем модель для распознавания речи
    model = whisper.load_model(model_name)

    # Распознаем аудиофайл в текст
    result = model.transcribe(audio_data)
    return result["text"]


async def get_text_from_audio(byte_voice):
     
    # Распознайте голос в текст
    text = await transcribe_audio(byte_voice)
    return text

async def get_answer(text):
    completion = openai.chat.completions.create(
        model="gpt-3.5-turbo-0301",
        messages=[{"role": "user", "content": text}])
    return completion.choices[0].message.content

async def start(update, context):
    await update.message.reply_text('Задайте любой вопрос chatGPT')

async def help_command(update, context):
    await update.message.reply_text("Вы можете пообщаться с chatGPT на любую тему")

async def handle_message(update, context):
    if update.message.text:
        # Обработка текстового сообщения
        res = await get_answer(update.message.text)
        message = await update.message.reply_text('Ваш вопрос обрабатывается…')
        await message.delete()  # Удаляем сообщение "Ваш вопрос обрабатывается…"
        await update.message.reply_text(res)
        # Преобразовать ответ в речь и воспроизвести его
        await show_audio_player(res, update)
    elif update.message.voice:
        # Обработка голосового сообщения
        file = await update.message.voice.get_file()
        audio_wav = await convert_to_wav(file)
        audio_text = await transcribe_audio(audio_wav)
        message = await update.message.reply_text('Ваш вопрос обрабатывается…')
        await message.delete()  # Удаляем сообщение "Ваш вопрос обрабатывается…"
        res = await get_answer(audio_text)
        await update.message.reply_text(res)
        # Преобразовать ответ в речь и воспроизвести его
        await show_audio_player(res, update)


async def show_audio_player(ai_content, update):
    sound_file = BytesIO()
    try:
        tts = gTTS(text=ai_content, lang="ru")
        tts.save("output.mp3")
        voice_file = open("output.mp3", "rb")
        await update.message.reply_voice(voice=voice_file)
                # Воспроизведите аудио с помощью pygame
    except gTTSError as err:
        update.message.reply_text(err)



def main():
    application = Application.builder().token(TOKEN).build()
    print('Бот запущен...')

    application.add_handler(CommandHandler("start", start, block=False))
    application.add_handler(CommandHandler("help", help_command, block=False))
    application.add_handler(MessageHandler(filters.TEXT | filters.VOICE, handle_message, block=False))

    application.run_polling()

if __name__ == "__main__":
    main()

