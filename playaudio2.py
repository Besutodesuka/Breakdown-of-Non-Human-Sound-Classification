import dash
import os
from dash import dcc, html, Input, Output, State

# Define recording directory path
recording_dir = r"C:\Users\User\Documents\GitHub\Breakdown-of-Speaker-Diarization\recordingfolder"

app = dash.Dash(__name__)

# Function to list available recordings
def get_recordings():
  recordings = []
  # Implement logic to scan recording_dir and list files
  # (This is a placeholder, replace with your implementation)
  for filename in os.listdir(recording_dir):
    if filename.endswith(".m4a"):
      recordings.append({"label": filename, "value": filename})
  return recordings

app.layout = html.Div(
    [
        dcc.Dropdown(
            id="recording-dropdown",
            options=get_recordings(),
            value=None,  # Initially no selection
        ),
        html.Button("Play Audio", id="play-button", n_clicks=0),
        html.Audio(id="audio-player", controls=True, src=None),  # Initially no source
    ]
)


@app.callback(
    Output("audio-player", "src"),
    [Input("play-button", "n_clicks")],
    [State("recording-dropdown", "value")],
)
def play_audio(n_clicks, selected_file):
    if n_clicks % 2 == 1 and selected_file:
        return os.path.join(recording_dir, selected_file)  # Construct full path
    return None  # Clear source on even clicks or no selection


if __name__ == "__main__":
    app.run_server(debug=True)
