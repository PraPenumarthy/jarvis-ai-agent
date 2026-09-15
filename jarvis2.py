import datetime
import os
import sys
from google import genai
from google.genai import types
import pyttsx3
import speech_recognition as sr
from dotenv import load_dotenv
import sounddevice as sd
from scipy.io.wavfile import write

# Allows for temporary audio file creation and management
import tempfile
from pathlib import Path

load_dotenv()  # Load environment variables from .env file
gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    raise RuntimeError("GEMINI_API_KEY not found in environment variables. Please set it in your local .env file.")

# initialize gemini API client
client = genai.Client(api_key= gemini_api_key)
# start the text-to-speech engine
engine = pyttsx3.init()

# Voice settings
voices = engine.getProperty("voices")
engine.setProperty("voice", voices[17].id) # Set to "DAVID" (closest to british) voice on macOS
engine.setProperty("rate", 300)          


def speak(text):
    # Prints response to screen and speaks it aloud
    print(f"\nJARVIS: {text}")
    engine.say(text)
    engine.runAndWait()


def greet_user():
    # Greets the user based on the time of day
    hour = int(datetime.datetime.now().hour)
    if 0 <= hour < 12:
        speak("Good morning, sir.")
    elif 12 <= hour < 18:
        speak("Good afternoon, sir.")
    else:
        speak("Good evening, sir.")
    speak("Systems are fully operational. I am ready.")

# Rewritten from older model and incorporates: 
# Avoids keeping voice recordings permanently.
# Reports useful errors rather than silently swallowing every exception.
# Removes the temporary WAV file whether transcription succeeds or fails.
# Returns an empty string instead of the special "none" value.

def take_command() -> str:
    #Record one voice command and return its transcription.
    recognizer = sr.Recognizer()
    sample_rate = 44100
    recording_seconds = 6

    print("\n[Listening...]")

    try:
        recording = sd.rec(
            int(recording_seconds * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype="int16",
        )
        sd.wait()

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_path = Path(temp_file.name)

        try:
            write(temp_path, sample_rate, recording)

            print("[Processing voice...]")
            with sr.AudioFile(str(temp_path)) as source:
                audio = recognizer.record(source)

            query = recognizer.recognize_google(audio, language="en-US")
            print(f"You: {query}")
            return query.lower().strip()

        finally:
            temp_path.unlink(missing_ok=True)

    except sr.UnknownValueError:
        print("[No recognizable speech detected.]")
        return ""

    except sr.RequestError as error:
        print(f"[Speech-recognition service error: {error}]")
        speak("I could not reach the speech-recognition service.")
        return ""

    except Exception as error:
        print(f"[Audio error: {error}]")
        return ""


if __name__ == "__main__":
    greet_user()

    # 3. Create a continuous chat session with a system persona
    # This keeps track of conversation history automatically
    chat = client.chats.create(
        model="gemini-3.5-flash",
        config=types.GenerateContentConfig(
            system_instruction=(
                "You are JARVIS, Tony Stark's AI assistant from Iron Man. "
                "Be helpful, intelligent, loyal, and slightly witty. "
                "Crucial rule: Keep your spoken responses brief (under 3 sentences) "
                "so they sound natural when read aloud."
            )
        )
    )

    while True:
        user_input = take_command()

        if not user_input:
            continue

        # Exit commands to shut down the script safely
        if any(word in user_input for word in ["goodbye jarvis", "thank you jarvis", "quit", "exit"]):
            speak("Powering down systems. Goodbye, sir.")
            
            engine.stop()

            sys.exit(0)

            

        # 2. Local Desktop Automation 
        elif "open" in user_input:
            # Extract the app name (e.g., "open spotify" -> "spotify")
            app_name = user_input.replace("open", "").strip()
            speak(f"Opening {app_name}, sir.")
            
            # macOS native open command runs any app in your Applications folder
            os.system(f"open -a '{app_name}'")
            continue

        elif "close" in user_input or "quit app" in user_input:
            # find the app name (e.g., "close spotify" -> "spotify")
            app_name = user_input.replace("close", "").replace("quit app", "").strip()
            speak(f"Closing {app_name}.")
            
            formatted_app = app_name.title()  # Capitalizes the first letter of each word for proper app name formatting

            # Force closes the macOS application safely
            os.system(f"osascript -e 'quit app \"{formatted_app}\"'")
            continue

        elif "search" in user_input or "google" in user_input or "look up" in user_input:
            # Clean the string to grab exactly what you want to look up
            search_query = user_input.replace("search for", "").replace("search", "").replace("google", "").strip()
            if not (search_query):
                speak("I didn't catch what you wanted to search for. Please try again.")
                continue
            speak(f"Searching the web for {search_query}, sir.")
            
            import urllib.parse
            import webbrowser
            
            # Format spaces and special symbols cleanly for browser compatibility
            encoded_query = urllib.parse.quote(search_query)
            search_url = f"https://www.google.com/search?q={encoded_query}"
            
            # This opens the query directly inside your default Mac browser (Safari)
            webbrowser.open(search_url)
            continue

        # If there isn't anything to do on device, send the spoken voice string to Gemini for a response
        try:
            # Send your spoken voice string directly to the cloud LLM
            response = chat.send_message(user_input)
            speak(response.text)
        except Exception as e:
            print(f"Error communicating =with Gemini: {e}")
            speak("I encountered an internal connection error.")