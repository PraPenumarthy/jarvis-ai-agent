# jarvis-ai-agent
Created an autonomous AI-agent in python that incorporates full desktop automation and voice recognition.

Utilizes embedded web-scraping and Google AI Studio Gemini API keys to dynamically fetch live internet data and execute multi-step automated tasks

^^ In order for the gemini-api key to work, you need to create your OWN key through Google AI Studio - otherwise it will not work.

** The voice index is mac-os specific **
Utilize the following for a comprehensive list of voices:

import pyttsx3
engine = pyttsx3.init()
voices = engine.getProperty('voices')

for index, voice in enumerate(voices):
    # Print the voice index number and its description
    print(f"Index: {index} | Name: {voice.name} | Languages: {voice.languages}")
