"""Example form for receiving sound from the microphone"""
# credit to https://pypi.org/project/dash-recording-components/

# Import
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
import os
from dash.exceptions import PreventUpdate

audio_samples = []  
app = dash.Dash(__name__)
app.head = html.Link(rel='stylesheet', href='/assets/style.css')

# Path get all record
SoundInput = Path(r"./SoundInput")

def get_recordings():
    """Returns a list of .wav files in the specified directory."""
    wav_files = [f for f in os.listdir(SoundInput) if f.endswith('.wav')]
    print(wav_files)
    return [{'label': f, 'value': f} for f in wav_files]

init_recording = get_recordings()

app.layout = html.Div([

    # Header
    html.Br(),
    html.H1("Non-Human"),
    html.H2("Sound Classification", 
        style={'padding-bottom': '0.5rem'}),
    
    html.Div([
        # Record
        dbc.Row([
            html.H5("Your record name : ", style={'display':'inline'}),
            dcc.Input(
                type="text",
                placeholder="recording.wav",
                value="test.wav", 
                id="record_name",
                style={'width' : '20rem', 'height' : '3.5rem'}
            ),
        ], style={'padding-bottom': '0.5rem'}),

        html.H5("Click to start recording"),
        html.Div([
            dmc.Button(
                DashIconify(icon="mdi:microphone", width=100, color='white'), 
                className='record',
                id="record"
            ),
            
            dmc.Button(
                DashIconify(icon="bi:stop-fill", width=100, color='white'), 
                className='stoprec',
                style={"display": "none"},
                id="stoprec"
            ),
        ], style={'text-align' : 'center'}),

        dmc.Switch(
            id="record-switch", 
            label="Start record", 
            checked=False,
            offLabel=DashIconify(icon="tabler:microphone-off", width=20),
            onLabel=DashIconify(icon="mdi:microphone", width=20),
            size="lg",
            color="green",
            style={"display": "none"}
        ),

        html.Div('or', className='hr-sect'),

        # Uploading files
        html.H5("Uploading .wav file"),

        dcc.Upload([
            'Drag and Drop or ',
            html.A('Select a File')
        ], 
        id="record-upload",
        multiple=False,
        accept='.wav',
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center'
        }),
        html.Div(id="alert-message"),

        # Select File
        html.H5("Select file that you want to inference on"),
        dcc.Dropdown(
            id="recording-dropdown",
            options=init_recording,
            clearable=False,
            style={'color':'black'},
        ),
        html.Button("Refresh", id="reload-file", className='refresh'),
        # Play Record
        html.Div(
            style={'padding-top': '1.5rem'}, 
            id="audio-output"
        ),
        html.Div(id="dummy-output", style={"display": "none"}),
        AudioRecorder(id="audio-recorder"),

        html.H5(id='len'),
        # Choose range
        html.H5("Choose the duration to inference"),
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

        # Predict button
        html.Br(),
        html.A([
            dmc.Button("Predict", variant="gradient", id="predict-nonhuman"),
        ], href="#end"),
    ]),

    # Loading
    dcc.Loading(
        id="ls-loading", 
        children=[html.Div(id="ls-loading-output")], 
        type="circle", 
        style={'margin-top': '8.5em'}
    ),

    html.Br(),
    # Result
    html.Div([
        html.Div([
            dmc.Text(
                id="nonhuman_result", 
                className='answer', 
                style={'display':'none'}),
        ], style={'width' : 'fit-content', 'margin' : 'auto'}),
    ], id="end", style={'height' : '10rem'})
], 
style={'width' : '95%', 'margin' : 'auto', 'position': 'relative'})

def save_file(name, content):
    """Decode and store a file uploaded with Plotly Dash."""
    
    # Check if the filename ends with .wav
    if not name.endswith('.wav'):
        raise PreventUpdate("File is not a .wav file.")

    # Split the content into metadata and the base64 encoded data
    content_type, content_string = content.split(',')

    # Decode the base64 data to bytes
    data = base64.b64decode(content_string)
    
    TARGET_DIR = "SoundInput"
    # Construct the file path
    file_path = os.path.join(TARGET_DIR, name)
    
    # Write the bytes to a file
    with open(file_path, "wb") as fp:
        fp.write(data)
    print(f"File {name} saved to {TARGET_DIR}")

