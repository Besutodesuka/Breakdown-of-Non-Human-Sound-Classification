# Assume each input spectrogram has 1024 time frames
from feature_extraction import ASTModelVis, make_features
import torch
from torch.cuda.amp import autocast
import joblib

input_tdim = 1024
checkpoint_path = '/content/ast/pretrained_models/audio_mdl.pth'
# now load the visualization model
ast_mdl = ASTModelVis(label_dim=527, input_tdim=input_tdim, imagenet_pretrain=True, audioset_pretrain=False)
print(f'[*INFO] load checkpoint: {checkpoint_path}')
checkpoint = torch.load(checkpoint_path, map_location='cuda')
audio_model = torch.nn.DataParallel(ast_mdl, device_ids=[0])
audio_model.load_state_dict(checkpoint)
audio_model = audio_model.to(torch.device("cuda:0"))
audio_model.eval()


filename = "non-human-recognition\classifier\svc_best.pkl"
clf = joblib.load(filename)

def extract_features(sound_sample_path):
    with torch.no_grad():
        feats = make_features(sound_sample_path, mel_bins=128)           # shape(1024, 128)
        # only feature extraction
        feats_data = feats.expand(1, input_tdim, 128)           # reshape the feature
        feats_data = feats_data.to(torch.device("cuda:0"))
        with autocast():
            output = audio_model.forward(feats_data, classifier = False)
    return output

def predict(sound_sample_path):
    feat = extract_features(sound_sample_path).cpu()
    feat = feat.reshape(1,768)
