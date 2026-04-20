import tensorflow as tf
from tensorflow.keras import layers

from tensorflow.keras.applications import (
    ResNet50,
    InceptionV3,
    Xception,
    VGG16,
    EfficientNetB0,
    DenseNet121
)

from tensorflow.keras.applications.resnet50 import preprocess_input as res_preprocess
from tensorflow.keras.applications.inception_v3 import preprocess_input as inc_preprocess
from tensorflow.keras.applications.xception import preprocess_input as xcep_preprocess
from tensorflow.keras.applications.vgg16 import preprocess_input as vgg_preprocess
from tensorflow.keras.applications.efficientnet import preprocess_input as eff_preprocess

from tensorflow.keras.applications import DenseNet121
from tensorflow.keras.applications.densenet import preprocess_input as den_preprocess

severity_labels = {
    0: "No DR",
    1: "Mild",
    2: "Moderate",
    3: "Severe",
    4: "Proliferative DR"
}


def build_model(base_name):

    if base_name == "ResNet50":
        base = ResNet50(
            weights="imagenet",
            include_top=False,
            input_shape=(224, 224, 3)
        )
        preprocess = res_preprocess


    elif base_name == "InceptionV3":
        base = InceptionV3(
            weights="imagenet",
            include_top=False,
            input_shape=(224, 224, 3)
        )
        preprocess = inc_preprocess


    elif base_name == "Xception":
        base = Xception(
            weights="imagenet",
            include_top=False,
            input_shape=(224, 224, 3)
        )
        preprocess = xcep_preprocess


    elif base_name == "VGG16":
        base = VGG16(
            weights="imagenet",
            include_top=False,
            input_shape=(224, 224, 3)
        )
        preprocess = vgg_preprocess


    elif base_name == "EfficientNetB0":
        base = EfficientNetB0(
            weights="imagenet",
            include_top=False,
            input_shape=(224, 224, 3)
        )
        preprocess = eff_preprocess


    elif base_name == "DenseNet121":
        base = DenseNet121(
            weights="imagenet",
            include_top=False,
            input_shape=(224, 224, 3)
        )
        preprocess = den_preprocess


    else:
        raise ValueError("Model not supported")


    # Freeze base model
    base.trainable = False


    model = tf.keras.Sequential([
        base,
        layers.GlobalAveragePooling2D(),
        layers.Dense(256, activation="relu"),
        layers.Dropout(0.5),
        layers.Dense(5, activation="softmax")
    ])


    return model, preprocess