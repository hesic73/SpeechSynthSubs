import regex as re
import os

from datetime import datetime

from google.cloud import texttospeech_v1beta1 as texttospeech
from google.cloud.texttospeech_v1beta1.types import SynthesizeSpeechRequest

from pysubs2 import SSAFile, SSAEvent, make_time

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


RUNS_DIR = os.path.abspath('runs')


def text_to_ssml(text: str) -> str:
    # Replace newlines with blanks and squeeze multiple blanks into one
    text = re.sub(r'\s+', ' ', text).strip()

    # Define punctuation pattern and excluded characters
    pattern = r'(\p{P}+|[\r\n]+|\p{S}+)'
    excluded_chars = set('\'"“”‘’、')

    ssml_segments = []
    mark_index = 0
    i = 0
    previous_char_was_non_separator = False

    while i < len(text):
        if text[i] in excluded_chars:
            ssml_segments.append(text[i])
            i += 1
        elif re.match(pattern, text[i]):
            if previous_char_was_non_separator or i == 0:
                ssml_segments.append(f'<mark name="mark_{mark_index}"/>')
                mark_index += 1
            ssml_segments.append(text[i])
            previous_char_was_non_separator = False
            i += 1
        else:
            start = i
            while i < len(text) and not re.match(pattern, text[i]) and text[i] not in excluded_chars:
                i += 1
            ssml_segments.append(text[start:i])
            previous_char_was_non_separator = True

    ssml_text = ''.join(ssml_segments)
    return f'<speak>{ssml_text}</speak>', mark_index


def call_text_to_speech_api(ssml: str, api_key: str) -> texttospeech.SynthesizeSpeechResponse:
    # Instantiates a client
    client = texttospeech.TextToSpeechClient(
        client_options={'api_key': api_key})

    # Set the text input to be synthesized
    synthesis_input = texttospeech.SynthesisInput(ssml=ssml)

    # Build the voice request, select the language code and the ssml voice gender
    voice = texttospeech.VoiceSelectionParams(
        language_code="cmn-CN",
        name="cmn-CN-Wavenet-C",
        ssml_gender=texttospeech.SsmlVoiceGender.MALE
    )

    # Select the type of audio file you want returned
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    request = SynthesizeSpeechRequest(
        input=synthesis_input, voice=voice, audio_config=audio_config, enable_time_pointing=[SynthesizeSpeechRequest.TimepointType.SSML_MARK])

    # Perform the text-to-speech request on the text input with the selected voice parameters and audio file type
    response = client.synthesize_speech(request=request)

    return response


def process_response(response: texttospeech.SynthesizeSpeechResponse, ssml: str, mark_count: int) -> list:
    # Initialize list to hold segments with their start and end times
    segments = []
    mark_times = {f'mark_{i}': None for i in range(mark_count)}

    # Collect the time points from the response
    for timepoint in response.timepoints:
        mark_times[timepoint.mark_name] = timepoint.time_seconds

    # Split the text into segments based on the SSML marks
    text_segments = re.split(r'<mark name="mark_\d+"/>', ssml)
    start_time = 0

    # Define unwanted separators
    unwanted_separators = re.compile(r'^[\p{P}\p{S}\s]+')

    for i, segment in enumerate(text_segments):
        segment = re.sub(r'<.*?>', '', segment)  # Remove SSML tags
        # Remove leading unwanted separators
        segment = unwanted_separators.sub('', segment)
        segment = segment.strip()  # Strip leading and trailing whitespace

        if segment:  # Only add non-empty segments
            if i < mark_count:
                end_time = mark_times[f'mark_{i}']
            else:
                end_time = None

            segments.append((segment, start_time, end_time))
            start_time = end_time

    return segments


def save_audio_to_file(audio_content: bytes, output_file: str):
    # The response's audio_content is binary.
    with open(output_file, "wb") as out:
        # Write the response to the output file.
        out.write(audio_content)
        logger.info(f'Audio content written to file "{output_file}"')


def synthesize_speech_from_text(text: str, output_dir: str, api_key: str):
    # Convert text to SSML
    ssml, mark_count = text_to_ssml(text)

    with open(os.path.join(output_dir, 'ssml.txt'), 'w') as f:
        f.write(ssml)

    # Call the text-to-speech API
    response = call_text_to_speech_api(ssml, api_key)

    # Process the response to get segments with timestamps
    segments = process_response(response, ssml, mark_count)

    # Save the audio content to a file
    save_audio_to_file(response.audio_content,
                       os.path.join(output_dir, 'output.mp3'))

    return segments


if __name__ == '__main__':
    api_key = os.environ.get('GOOGLE_TTS_API_KEY')

    if not api_key:
        logger.error(
            "API key not found. Please set the 'GOOGLE_TTS_API_KEY' environment variable.")
        exit(1)

    timestamp = datetime.now().strftime("%Y%m%d_%H_%M_%S")
    output_dir = os.path.join(RUNS_DIR, timestamp)
    os.makedirs(output_dir, exist_ok=True)

    with open('input.txt', 'r') as f:
        text = f.read()
    segments = synthesize_speech_from_text(
        text, output_dir, api_key)

    sub = SSAFile()
    for segment in segments:
        text, start, end = segment

        if end is None:
            end = start + 5
            logger.warning(
                f"End time not found for segment '{text}'. Defaulting to {end} seconds.")

        sub.append(SSAEvent(start=make_time(s=start),
                   end=make_time(s=end), text=text))

    subtitle_file = os.path.join(output_dir, 'subtitles.srt')
    sub.save(subtitle_file)
    logger.info(f"Subtitles written to file '{subtitle_file}'")
