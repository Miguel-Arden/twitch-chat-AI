import openai
from twitchio.ext import commands
import os
from dotenv import load_dotenv
import asyncio
import time
from pathlib import Path
from playsound import playsound
import random
import whisper
import sounddevice as sd
import numpy as np
import queue
from rich import print as rprint
from Prompts import SYSTEM_PROMPT

load_dotenv()

openai.api_key = os.getenv('OPENAI_API_KEY') #see readme if you're confused on what to put here

whisper_model = whisper.load_model("base")
audio_queue = queue.Queue()

def audio_callback(indata, frames, time, status):
    if status:
        print(f"Audio status: {status}")
    audio_queue.put(indata.copy())

def transcribe_audio():
    audio_buffer = []
    while not audio_queue.empty():
        audio_chunk = audio_queue.get()
        audio_buffer.append(audio_chunk)
    if audio_buffer:
        audio_array = np.concatenate(audio_buffer, axis=0).flatten()
        return whisper_model.transcribe(audio_array, fp16=False)["text"]
    return ""

class Bot(commands.Bot):
    def __init__(self):
        super().__init__(
            token=os.getenv('GREG_ACCESS'), #Twitch access token for the AI channel goes here
            prefix='!',
            initial_channels=['migven'], #CHANGE THIS TO THE CHANNEL YOU WANT THE AI TO TYPE IN
            nick="GregoryThe52" #CHANGE THIS TO THE NAME OF THE ACCOUNT YOU MADE FOR THE AI
        )
        self.last_message_time = 0
        self.message_cooldown = random.randint(1, 2) #ignore
        self.last_chat_response_time = 0
        self.chat_response_cooldown = random.randint(5, 70)
        self.chat_history = []
        self.transcribed_text = ""

    async def event_ready(self):
        print(f'Logged in as | {self.nick}')
        print(f'Connected channels: {[channel.name for channel in self.connected_channels]}')
        self.loop.create_task(self.periodic_chat())

    async def event_message(self, message):
        if message.echo:
            return

        print(f"Received message from {message.author.name}: {message.content}")
        self.chat_history.append(f"{message.author.name}: {message.content}")
        self.chat_history = self.chat_history[-10:]
        
        # 47% chance to respond to chat messages (if not on cooldown)
        current_time = time.time()
        if random.random() <= 0.47 and current_time - self.last_chat_response_time >= self.chat_response_cooldown:
            print("Responding to a chat message...")
            chat_context = "\n".join(self.chat_history)
            
            response = openai.ChatCompletion.create( # there's 2 of these to configure the responding to chat messages and normal timed responses, idk why tbh
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT
                    },
                    {
                        "role": "user",
                        "content": chat_context
                    }
                ],
                max_tokens=40, #this one is for responding to random chat messages
                temperature=1.0
            )
            
            bot_message = response.choices[0].message.content.strip()

            channel = self.connected_channels[0]
            await channel.send(bot_message)
            rprint(f"[blue]Chat response sent: {bot_message}[/blue]")

            self.chat_response_cooldown = random.randint(25, 170)
            self.last_chat_response_time = current_time

    async def periodic_chat(self):
        print("Starting periodic chat loop...")

        with sd.InputStream(callback=audio_callback, channels=1, samplerate=16000):
            while True:
                try:
                    current_time = time.time()
                    time_since_last = current_time - self.last_message_time
                    rprint(f"[yellow]Time since last message: {time_since_last:.1f}s (Cooldown: {self.message_cooldown}s)[/yellow]")

                    if current_time - self.last_message_time >= self.message_cooldown:
                        print("Transcribing microphone audio...")
                        self.transcribed_text = transcribe_audio()
                        print(f"Original Transcribed text: {self.transcribed_text}")

                        chat_context = "\n".join(self.chat_history)
                        combined_context = f"{chat_context}\n Mig said: {self.transcribed_text}"

                        response = openai.ChatCompletion.create( #responding normally (timed message)
                            model="gpt-4o",
                            messages=[
                                {
                                    "role": "system",
                                    "content": SYSTEM_PROMPT
                                },
                                {
                                    "role": "user",
                                    "content": combined_context
                                }
                            ],
                            max_tokens=40,
                            temperature=1.0
                        )
                        
                        message = response.choices[0].message.content.strip()

                        #print(f"GPT Generated Message: {message}") forgot what this is for ignore

                        channel = self.connected_channels[0]
                        await channel.send(message)
                        rprint(f"[green]Message sent to channel: {message}[/green]")

                        self.message_cooldown = random.randint(25, 70)
                        self.last_message_time = current_time

                except Exception as e:
                    print(f"Error in periodic task: {e}")

                await asyncio.sleep(5)

if __name__ == "__main__":
    bot = Bot()
    bot.run()
