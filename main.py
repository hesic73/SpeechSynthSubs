import regex as re
import os

from google.cloud import texttospeech_v1beta1 as texttospeech
from google.cloud.texttospeech_v1beta1.types import SynthesizeSpeechRequest

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
        language_code="cmn-CN", ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
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

    for i, segment in enumerate(text_segments):
        segment = re.sub(r'<.*?>', '', segment)  # Remove SSML tags
        if i < mark_count:
            end_time = mark_times[f'mark_{i}']
        else:
            end_time = None

        segments.append((segment.strip(), start_time, end_time))
        start_time = end_time

    return segments


def save_audio_to_file(audio_content: bytes, output_file: str):
    # The response's audio_content is binary.
    with open(output_file, "wb") as out:
        # Write the response to the output file.
        out.write(audio_content)
        print(f'Audio content written to file "{output_file}"')


def synthesize_speech_from_text(text: str, output_file: str, api_key: str):
    # Convert text to SSML
    ssml, mark_count = text_to_ssml(text)

    with open('ssml.txt', 'w') as f:
        f.write(ssml)

    logger.info("SSML text written to file 'ssml.txt'")

    # Call the text-to-speech API
    response = call_text_to_speech_api(ssml, api_key)

    # Process the response to get segments with timestamps
    segments = process_response(response, ssml, mark_count)

    # Save the audio content to a file
    save_audio_to_file(response.audio_content, output_file)

    return segments


if __name__ == '__main__':
    api_key = os.environ.get('GOOGLE_API_KEY')
    text = """
    这次午宴上有一道菜叫“烧滑水”，
    对于不喜欢吃多刺鱼的外宾来说，
    这道菜并不合适，
    但毛泽东执意要加上去。
    就这样，由毛泽东钦点的烧滑水、鱼翅仔鸡、牛排这三个菜，一同端上了尼克松夫妇的餐桌。
    当尼克松及夫人知道这三道菜是毛泽东及夫人江青特意为他们安排的，感到非常高兴，而且吃得很干净。吃完之后他们连声道谢，并表示感受到了中国人民的好客之情。
    """

    segments = synthesize_speech_from_text(text, 'output.mp3', api_key)
    for segment in segments:
        print(segment)