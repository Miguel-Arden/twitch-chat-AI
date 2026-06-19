from openai import OpenAI
from twitchio.ext import commands
import os
from dotenv import load_dotenv
import asyncio
import time
import random
import whisper
import sounddevice as sd
import numpy as np
import queue
from rich import print as rprint
from Prompts import ANY_STREAMER

load_dotenv()

client = OpenAI(
    api_key = os.getenv("OPENAI_API_KEY")
)

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
        return whisper_model.transcribe(audio_array, fp16=False, language="en", condition_on_previous_text=False)["text"]
    return ""

class Bot(commands.Bot):
    def __init__(self):
        super().__init__(
            token=os.getenv('GREG_ACCESS'), #Twitch access token for the AI channel goes here
            prefix='!',
            initial_channels=['miguelarden_'], #replace with your twitch user
            nick="GregoryThe52" #replace this with your ai channels username
        )
        self.last_message_time = 0
        self.message_cooldown = random.randint(1, 2) #ignore
        self.last_chat_response_time = 0
        self.chat_response_cooldown = random.randint(5, 70)
        self.chat_history = []
        self.transcribed_text = ""
        self.is_generating = False
        self.cached_stream_title = "No stream info available"
        self.last_stream_fetch_time = 0
        self.stream_fetch_interval = 300  # fetch every 5 minutes

        

    async def get_stream_info(self):
        current_time = time.time()
        if current_time - self.last_stream_fetch_time >= self.stream_fetch_interval:
            try:
                streams = await self.fetch_streams(user_logins=['miguelarden_']) #replace this with your TWITCH channel name!
                if streams:
                    self.cached_stream_title = streams[0].title
                else:
                    self.cached_stream_title = "No stream info available"
                self.last_stream_fetch_time = current_time
                print(f"Stream title refreshed: {self.cached_stream_title}")
            except Exception as e:
                print(f"Error fetching stream info: {e}")
        return self.cached_stream_title

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

        current_time = time.time()
        if random.random() <= 0.65 and current_time - self.last_chat_response_time >= self.chat_response_cooldown:
            if self.is_generating:
                return
            self.is_generating = True
            try:
                print("Responding to a chat message...")
                chat_context = "\n".join(self.chat_history)

                stream_title = await self.get_stream_info()
                dynamic_prompt = ANY_STREAMER + f"\n\n***CURRENT STREAM***\nstream title is: {stream_title}"

                response = client.responses.create( # there's 2 of these to configure the responding to chat messages and normal timed responses, idk why tbh I vibecoded this one
                    model="gpt-4o",
                    input=[
                        {
                            "role": "system",
                            "content": dynamic_prompt
                        },
                        {
                            "role": "user",
                            "content": chat_context
                        }
                    ],
                    max_output_tokens=35,
                    temperature=1.0
                )

                self.session_tokens = 0
                self.session_input_tokens = 0
                self.session_output_tokens = 0

                print(
                    f"tokens used: {response.usage.total_tokens}\n "
                    f"session total: {self.session_tokens}\n "
                    f"input tokens used: {self.session_input_tokens}\n "
                )

                bot_message = response.output_text.strip()

                channel = self.connected_channels[0]
                await asyncio.sleep(1)
                await channel.send(bot_message)
                rprint(f"[blue]Chat response sent: {bot_message}[/blue]")

                self.chat_response_cooldown = random.randint(5, 30)
                self.last_chat_response_time = current_time
            finally:
                self.is_generating = False

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
                        self.transcribed_text = await asyncio.to_thread(transcribe_audio)
                        print(f"Original Transcribed text: {self.transcribed_text}")

                        if not self.transcribed_text or len(self.transcribed_text.strip()) < 6:
                            await asyncio.sleep(2)
                            continue

                        words = self.transcribed_text.strip().split()
                        if len(words) > 2 and len(set(words)) <= 2:
                            await asyncio.sleep(1)
                            continue

                        if self.is_generating:
                            await asyncio.sleep(2)
                            continue
                        self.is_generating = True
                        try:
                            chat_context = "\n".join(self.chat_history[-6:])
                            truncated_transcription = self.transcribed_text[-200:]
                            combined_context = f"{chat_context}\nUser said: {truncated_transcription}"

                            print(f"Context that greg is seeing: {combined_context}")

                            stream_title = await self.get_stream_info()
                            dynamic_prompt = ANY_STREAMER + f"\n\n***CURRENT STREAM***\nstream title is: {stream_title}"

                            response = client.responses.create(
                                model="gpt-4o",
                                input=[
                                    {
                                        "role": "system",
                                        "content": dynamic_prompt
                                    },
                                    {
                                        "role": "user",
                                        "content": combined_context
                                    }
                                ],
                                max_output_tokens=40,
                                temperature=1.0
                            )

                            self.session_tokens = 0
                            self.session_input_tokens = 0
                            self.session_output_tokens = 0

                            print(
                                f"tokens used: {response.usage.total_tokens}\n "
                                f"session total: {self.session_tokens}\n "
                                f"input tokens used: {self.session_input_tokens}\n "
                            )

                            message = response.output_text.strip()

                            channel = self.connected_channels[0]
                            await channel.send(message)
                            rprint(f"[green]Message sent to channel: {message}[/green]")

                            self.message_cooldown = random.randint(50, 140)
                            self.last_message_time = current_time
                        finally:
                            self.is_generating = False

                except Exception as e:
                    print(f"Error in periodic task: {e}")

                await asyncio.sleep(2)

if __name__ == "__main__":
    bot = Bot()
    bot.run()