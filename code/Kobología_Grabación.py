#Script original por Frederic Font
#Modificado por Gustavo Castelo 

# Python requirements
# Runs on python 3
# pip install wave pyaudio python-rtmidi mido music21 

import pyaudio
import wave
import mido
import os
import time
import music21
import math
import csv

# Audio and midi config
CHUNK = 1024  # Audio buffer size
FORMAT = pyaudio.paInt16  # Audio format (16bit)
CHANNELS = 1  # Number of channels to record
RATE = 44100  # Sampling rate of the recorded files
MIDI_DEVICE_NAME = 'SBX-1 1'  # Device name of the MIDI output port
AUDIO_DEVICE_INDEX = 1  # Will use default audio device

# Sampling config

NOTE_SECONDS = 1  # Note sustain (time between note on and note off messages)
TAIL_SECONDS = 1  # Time recording after note off message
NOTE_MIN = 0  # Lowest MIDI note to sample
NOTE_MAX = 60  # Highest MIDI note to sample
NOTE_STEP = 4
WAVF_MIN = 0  # Lowest MIDI waveform to sample
WAVF_STEP= 5 # MIDI waveform step
WAVF_MAX = 126  # Highest MIDI waveform to sample

RECORDING_FOLDER = './sampling1/'  # Where the audio will be stored ('.' means current directory)

# Other config stuff
WRITE_CSV = True
RECORD_AUDIO = True

# Set MIDI and audio stuff
print('Available MIDI device names:')
for name in mido.get_output_names():
    print('\t{0}'.format(name))
try:
    outport = mido.open_output(MIDI_DEVICE_NAME)
    print(
        'Will use MIDI output port "{0}" (change that by setting \'MIDI_DEVICE_NAME\' in sampler.py)'.format(
            MIDI_DEVICE_NAME))
except IOError:
    print('Could not connect to MIDI output port, skipping audio recording')
    RECORD_AUDIO = False
p = pyaudio.PyAudio()
print('Available audio device indexes:')
for i in range(0, p.get_device_count()):
    print('\t{0} - {1}'.format(i, p.get_device_info_by_index(i)['name']))
print(
    'Will use audio device "{0}" (change that by setting \'AUDIO_DEVICE_INDEX\' in sampler.py)'.format(
        p.get_device_info_by_index(AUDIO_DEVICE_INDEX)['name']))


def seconds_to_time_label(seconds):
    hours_remaining = math.floor(seconds / 3600)
    extra_seconds = seconds % 3600
    minutes_remaining = math.floor(extra_seconds / 60)
    seconds_remaining = extra_seconds % 60
    return '%.2i:%.2i:%.2i remaining' % (
        hours_remaining, minutes_remaining, seconds_remaining)


def start_audio_stream():
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)
    return stream


def stop_audio_stream(stream):
    stream.stop_stream()
    stream.close()


def note_off_all():
    for midi_note in range(0, 127):
        outport.send(mido.Message('note_off', note=midi_note))


def get_note_list():
    notes = []
    for midi_note in range(NOTE_MIN, NOTE_MAX,NOTE_STEP):
        for midi_wavf in range(WAVF_MIN,WAVF_MAX,WAVF_STEP):
            notes.append((midi_note,midi_wavf))
    return notes


