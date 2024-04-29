"""Example form for receiving sound from the microphone"""
# credit to https://pypi.org/project/dash-recording-components/
import dash
from dash import html, dcc
from dash.dependencies import Input, Output, State
from dash_recording_components import AudioRecorder
import dash_bootstrap_components as dbc
import soundfile as sf
import numpy as np
import io
import base64
import dash_mantine_components as dmc
from dash_iconify import DashIconify
from non_human_recognition.inference import predict
import torch, torchaudio
from functools import lru_cache
from pathlib import Path

audio_samples = []  
app = dash.Dash(__name__)
# app.head = html.Link(rel='stylesheet', href='/assets/style.css')

#get all recording
SoundInput = Path(r"./SoundInput")

@lru_cache(maxsize=None)
def get_recordings():
    recordings = []
    for filename in SoundInput.glob("*.wav"):
        recordings.append({"label": filename.name, "value": filename.name})
    return recordings

app.layout = dbc.Container([
    # Header
    html.Br(),
    dbc.Row([
         html.H1("Non-Human"),
        html.H2("Sound Classification"),
    ],justify="center"),
    html.Br(),

    # Record
    # html.Button(children='Start', id='record', n_clicks=0),
    dbc.Row([
        dbc.Col([
            dmc.TextInput(label="Your record name:",placeholder="recording.wav",value="test.wav", w=200,id="record_name"),
            html.H4("Click to start recording"),
            # add input for naming file record
            dmc.Switch(
                id="record-switch", 
                label="Start record", 
                checked=False,
                offLabel=DashIconify(icon="tabler:microphone-off", width=20),
                onLabel=DashIconify(icon="mdi:microphone", width=20),
                size="lg",
                color="green",
                )
        ],width=5),
        dbc.Col([
            html.H3("or", )
            ],
         width=2),
        dbc.Col(
                dcc.Upload([
                    'Drag and Drop or ',
                    html.A('Select a File'),
                ]
                ,accept="wav"
                , style={
                    'width': '500px',
                    'height': '60px',
                    'lineHeight': '60px',
                    'borderWidth': '1px',
                    'borderStyle': 'dashed',
                    'borderRadius': '5px',
                    'textAlign': 'center'
                }
                 )
        )
    ], justify= "center"),
    # dat selection
    dbc.Row([
    html.H3("Select file that you want to inferences on"),
    html.Div(
            [
                dcc.Dropdown(
                    id="recording-dropdown",
                    options=get_recordings(),
                    clearable=False,
                )
            ]
    ),
    # Play Record
    html.Br(),
    html.Div(id="audio-output"),
    html.Div(id="dummy-output", style={"display": "none"}),

    AudioRecorder(id="audio-recorder"),

    html.H5("Choose the duration to predict"),
    # choose range
    html.Div([
        dmc.RangeSlider(
            id="range-slider-callback",
            value=[0,len(audio_samples)],
            mb=5,
            min=0, 
            max=len(audio_samples), 
            step=1,
            minRange=3,
            maxRange=5,
        ),
        dmc.Text(id="range-slider-output"),
    ]),
    
    #Predict button
    html.Br(),
    dmc.Button("Predict", variant="gradient", id="predict-nonhuman"),
    #Loading
    dcc.Loading(
        id="ls-loading", 
        children=[html.Div(id="ls-loading-output")], 
        type="circle", 
        style={'margin-top': '8em'}
    ),
    dmc.Text(id="nonhuman_result"),
    ])
])

# Encode the local .wav file into base64 to serve it inline
def encode_audio(audio_file_path):
    with open(audio_file_path, 'rb') as audio_file:
        base64_encoded = base64.b64encode(audio_file.read()).decode('ascii')
        mime_type = "audio/wav"
        audio_data = f"data:{mime_type};base64,{base64_encoded}"
        return audio_data
    
#sound selector
@app.callback(
    Output("audio-output", "children"),#Output("range-slider-callback", "max"),
    Input("recording-dropdown", "value"), State("recording-dropdown", "options"),
)
def update_options_and_player(selected_value, options):
    global audio_samples
    new_options = get_recordings()
    if new_options != options:
        return ""  # Return new options, empty source initially
    # Only update source if a recording is selected
    print(selected_value)
    if selected_value:
        # read file from path
        path = rf'SoundInput/{selected_value}'
        audio_src = encode_audio(path)
        audio_samples = audio_src
        out = html.Audio(src=audio_src, controls=True)
        return out  # Return existing options, updated source
    return ""
    # return options  # No selection, return existing options, empty source

#Predict button
@app.callback(
    Output("nonhuman_result", "children"),
    Output("predict-nonhuman", "n_clicks"),
    Output("ls-loading-output", "children"),
    Input("predict-nonhuman", "n_clicks"),
    Input("range-slider-callback", "value"),
    Input("recording-dropdown", "value"),
)
def get_non_human_pred(click, selected_time,filename):
    if click != None:
        if click > 0:
            sample = torch.tensor(audio_samples[16000*selected_time[0]:16000*selected_time[1]])
            # copy and paste
            # if len(sample.shape) == 1:
            #     sample = sample.repeat(2, 1)
            # print()
            # sf.write(r'SoundInput/nonhooman_sample.wav', np.array(sample), 16000)
            pred = predict(rf'SoundInput/{filename}')
            return pred, 0, None
    return "no result", 0, None

@app.callback(
    Output("range-slider-callback", "max"), Input("recording-dropdown", "value"),
)
def update_max(val):
    if val: return len(audio_samples)//16000

# update slider time range
@app.callback(
    Output("range-slider-output", "children"), Input("range-slider-callback", "value")
)
def update_value(value):
    return f"You have selected: [{value[0]}, {value[1]}]"

#swicth record mode
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

#display recording and save file recording
@app.callback(
    Output("recording-dropdown", "value"),
    Output("recording-dropdown", "options"),
    Input("record-switch", "checked"),
    Input("record_name", "value"),
    prevent_initial_call=True
)
def play_audio(recorded,record_name):
    global audio_samples
    # reset cache of record
    if recorded:
        audio_samples = []
        # return None
    # finished record exporting file
    if not recorded:
        if audio_samples:
            # when we play the audio we need to convert to b64 encoded wav and provide it as a data URI
            audio_array = np.array(audio_samples)
            # with io.BytesIO() as wav_buffer:
                # sf.write(wav_buffer, audio_array, 16000, format="WAV")
                # wav_bytes = wav_buffer.getvalue()
            path = rf'SoundInput/{record_name}'
            sf.write(path,audio_array, 16000, format="WAV")
            return path, get_recordings()
    return "", get_recordings()

#append new sample of recording
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

# ,style={'width' : '95%', 'margin' : 'auto'}
# Record
# @app.callback(Output('record', 'children'),
#               Input('record', 'n_clicks'))

# def displayClick(num_click):
#     changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
#     if 'record' in changed_id:
#         if num_click%2==0:
#             return True
#         else:
#            return False