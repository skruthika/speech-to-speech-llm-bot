# Import necessary libraries
import streamlit as st
import speech_recognition as sr
import google.generativeai as gen_ai
import os
from dotenv import load_dotenv
from gtts import gTTS
from io import BytesIO
import pygame
import tempfile
import cv2
import numpy as np

# Load environment variables
load_dotenv()

# Initialize recognizer
recognizer = sr.Recognizer()

# Configure Google Gemini API
GOOGLE_API_KEY = 'AIzaSyAhYPPra6fcIa96tkTTYgez5QWY0ydVzb0'

if not GOOGLE_API_KEY:
    st.error("GOOGLE_API_KEY environment variable not set.")
else:
    try:
        gen_ai.configure(api_key=GOOGLE_API_KEY)
        model = gen_ai.GenerativeModel('gemini-pro')
    except Exception as e:
        st.error(f"Error configuring Google Gemini API: {e}")

# Function to convert speech to text
def speech_to_text(audio_data):
    try:
        text = recognizer.recognize_google(audio_data)
        return text
    except sr.UnknownValueError:
        return "Sorry, I did not understand that. Try again recording."
    except sr.RequestError:
        return "Sorry, there seems to be a network issue."

# Function to get response from Gemini
def get_gemini_response(prompt):
    if prompt == "Sorry, I did not understand that. Try again recording." or prompt == "Sorry, there seems to be a network issue.":
        return "Please, Speak clearly !!"
    else:
        text_prompt = "Give a response in a single line for the following prompt without emojis and symbols (give only text as output): "
        user_prompt = text_prompt + prompt
        
        # Initialize chat session if not already present
        if "chat_session" not in st.session_state:
            st.session_state.chat_session = model.start_chat(history=[])

        # Send the user's message to Gemini-Pro and get the response
        chat_session = st.session_state.chat_session
        gemini_response = chat_session.send_message(user_prompt)
        return gemini_response.text.strip()

# Function to convert text to speech and play it using pygame
def speak_text_with_pygame(text):
    # Convert text to speech
    tts = gTTS(text=text, lang='en')
    
    # Create a temporary file for the audio
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
        audio_file = temp_file.name
        tts.write_to_fp(temp_file)

    # Initialize pygame mixer and play the audio
    pygame.mixer.init()
    pygame.mixer.music.load(audio_file)
    pygame.mixer.music.play()

    # Wait until the audio is done playing
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)
    
    pygame.mixer.music.stop()  # Ensure music playback stops
    
    # Close the file and delete it after playback
    pygame.mixer.music.unload()
    os.remove(audio_file)

# Function to capture video from camera
def capture_video():
    cap = cv2.VideoCapture(0)
    stframe = st.empty()
    
    # Create the "Stop Video" button once, outside the loop
    stop_button_pressed = st.button("Stop Video", key="stop_video")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Show video frame in Streamlit app
        stframe.image(frame, channels="BGR")

        # Check if the stop button is pressed
        if stop_button_pressed:
            break

    cap.release()

# Streamlit UI
st.title("Speech-to-Speech Chatbot with Google Gemini and Live Video Capture")

# Add option to start video capture
if st.button("Start Video Capture"):
    capture_video()

# Placeholder for the "Listening..." message
status_placeholder = st.empty()

# Audio capture button
if st.button("Start Recording"):
    status_placeholder.write("Listening...")

    # Capture audio via microphone
    with sr.Microphone() as source:
        audio = recognizer.listen(source)
        user_input = speech_to_text(audio)
        st.write(f"You said: {user_input}")
    
    # Clear the "Listening..." message
    status_placeholder.empty()

# Call Gemini API to generate response if user_input has a value
if 'user_input' in locals() and user_input:
    response = get_gemini_response(user_input)
    st.write(f"Bot: {response}")

    # Convert bot response to speech and play it using pygame
    speak_text_with_pygame(response)
