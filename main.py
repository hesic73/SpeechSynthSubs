from typing import Optional, List, Tuple
import os
from datetime import datetime

from google.cloud import texttospeech_v1beta1 as texttospeech
from google.cloud.texttospeech_v1beta1.types import SynthesizeSpeechRequest

from pysubs2 import SSAFile, SSAEvent, make_time

import click
from click_option_group import optgroup, RequiredMutuallyExclusiveOptionGroup

import logging
import spacy

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

RUNS_DIR = os.path.abspath('runs')

DEFAULT_LANGUAGE_CODE = 'cmn-CN'
DEFAULT_VOICE_NAME = 'cmn-CN-Standard-A'
DEFAULT_SPACY_MODEL = 'zh_core_web_sm'


NON_DELIMITER_PUNCTUATION = ('\'', '"', '“', '”', '‘', '’', '”', '“', '、')


def text_to_ssml_and_segments(text: str, nlp) -> Tuple[str, List[Tuple[str, int]]]:
    doc = nlp(text)

    ssml_segments = []
    segments = []
    mark_index = 0
    current_segment = []

    for token in doc:
        if token.pos_ == 'PUNCT' and token.text not in NON_DELIMITER_PUNCTUATION:
            if current_segment:
                segments.append((''.join(current_segment).strip(), mark_index))
                current_segment = []
                ssml_segments.append(f'<mark name="mark_{mark_index}"/>')
                mark_index += 1
            ssml_segments.append(token.text)
        else:
            if (not (token.pos_ == 'PUNCT' and token.text in NON_DELIMITER_PUNCTUATION)) and token.text.strip():
                current_segment.append(token.text)
            ssml_segments.append(token.text)

    if current_segment:
        segments.append((''.join(current_segment).strip(), mark_index))

    ssml_text = ''.join(ssml_segments)
    return f'<speak>{ssml_text}</speak>', segments


def call_text_to_speech_api(ssml: str, api_key: str, language_code: str, voice_name: Optional[str] = None) -> texttospeech.SynthesizeSpeechResponse:
    client = texttospeech.TextToSpeechClient(
        client_options={'api_key': api_key})

    synthesis_input = texttospeech.SynthesisInput(ssml=ssml)

    voice = texttospeech.VoiceSelectionParams(
        language_code=language_code,
        name=voice_name,
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    request = SynthesizeSpeechRequest(
        input=synthesis_input, voice=voice, audio_config=audio_config, enable_time_pointing=[SynthesizeSpeechRequest.TimepointType.SSML_MARK])

    response = client.synthesize_speech(request=request)

    return response


def process_response(response: texttospeech.SynthesizeSpeechResponse, segments: List[Tuple[str, int]]) -> List[Tuple[str, float, Optional[float]]]:
    mark_times = {f'mark_{index}': None for _, index in segments}

    for timepoint in response.timepoints:
        mark_times[timepoint.mark_name] = timepoint.time_seconds

    result_segments = []
    start_time = 0

    for segment_text, mark_index in segments:
        end_time = mark_times.get(f'mark_{mark_index}')
        result_segments.append((segment_text, start_time, end_time))
        start_time = end_time

    return result_segments


def save_audio_to_file(audio_content: bytes, output_file: str):
    with open(output_file, "wb") as out:
        out.write(audio_content)
        logger.info(f'Audio content written to file "{output_file}"')


def synthesize_speech_from_text(text: str, output_dir: str, api_key: str, language_code: str, voice_name: Optional[str], spacy_model: str) -> List[Tuple[str, float, Optional[float]]]:
    nlp = spacy.load(spacy_model)
    ssml, segments = text_to_ssml_and_segments(text, nlp)

    with open(os.path.join(output_dir, 'ssml.txt'), 'w') as f:
        f.write(ssml)

    response = call_text_to_speech_api(
        ssml, api_key, language_code, voice_name)

    result_segments = process_response(response, segments)

    save_audio_to_file(response.audio_content,
                       os.path.join(output_dir, 'output.mp3'))

    return result_segments


@click.command()
@optgroup.group('Input data sources', cls=RequiredMutuallyExclusiveOptionGroup,
                help='The sources of the input data')
@optgroup.option('--file', '-f', type=click.Path(exists=True), help='Path to the input text file')
@optgroup.option('--text', '-t', help='Text to synthesize')
@click.option('--language-code', '-l', default=DEFAULT_LANGUAGE_CODE, help=f'Language code, defaults to "{DEFAULT_LANGUAGE_CODE}"')
@click.option('--voice-name', '-v', default=DEFAULT_VOICE_NAME, help=f'Voice name, defaults to "{DEFAULT_VOICE_NAME}"')
@click.option('--spacy-model', '-m', default=DEFAULT_SPACY_MODEL, help=f'SpaCy model, defaults to "{DEFAULT_SPACY_MODEL}"')
def main(file, text, language_code, voice_name, spacy_model):

    if language_code != DEFAULT_LANGUAGE_CODE:
        logger.error(
            "The script is hardcoded to load the Chinese spaCy model. If you want to use a different language, you need to modify the script.")
        exit(1)

    if file:
        with open(file, 'r') as f:
            text = f.read()
    elif text:
        text = text

    api_key = os.environ.get('GOOGLE_TTS_API_KEY')

    if not api_key:
        logger.error(
            "API key not found. Please set the 'GOOGLE_TTS_API_KEY' environment variable.")
        exit(1)

    timestamp = datetime.now().strftime("%Y%m%d_%H_%M_%S")
    output_dir = os.path.join(RUNS_DIR, timestamp)
    os.makedirs(output_dir, exist_ok=True)

    with open(os.path.join(output_dir, 'text.txt'), 'w') as f:
        f.write(text)

    segments = synthesize_speech_from_text(
        text, output_dir, api_key, language_code, voice_name, spacy_model)

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


if __name__ == '__main__':
    main()
