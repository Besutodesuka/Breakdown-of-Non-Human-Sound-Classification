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
from inference import predict
import torch, torchaudio

audio_samples = []  
app = dash.Dash(__name__)
app.head = html.Link(rel='stylesheet', href='/assets/style.css')

app.layout = html.Div([

    # Header
    html.Br(),
    html.H1("Non-Human"),
    html.H2("Sound Classification"),
    html.Br(),

    # Record
    # html.Button(children='Start', id='record', n_clicks=0),
    html.H5("Click to start recording"),
    dmc.Switch(
        id="record-switch", 
        label="Start record", 
        checked=False,
        offLabel=DashIconify(icon="tabler:microphone-off", width=20),
        onLabel=DashIconify(icon="mdi:microphone", width=20),
        size="lg",
        color="green",
    ),

    # Play Record
    html.Br(),
    html.Div(id="audio-output"),
    html.Div(id="dummy-output", style={"display": "none"}),
    AudioRecorder(id="audio-recorder"),

    #for uploading any files
    # dcc.Upload(html.Button('Upload File')),
    # html.Hr(),
    # dcc.Upload(html.A('Upload File')),
    # html.Hr(),

    # dcc.Upload([
    #     'Drag and Drop or ',
    #     html.A('Select a File')
    # ], style={
    #     'width': '100%',
    #     'height': '60px',
    #     'lineHeight': '60px',
    #     'borderWidth': '1px',
    #     'borderStyle': 'dashed',
    #     'borderRadius': '5px',
    #     'textAlign': 'center'
    # }),

    html.Div(id="audio-output"),

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
], 
style={'width' : '95%', 'margin' : 'auto'})


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

#Predict button
@app.callback(
    Output("nonhuman_result", "children"),
    Output("predict-nonhuman", "n_clicks"),
    Output("ls-loading-output", "children"),
    Input("predict-nonhuman", "n_clicks"),
    Input("range-slider-callback", "value"),
)
def get_non_human_pred(click, selected_time):
    if click > 0:
        sample = torch.tensor(audio_samples[16000*selected_time[0]:16000*selected_time[1]])
        # copy and paste
        # if len(sample.shape) == 1:
        #     sample = sample.repeat(2, 1)
        sf.write('nonhooman_sample.wav', np.array(sample), 16000)
        pred = predict('nonhooman_sample.wav')
        return pred, 0, None
    return "no result", 0, None

@app.callback(
    Output("range-slider-callback", "max"), Input("record-switch", "checked"),
)
def update_max(record):
    if not record: return len(audio_samples)//16000

@app.callback(
    Output("range-slider-output", "children"), Input("range-slider-callback", "value")
)
def update_value(value):
    return f"You have selected: [{value[0]}, {value[1]}]"

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
    global audio_samples
    if recorded:
        audio_samples = []
        return None
    if not recorded:
        if audio_samples:
            # when we play the audio we need to convert to b64 encoded wav and provide it as a data URI
            audio_array = np.array(audio_samples)
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