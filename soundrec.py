"""Example form for receiving sound from the microphone"""
# credit to https://pypi.org/project/dash-recording-components/
import dash
from dash import html, dcc
from dash.dependencies import Input, Output, State
from dash_recording_components import AudioRecorder
import soundfile as sf
import numpy as np
import io
import base64
import dash_mantine_components as dmc
from dash_iconify import DashIconify

audio_filepath = r"C:\Users\User\Documents\GitHub\Breakdown-of-Speaker-Diarization\ambient_sample.wav"

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
    html.H1("Audio Recorder and Player"),
    dmc.Switch(id="record-switch", label="Start record", checked=False,
    offLabel=DashIconify(icon="tabler:microphone-off", width=20),
    onLabel=DashIconify(icon="mdi:microphone", width=20),
    size="lg",
    color="green",
    ),
    html.Div(id="audio-output"),
    html.Div(id="dummy-output", style={"display": "none"}),
    AudioRecorder(id="audio-recorder"),
    #for uploading any files

    # dcc.Upload(html.Button('Upload File')),
    # html.Hr(),
    # dcc.Upload(html.A('Upload File')),
    # html.Hr(),
    html.Audio(
            id="audio-player",
            controls=True,
            src=audio_filepath,
            style={"display": "block"},  # Make the player visible
        ),
        html.Button("Play Audio", id="play-button", n_clicks=0),

    dcc.Upload([
        'Drag and Drop or ', html.A('Select a File')],
         style={
        'width': '100%',
        'height': '60px',
        'lineHeight': '60px',
        'borderWidth': '1px',
        'borderStyle': 'dashed',
        'borderRadius': '5px',
        'textAlign': 'center'
        })
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
    Output("audio-player", "prop_id"),  # Update a different property
    [Input("play-button", "n_clicks")],
)
def play_audio(n_clicks):
    if n_clicks % 2 == 1:
        return "play"  # Play on odd clicks
    return "pause"  # Pause on even clicks

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