def sample_note(midi_note,midi_wavf, output_filename, stream):
    frames = []
    print("midi note")
    print(midi_note)
    print("cc3 value")
    print(midi_wavf)
    # Send note on and start recording for NOTE_SECONDS
    outport.send(mido.Message('control_change',channel=1, control=3,value=midi_wavf))

    outport.send(mido.Message('note_on', note=midi_note))
    for i in range(0, int(RATE / CHUNK * NOTE_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)

    # Send note off and continue recording during TAIL_SECONDS
    
    outport.send(mido.Message('note_off', note=midi_note))
    for i in range(0, int(RATE / CHUNK * TAIL_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)

    wf = wave.open(output_filename, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()


textual_description_template = """Single note sampled from <a href="https://en.wikipedia.org/wiki/RSF_Kobol">RSF Kobol</a> analog monophonic synthesizer.

Synthesizer: Deckard's Dream (DDRM)
Note: %s
Midi note: %i
Midi waveform value: %i
"""


def sample_preset():
    print('\nSTARTING TO SAMPLE')

    # Stop all notes (just in case)
    if RECORD_AUDIO:
        note_off_all()

    # Start audio stream and sampling process
    if RECORD_AUDIO:
        stream = start_audio_stream()
    failed = []
    existing = []
    recorded = []
    notes = get_note_list()
    csv_rows = []
    for count, (midi_note,midi_wavf) in enumerate(notes):

        # Generate filename
        mp = music21.pitch.Pitch()
        mp.midi = midi_note
        note_name = mp.name.replace('-', 'b') + str(mp.octave)
        output_filename = '%s/Kobol - %.3i (%s) -mod_ %.3i.wav' % (
            RECORDING_FOLDER, midi_note, note_name, midi_wavf)
        print(output_filename)
        csv_rows.append(
            [  # Prepare CSV information for Freesound bulk description
                'Kobol-%.3i(%s)-mod%.3i.wav' % (
                     midi_note, note_name,midi_wavf),  # Audio filename
                'Kobol-%.3i(%s)-mod:%.3i' % (
                    midi_note,note_name,midi_wavf),  # Sound name
                ' '.join([
                    'multisample single-note synthetizer synth analogue rsf kobol %s mini-note-%i' % (
                        note_name.replace('#', 'Sharp'), midi_note)]),  # Tags
                '',  # Geotag
                textual_description_template % (
                    note_name, midi_note, midi_wavf),
                # Textual description
                'Creative Commons 0',  # License
                'nombrepack', #Pack name
                '0',  # Is explicit
            ])

        if not os.path.exists(output_filename) and RECORD_AUDIO:
            seconds_remaining = (len(notes) - count) * (
                    NOTE_SECONDS + TAIL_SECONDS)
            time_remaining_label = seconds_to_time_label(seconds_remaining)
            print("* recording {0} - [{1}/{2}] - {3}".format(midi_note,
                                                                 count + 1,
                                                                 len(notes),
                                                                 time_remaining_label))
            try:
                sample_note(midi_note,midi_wavf, output_filename, stream)
                recorded.append(output_filename)
            except IOError:
                # If something fails, send note off and do the next note
                # At a later re-run failed notes can be fixed
                print('ERROR with {0}, skipping'.format(output_filename))
                outport.send(mido.Message('note_off', note=midi_note))
                failed.append(output_filename)
                stream = start_audio_stream()  # restart audio stream
        else:
            existing.append(output_filename)

    if RECORD_AUDIO:
        stop_audio_stream(stream)
        note_off_all()

    print('DONE SAMPLING')
    if RECORD_AUDIO:
        print('{0} notes recorded successfully'.format(len(recorded)))
        print('{0} notes already existing'.format(len(existing)))
        print('{0} notes failed recording'.format(len(failed)))
    else:
        print('No new notes were recorded (audio recording disabled)')
    return failed, csv_rows


if RECORD_AUDIO:
    note_off_all()

expected_total_time = len(range(WAVF_MIN,WAVF_MAX,WAVF_STEP))* len(range(NOTE_MIN, NOTE_MAX)) * (NOTE_SECONDS + TAIL_SECONDS)
print("Expected time{0}".format(expected_total_time))
time_remaining_label = seconds_to_time_label(expected_total_time)
if RECORD_AUDIO:
    input(
        '\n\nWill start sampling, you want to continue? (will take approx {0})'.format(
             time_remaining_label))

while True:
    failed, csv_rows = sample_preset()
    if not failed:
        if WRITE_CSV:
            csv_filename = 'RSF descriptions.csv'
            csv_header = ['audio_filename', 'name', 'tags', 'geotag',
                            'description', 'license', 'pack_name',
                            'is_explicit']
            csvfile = csv.writer(open(csv_filename, 'w'))
            csvfile.writerow(csv_header)
            csvfile.writerows(csv_rows)
            print('CSV output saved in %s' % csv_filename)
        break  # Break while loop if no sounds failed, otherwise run it again

p.terminate()

