"""Example form for receiving sound from the microphone"""
# credit to https://pypi.org/project/dash-recording-components/
import dash
from dash import html, clientside_callback
from dash.dependencies import Input, Output, State
from dash_recording_components import AudioRecorder
import soundfile as sf
import numpy as np
import io
import base64
import dash_mantine_components as dmc
from dash_iconify import DashIconify

app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Audio Recorder and Player"),
    dmc.Switch(id="record-switch", label="Start record", checked=False),
    html.Div(id="audio-output"),
    html.Div(id="dummy-output", style={"display": "none"}),
    AudioRecorder(id="audio-recorder")
])

audio_samples = []  

@app.callback(
    Output("audio-recorder", "recording"),
    Input("record-switch", "checked"),
    State("audio-recorder", "recording"),
    prevent_initial_call=True
)
def control_recording(record_clicks, recording):
    if record_clicks:
        return True
    else:
        return False

@app.callback(
    Output("audio-output", "children"),
    Input("record-switch", "checked"),
    prevent_initial_call=True
)
def play_audio(recorded):
    if not recorded:
        global audio_samples
        if audio_samples:
            # when we play the audio we need to convert to b64 encoded wav and provide it as a data URI
            audio_array = np.array(audio_samples)
            audio_samples = []  
            with io.BytesIO() as wav_buffer:
                sf.write(wav_buffer, audio_array, 16000, format="WAV")
                wav_bytes = wav_buffer.getvalue()
                wav_base64 = base64.b64encode(wav_bytes).decode()
                audio_src = f"data:audio/wav;base64,{wav_base64}"
                return html.Audio(src=audio_src, controls=True)
    return ""


@app.callback(
    Output("dummy-output", "children"),
    Input("audio-recorder", "audio"),
    prevent_initial_call=True
)
def update_audio(audio):
    # running list of the audio samples, aggregated on the server
    global audio_samples
    if audio is not None:
        # Update the audio samples with the new audio
        audio_samples += list(audio.values())
    return ""


if __name__ == "__main__":
    app.run_server(debug=True)