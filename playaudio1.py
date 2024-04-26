import dash
from dash import dcc, html, Input, Output

# Define the location of your WAV file
audio_filepath = r"C:\Users\User\Documents\GitHub\Breakdown-of-Speaker-Diarization\ambient_sample.wav"

app = dash.Dash(__name__)

app.layout = html.Div(
    [
        html.Audio(id="audio-player", controls=False, src=audio_filepath),
        html.Button("Play Audio", id="play-button", n_clicks=0),
    ]
)


@app.callback(Output("audio-player", "children"), [Input("play-button", "n_clicks")])
def play_audio(n_clicks):
    if n_clicks % 2 == 1:
        return """<script>document.getElementById('audio-player').play()</script>"""
    return ""  # Clear any previous script on even clicks


if __name__ == "__main__":
    app.run_server(debug=True)