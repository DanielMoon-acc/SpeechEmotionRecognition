import numpy as np
import streamlit as st
import cv2
import librosa
import librosa.display
from tensorflow.keras.models import load_model
import os
from datetime import datetime
import streamlit.components.v1 as components
import matplotlib.pyplot as plt
from PIL import Image
from melspec import plot_colored_polar, plot_melspec

# load models
model = load_model("model3.h5")

# constants
starttime = datetime.now()

CAT6 = ['fear', 'angry', 'neutral', 'happy', 'sad', 'surprise']
CAT3 = ["positive", "neutral", "negative"]

COLOR_DICT = {"neutral": "grey",
              "positive": "green",
              "happy": "green",
              "surprise": "orange",
              "fear": "purple",
              "negative": "red",
              "angry": "red",
              "sad": "lightblue",
              "disgust": "brown"}

TEST_CAT = ['fear', 'disgust', 'neutral', 'happy', 'sad', 'surprise', 'angry']
TEST_PRED = np.array([.3, .3, .4, .1, .6, .9, .1])

# page settings
st.set_page_config(page_title="Speech Emotion Recognition", page_icon=":speech_balloon:", layout="wide")

# @st.cache
def log_file(txt=None):
    with open("log.txt", "a") as f:
        datetoday = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        f.write(f"{txt} - {datetoday};\n")


# @st.cache
def save_audio(file):
    if file.size > 4000000:
        return 1
    
    folder = "audio"
    datetoday = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))

    try:
        with open("log0.txt", "a") as f:
            f.write(f"{file.name} - {file.size} - {datetoday};\n")
    except:
        pass

    with open(os.path.join(folder, file.name), "wb") as f:
        f.write(file.getbuffer())
    return 0


# @st.cache
def get_melspec(audio):
    y, sr = librosa.load(audio, sr=44100)
    X = librosa.stft(y)
    Xdb = librosa.amplitude_to_db(abs(X))
    img = np.stack((Xdb,) * 3, -1)
    img = img.astype(np.uint8)
    grayImage = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    grayImage = cv2.resize(grayImage, (224, 224))
    rgbImage = np.repeat(grayImage[..., np.newaxis], 3, -1)
    return (rgbImage, Xdb)


# @st.cache
def get_mfccs(audio, limit):
    y, sr = librosa.load(audio)
    a = librosa.feature.mfcc(y, sr=sr, n_mfcc=40)
    if a.shape[1] > limit:
        mfccs = a[:, :limit]
    elif a.shape[1] < limit:
        mfccs = np.zeros((a.shape[0], limit))
        mfccs[:, :a.shape[1]] = a
    return mfccs


@st.cache
def get_title(predictions, categories=CAT6):
    title = f"Detected emotion: {categories[predictions.argmax()]}"
    return title


@st.cache
def color_dict(coldict=COLOR_DICT):
    return COLOR_DICT


@st.cache
def plot_polar(fig, predictions=TEST_PRED, categories=TEST_CAT,
               title="TEST", colors=COLOR_DICT):
    

    N = len(predictions)
    ind = predictions.argmax()

    COLOR = color_sector = colors[categories[ind]]
    theta = np.linspace(0.0, 2 * np.pi, N, endpoint=False)
    radii = np.zeros_like(predictions)
    radii[predictions.argmax()] = predictions.max() * 10
    width = np.pi / 1.8 * predictions
    fig.set_facecolor("#d1d1e0")
    ax = plt.subplot(111, polar="True")
    ax.bar(theta, radii, width=width, bottom=0.0, color=color_sector, alpha=0.25)

    angles = [i / float(N) * 2 * np.pi for i in range(N)]
    angles += angles[:1]

    data = list(predictions)
    data += data[:1]
    plt.polar(angles, data, color=COLOR, linewidth=2)
    plt.fill(angles, data, facecolor=COLOR, alpha=0.25)

    ax.spines['polar'].set_color('lightgrey')
    ax.set_theta_offset(np.pi / 3)
    ax.set_theta_direction(-1)
    plt.xticks(angles[:-1], categories)
    ax.set_rlabel_position(0)
    plt.yticks([0, .25, .5, .75, 1], color="grey", size=8)
    plt.suptitle(title, color="darkblue", size=12)
    plt.title(f"BIG {N}\n", color=COLOR)
    plt.ylim(0, 1)
    plt.subplots_adjust(top=0.75)


