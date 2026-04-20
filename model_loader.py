import os
from tensorflow.keras.models import load_model
from tensorflow.keras.layers import Dense

# ===== FIX KERAS VERSION ISSUE =====
class DenseFix(Dense):
    def __init__(self, *args, quantization_config=None, **kwargs):
        super().__init__(*args, **kwargs)

# ===== PREPROCESS =====
from tensorflow.keras.applications.efficientnet import preprocess_input as eff_pre
from tensorflow.keras.applications.resnet50 import preprocess_input as res_pre
from tensorflow.keras.applications.inception_v3 import preprocess_input as inc_pre
from tensorflow.keras.applications.vgg16 import preprocess_input as vgg_pre
from tensorflow.keras.applications.xception import preprocess_input as xce_pre

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "2019models")

def load(path):
    return load_model(
        path,
        compile=False,
        custom_objects={"Dense": DenseFix}
    )

MODELS = {

    "EfficientNet": {
        "model": load(os.path.join(MODEL_DIR,"2019_efficientnet_useclassweight.h5")),
        "preprocess": eff_pre
    },

    "ResNet50": {
        "model": load(os.path.join(MODEL_DIR,"2019_resnet.h5")),
        "preprocess": res_pre
    },

    "InceptionV3": {
        "model": load(os.path.join(MODEL_DIR,"2019_inception_useclassweight.h5")),
        "preprocess": inc_pre
    },

    "VGG16": {
        "model": load(os.path.join(MODEL_DIR,"2019_vgg_useclassweight.h5")),
        "preprocess": vgg_pre
    },

    "Xception": {
        "model": load(os.path.join(MODEL_DIR,"2019_xception_useclassweight.h5")),
        "preprocess": xce_pre
    }

}