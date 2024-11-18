import os, json, torch, warnings, threading, re, gdown
import numpy as np
import sounddevice as sd

warnings.filterwarnings("ignore")

from .tacotron2.hparams import create_hparams
from .tacotron2.model import Tacotron2
from .tacotron2.layers import TacotronSTFT
from .tacotron2.audio_processing import griffin_lim
from .tacotron2.text.__init__ import text_to_sequence

from .hifigan.env import AttrDict
from .hifigan.meldataset import MAX_WAV_VALUE
from .hifigan.models import Generator

Directory = os.path.dirname(os.path.realpath(__file__))
GoogleDriveDirectory = "https://drive.google.com/uc?export=download&id="

Device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def GetHifigan(ModelName, ModelID):
    
    if not os.path.exists(f"{Directory}/models/{ModelName}"):
        gdown.download(GoogleDriveDirectory + ModelID, f"{Directory}/models/{ModelName}", quiet=False)
                
    with open(Directory + "/hifigan/config.json") as File:
        JsonConfig = json.loads(File.read())
        
    HyperParams = AttrDict(JsonConfig)
    torch.manual_seed(HyperParams.seed)
    Model = Generator(HyperParams).to(Device)
    StateDictGenerator = torch.load(f"{Directory}/models/{ModelName}", weights_only=True, map_location=Device)
    
    Model.load_state_dict(StateDictGenerator["generator"])
    Model.eval()
    Model.remove_weight_norm()
    
    return Model, HyperParams

def GetTactron2(ModelName, ModelID):
    
    if not os.path.exists(f"{Directory}/models/{ModelName}"):
        gdown.download(GoogleDriveDirectory + ModelID, f"{Directory}/models/{ModelName}", quiet=False)
        
    HyperParams = create_hparams()
    HyperParams.sampling_rate = 22050
    HyperParams.max_decoder_steps = 3000
    HyperParams.gate_threshold = 0.25
    
    Model = Tacotron2(HyperParams)
    StateDict = torch.load(f"{Directory}/models/{ModelName}", weights_only=True)["state_dict"]
    Model.load_state_dict(StateDict)
    Model.to(Device).eval().half()
    
    return Model, HyperParams

class TextToSpeech:
    def __init__(self, HifiganName, Tacotron2Name, HifiganID, Tacotron2ID, StopThreshold=0.9):
        self.HifiganModel, self.HifiganHyperParams = GetHifigan(HifiganName, HifiganID)
        self.Tacotron2Model, self.Tacotron2HyperParams = GetTactron2(Tacotron2Name, Tacotron2ID)

        self.Tacotron2Model.decoder.max_decoder_steps = 1000
        self.Tacotron2Model.decoder.gate_threshold = StopThreshold

        self.InferenceThread = None
        self.IsProcessing = False

    def StartInference(self, Text):
        if not self.IsProcessing:
            self.IsProcessing = True
            self.InferenceThread = threading.Thread(target=self.InferenceTask, args=(Text,))
            self.InferenceThread.daemon = True
            self.InferenceThread.start()

    def InferenceTask(self, Text):
        try:
            for Sentence in re.split(r'[.!?]', Text):
                CleanedSentence = re.sub(r'[^\w\s]', '', Sentence)
                    
                if CleanedSentence:
                    
                    if CleanedSentence[-1] != ";":
                        CleanedSentence = CleanedSentence + ";"
                        
                    with torch.no_grad():
                        
                        TextSequence = np.array(text_to_sequence(CleanedSentence, ["english_cleaners"]))[None, :]
                        TextSequence = torch.autograd.Variable(torch.from_numpy(TextSequence)).to(Device).long()

                        MelSpectrogram, MelSpectrogramPostnet, GateOutputs, AttentionAlignments = self.Tacotron2Model.inference(TextSequence)
                        GeneratedAudio = self.HifiganModel(MelSpectrogramPostnet.float())
                        
                        FinalAudio = GeneratedAudio.squeeze() * MAX_WAV_VALUE
                        sd.play(FinalAudio.cpu().numpy().astype("int16"), samplerate=self.Tacotron2HyperParams.sampling_rate, blocking=True)

        finally:
            self.IsProcessing = False