def main():
    side_img = Image.open("images/SERLOGO.png")
    with st.sidebar:
        st.image(side_img, width=300)
    st.sidebar.subheader("Menu")
    website_menu = st.sidebar.selectbox("Menu", ("Speech Emotion Recognition",
                                                 ""))
    st.set_option('deprecation.showfileUploaderEncoding', False)

    if website_menu == "Speech Emotion Recognition":
        st.sidebar.subheader("Model")
        model_type = st.sidebar.selectbox("How would you like to predict?", ("Mixed Gender", "Female Only", "Male Only"))
        em3 = em6 = em7 = gender = False
        st.sidebar.subheader("Settings")

        st.markdown("## Upload the file")
        with st.container():
            col1, col2 = st.columns(2)
            
            with col1:
                audio_file = st.file_uploader("Upload audio file", type=['wav', 'mp3', 'ogg'])
                if audio_file is not None:
                    if not os.path.exists("audio"):
                        os.makedirs("audio")
                    path = os.path.join("audio", audio_file.name)
                    if_save_audio = save_audio(audio_file)
                    if if_save_audio == 1:
                        st.warning("File size is too large. Try another file.")
                    elif if_save_audio == 0:
                      
                        st.audio(audio_file, format='audio/wav', start_time=0)
                        try:
                            wav, sr = librosa.load(path, sr=44100)
                            Xdb = get_melspec(path)[1]
                            mfccs = librosa.feature.mfcc(wav, sr=sr)
                           
                        except Exception as e:
                            audio_file = None
                            st.error(f"Error {e} - wrong format of the file. Try another .wav file.")
                    else:
                        st.error("Unknown error")
                else:
                    if st.button("Try test file"):
                        wav, sr = librosa.load("test.wav", sr=44100)
                        Xdb = get_melspec("test.wav")[1]
                        mfccs = librosa.feature.mfcc(wav, sr=sr)
                        # display audio
                        st.audio("test.wav", format='audio/wav', start_time=0)
                        path = "test.wav"
                        audio_file = "test"
            with col2:
                if audio_file is not None:
                    fig = plt.figure(figsize=(10, 2))
                    fig.set_facecolor('#d1d1e0')
                    plt.title("Wave-form")
                    librosa.display.waveplot(wav, sr=44100)
                    plt.gca().axes.get_yaxis().set_visible(False)
                    plt.gca().axes.get_xaxis().set_visible(False)
                    plt.gca().axes.spines["right"].set_visible(False)
                    plt.gca().axes.spines["left"].set_visible(False)
                    plt.gca().axes.spines["top"].set_visible(False)
                    plt.gca().axes.spines["bottom"].set_visible(False)
                    plt.gca().axes.set_facecolor('#d1d1e0')
                    st.write(fig)
                else:
                    pass
            

        if model_type == "Mixed Gender":
            em3 = st.sidebar.checkbox("3 emotions", True)
            em6 = st.sidebar.checkbox("6 emotions", True)
            #em7 = st.sidebar.checkbox("7 emotions")
            gender = st.sidebar.checkbox("gender")

        

        else:
            st.sidebar.warning("This model is temporarily disabled")

    

        if audio_file is not None:
            st.markdown("## Analyzing...")
            if not audio_file == "test":
                st.sidebar.subheader("Audio file")
                file_details = {"Filename": audio_file.name, "FileSize": audio_file.size}
                st.sidebar.write(file_details)

            with st.container():
                col1, col2 = st.columns(2)
                with col1:
                    fig = plt.figure(figsize=(10, 2))
                    fig.set_facecolor('#d1d1e0')
                    plt.title("MFCCs")
                    librosa.display.specshow(mfccs, sr=sr, x_axis='time')
                    plt.gca().axes.get_yaxis().set_visible(False)
                    plt.gca().axes.spines["right"].set_visible(False)
                    plt.gca().axes.spines["left"].set_visible(False)
                    plt.gca().axes.spines["top"].set_visible(False)
                    st.write(fig)
                with col2:
                    fig2 = plt.figure(figsize=(10, 2))
                    fig2.set_facecolor('#d1d1e0')
                    plt.title("Mel-log-spectrogram")
                    librosa.display.specshow(Xdb, sr=sr, x_axis='time', y_axis='hz')
                    plt.gca().axes.get_yaxis().set_visible(False)
                    plt.gca().axes.spines["right"].set_visible(False)
                    plt.gca().axes.spines["left"].set_visible(False)
                    plt.gca().axes.spines["top"].set_visible(False)
                    st.write(fig2)

            if model_type == "Mixed Gender":
                st.markdown("## Predictions")
                with st.container():
                    col1, col2, col3, col4 = st.columns(4)
                    mfccs = get_mfccs(path, model.input_shape[-1])
                    mfccs = mfccs.reshape(1, *mfccs.shape)
                    pred = model.predict(mfccs)[0]

                    with col1:
                        if em3:
                            pos = pred[3] + pred[5] * .5
                            neu = pred[2] + pred[5] * .5 + pred[4] * .5
                            neg = pred[0] + pred[1] + pred[4] * .5
                            data3 = np.array([pos, neu, neg])
                            txt = "\n" + get_title(data3, CAT3)
                            fig = plt.figure(figsize=(5, 5))
                            COLORS = color_dict(COLOR_DICT)
                            plot_colored_polar(fig, predictions=data3, categories=CAT3,
                                               title=txt, colors=COLORS)
                            
                            st.write(fig)
                    with col2:
                        if em6:
                            txt = "\n" + get_title(pred, CAT6)
                            fig2 = plt.figure(figsize=(5, 5))
                            COLORS = color_dict(COLOR_DICT)
                            plot_colored_polar(fig2, predictions=pred, categories=CAT6,
                                               title=txt, colors=COLORS)
                            
                            st.write(fig2)
                   
                    with col4:
                        if gender:
                            with st.spinner('Wait for it...'):
                                gmodel = load_model("model_mw.h5")
                                gmfccs = get_mfccs(path, gmodel.input_shape[-1])
                                gmfccs = gmfccs.reshape(1, *gmfccs.shape)
                                gpred = gmodel.predict(gmfccs)[0]
                                gdict = [["Female", "woman.png"], ["Male", "man.png"]]
                                ind = gpred.argmax()
                                txt = "Predicted Gender: " + gdict[ind][0]
                                img = Image.open("images/" + gdict[ind][1])

                                fig4 = plt.figure(figsize=(3, 3))
                                fig4.set_facecolor('#d1d1e0')
                                plt.title(txt)
                                plt.imshow(img)
                                plt.axis("off")
                                st.write(fig4)


   


if __name__ == '__main__':
    main()