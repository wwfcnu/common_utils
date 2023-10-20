import requests

def generate_text_from_audio(audio_path, question, service_url):
    # Define the request payload as a dictionary
    payload = {
        "audio_path": audio_path,
        "question": question
    }

    # Send a POST request with JSON payload
    response = requests.post(service_url, json=payload)

    # Check the response status code
    if response.status_code == 200:
        # Return the response data
        return response.text
    else:
        # Return an error message
        return f"Error: {response.status_code} - {response.text}"

# URL of the FastAPI service
url = "http://172.16.10.13:18200/generate_text"

# Example usage of the function
audio_path = "/home/wangweifei/repository/wair/MU-LLaMA/MU-LLaMA/000029.wav"

#question = "Describe the music in detail"
#question = "What genre of music is represented by the audio"
question ="What can be inferred from the audio?"

result = generate_text_from_audio(audio_path, question, url)

# Print the result
print(result)
