import dash
from dash import html, dcc
from dash.dependencies import Input, Output, State
from functools import lru_cache
from pathlib import Path
from dash_audio_components import Audio  # Import from dash-audio-components

# Define recording directory path
recording_dir = Path(r"C:\Users\User\Documents\GitHub\Breakdown-of-Speaker-Diarization\recordingfolder")

app = dash.Dash(__name__)
server = app.server

@lru_cache(maxsize=None)
def get_recordings():
    recordings = []
    for filename in recording_dir.glob("*.m4a"):
        recordings.append({"label": filename.name, "value": filename.name})
    return recordings

app.layout = html.Div(
    [
        html.Div(
            [
                dcc.Dropdown(
                    id="recording-dropdown",
                    options=get_recordings(),
                    clearable=False,
                )
            ]
        ),
        Audio(
            id="recording-player",
            controls=True,  # Add controls for play/pause/volume
            src="",  # Initially set source to empty string
        )
    ]
)


@app.callback(
    [Output("recording-dropdown", "options"), Output("recording-player", "src")],
    [Input("recording-dropdown", "value"), State("recording-dropdown", "options")],
)
def update_options_and_player(selected_value, options):
    new_options = get_recordings()
    if new_options != options:
        return new_options, ""  # Return new options, empty source initially
    # Only update source if a recording is selected
    if selected_value:
        recording_path = recording_dir / selected_value
        return options, recording_path.as_posix()  # Return existing options, updated source
    return options, ""  # No selection, return existing options, empty source


if __name__ == "__main__":
    app.run_server(debug=True)
