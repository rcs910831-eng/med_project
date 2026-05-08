import google.generativeai as genai
import os

genai.configure(api_key="AIzaSyCYmQ0yvogcrKB1reCqaZY5uF-DZVHxRQ8")

print("Available models:")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
except Exception as e:
    print(f"Error: {e}")
