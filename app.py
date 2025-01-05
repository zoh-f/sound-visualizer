import numpy as np
import soundfile as sf
from flask import Flask, request, jsonify, send_file, send_from_directory, render_template
import io
import plotly.graph_objs as go
from flask_cors import CORS


app = Flask(__name__, static_folder='frontend')
CORS(app, resources={r"/*": {"origins": "*"}}) 

SAMPLING_RATE = 44100

def note_to_frequency(note):
    # mapping of notes to their corresponding positions in the chromatic scale
    note_map = {
        'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4, 'F': 5, 'F#': 6,
        'G': 7, 'G#': 8, 'A': 9, 'A#': 10, 'B': 11
    }

    # extract the note (e.g., "A") and the octave (e.g., "4")
    note_str = note[:-1]  # get the note part (e.g., 'A')
    octave = int(note[-1])  # get the octave part (e.g., 4)

    # frequency of A4 is 440 Hz
    reference_freq = 440

    # calculate the distance from A4
    note_position = note_map[note_str]
    a4_position = note_map['A']

    # number of semitones between the note and A4
    semitone_difference = note_position - a4_position

    # calculate the frequency of the note
    frequency = reference_freq * (2 ** (semitone_difference / 12)) * (2 ** (octave - 4))

    return frequency

def get_waveform(note, type, duration = 1.0, amplitude = .5):

    freq = float(note_to_frequency(note))
    amplitude = float(amplitude)

    if not isinstance(freq, (int, float)):
        raise ValueError("Frequency must be a number.")
    if not isinstance(duration, (int, float)) or duration <= 0:
        raise ValueError("Duration must be a positive number.")
    if not isinstance(amplitude, (int, float)) or not (0 <= amplitude <= 1):
        raise ValueError("Amplitude must be a number between 0 and 1.")
    
    t = np.linspace(0, duration, int(SAMPLING_RATE*duration), endpoint=False)

    match type:
        case "sine":
            waveform = np.sin(2*np.pi*freq*t)
        case "cosine":
            waveform = np.cos(2*np.pi*freq*t)
        case "square":
            waveform = np.sign(np.sin(2 * np.pi * freq * t))
        case "sawtooth":
            waveform = 2*(t * freq - np.floor(t * freq + 0.5))
    
    waveform *= amplitude
    return t, waveform


@app.route('/generate_wave', methods=['POST'])
def generate_wave():
    data = request.json
    note = data['note']
    waveform = data['waveform']
    amplitude = data['amplitude']

    wf = get_waveform(note, waveform, amplitude=amplitude)

    buffer = io.BytesIO()
    sf.write(buffer, wf[1], SAMPLING_RATE, format='ogg')
    buffer.seek(0)

    return send_file(buffer, mimetype='audio/ogg', as_attachment=True, download_name="waveform.ogg")

@app.route('/graph_wave', methods=['POST'])
def graph_wave():
    data = request.json
    # print("received data:", data)  
    note = data['note']
    waveform = data['wave_type']
    amplitude = data['amplitude']
    t, waveform = get_waveform(note, waveform, amplitude=amplitude)
    # convert NumPy arrays to lists
    t = t.tolist()  
    waveform = waveform.tolist() 
    return jsonify({'time': t, 'waveform': waveform})


@app.route('/')
def serve_frontend():
    return send_from_directory(app.static_folder, 'frontend.html')

@app.route('/frontend.html')
def frontend():
    return render_template('frontend.html')

if __name__ == '__main__':
    app.run(debug=True)