# upload file then save
@app.callback(
    Output('alert-message', 'children'),
    Input('record-upload', 'filename'),
    Input('record-upload', 'contents')
)
def upload_audio(filename, contents):
    new_options = get_recordings()
    if filename is not None and contents is not None:
        file_extension = os.path.splitext(filename)[1]
        if file_extension != '.wav':
            return html.Div('This file type is not allowed. Please upload a .wav file.', style={'color': 'red'})
        else:
            save_file(filename, contents)
            return html.Div(f'Successfully saved {filename} to the server.', style={'color': 'green'})
        
# Encode the local .wav file into base64 to serve it inline
def encode_audio(audio_file_path):
    with open(audio_file_path, 'rb') as audio_file:
        base64_encoded = base64.b64encode(audio_file.read()).decode('ascii')
        mime_type = "audio/wav"
        audio_data = f"data:{mime_type};base64,{base64_encoded}"
        return audio_data


# upload file then save
@app.callback(
    Output("recording-dropdown", "options"),
    Input('reload-file', 'n_clicks')
)
def refresh_recordings(clicked):
    return get_recordings()

# sound selector
@app.callback(
    Output("audio-output", "children"),
    # Output("range-slider-callback", "max"),
    Input("recording-dropdown", "value"), 
    State("recording-dropdown", "options"),
)
def update_options_and_player(selected_value, options):
    global audio_samples
    audio_samples = []
    new_options = get_recordings()
    if new_options != options:
        return "" # Return new options, empty source initially
    # Only update source if a recording is selected
    print(selected_value)
    if selected_value:
        # read file from path
        path = rf'SoundInput/{selected_value}'
        audio_src = encode_audio(path)
        audio_samples = audio_src
        out = html.Audio(src=audio_src, controls=True, style={'width' : '100%'})
        return out  # Return existing options, updated source
    return ""

# Predict button
@app.callback(
    Output("nonhuman_result", "children"),
    Output("nonhuman_result", component_property='style'),
    Output("predict-nonhuman", "n_clicks"),
    Output("ls-loading-output", "children"),
    Input("predict-nonhuman", "n_clicks"),
    Input("range-slider-callback", "value"),
    Input("recording-dropdown", "value"),
)
def get_non_human_pred(click, selected_time, filename):
    if click != None:
        if click > 0:
            sample = torch.tensor(audio_samples[16000*selected_time[0]:16000*selected_time[1]])
            # copy and paste
            # if len(sample.shape) == 1:
            #     sample = sample.repeat(2, 1)
            # print()
            # sf.write(r'SoundInput/nonhooman_sample.wav', np.array(sample), 16000)
            pred = predict(rf'SoundInput/{filename}')
            return pred, {'display':'inline'}, 0, None
    return "no result", {'display':'none'}, 0, None

# Range
@app.callback(
    Output("range-slider-callback", "max"), 
    Input("recording-dropdown", "value"), 
)
def update_max(val):
    global audio_samples
    if val: return len(audio_samples)//16000

@app.callback(
    Output("range-slider-output", "children"), 
    Input("range-slider-callback", "value")
)
def update_value(value):
    return f"You have selected: [{value[0]}, {value[1]}]"

# Swicth record mode
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

# Record voice
@app.callback(
    Output("record-switch", "checked"),
    Output("record", "n_clicks"),
    Output("stoprec", "n_clicks"),
    Output("record", component_property='style'),
    Output("stoprec", component_property='style'),
    Input("record", "n_clicks"),
    Input("stoprec", "n_clicks"),
)
def recbutton(rec, notrec):
    if rec > 0:
        return True, 0, 0, {'display':'None'}, {'display':'inline'}
    elif notrec > 0:
        return False, 0, 0, {'display':'inline'}, {'display':'None'}

# Display recording and save file recording
@app.callback(
    Output("recording-dropdown", "value"),
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
            sf.write(path, audio_array, 16000, format="WAV")
            return path
    return ""

# Append new sample of recording
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