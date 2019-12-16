# -*- coding: utf-8 -*-
"""Ferre_ai_collaborative_v2.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1Ai_uE-FexSykv-U-YPkBKRJF5xsbp3Ap

### Do this to make sure this notebook runs correctly:

go to Runtime ---> Change Runtime Type --->
click on Hardware Accelerator dropdown arrow --->
choose TPU ---> click Save

This makes sure that the Google server runs this notebook on the TPU, which just makes it work faster and uses substantially less CPU.

### This cell will install all the packages you need for the project to work.
Press shift+enter to run the cell.

Once you have run this cell once, you will never need to run it again.
"""

#!pip install music21
#!pip install glob     Standard library no need to install
#!pip install pickle   Same
#!pip install keras
#!pip install h5py pyyaml
#!pip install tf_nightly

"""
### This cell connects this document to your Google Drive.
"""

from google.colab import drive
drive.mount('/content/drive')

"""
### In this cell we will import the packages and functions necessary.
"""

import glob #this module helps work with files and directories
import pickle #pickle may not be necessary, but just in case, I have it here
import numpy as np #same with numpy, but numpy is always good to have just in case.
from music21 import converter, instrument, note, chord, stream, midi, roman, pitch, analysis, meter, tempo, clef #this is the music library
import time

import random
from fractions import Fraction
import itertools
import collections

"""
### This cell contains the pre-processing steps of the project.
It takes a midi file, or a folder full of midi files, and it extracts the data from them in whatever form we specify
(i.e. note, like A4, or duration, like 1.5, or offset position, etc.). It then takes these values and puts them into a list.
These are the values that will be inputted into the algorithm for learning.
"""

"""
CREATE LISTS AND SET TIME
"""

#the notes_durs list is the list that will contain the data we extract from the midi file.
#each entry in the list will be a string concatenation of each different value (note, duration, offset),
#and each string will be separated by a comma
notes_durs = []
roman_numerals = []

chord_number = 1

t0 = time.time()

"""
GET FILES
"""

#the next few lines parse through the midi file(s). Make sure your filepath is correct
for file in glob.glob("/content/drive/My Drive/Ferre_ai_collaborative/datasets/that_green/*.mid"):
    midi_score = converter.parse(file)
    print(f"parsing {file} \n")

    """
    SHOW THE SCORE
    """
    #for comparison with how final score should look
    #midi_score.show('text')

    """
    TRANSPOSE
    """

    #transpose the piece to either C major or A minor
    key_sig = midi_score.analyze("key")
    key_mode = key_sig.mode
    if key_mode == "major":
        pitch_shift = 60 - key_sig.tonic.midi
    elif key_mode == "minor":
        pitch_shift = 69 - key_sig.tonic.midi
    midi_score.transpose(pitch_shift, inPlace=True)
    #new_key_sig is used in the roman numeral analysis
    new_key_sig = midi_score.analyze("key")

    """
    CHORDIFY
    """

    if not midi_score.hasMeasures():
        original_score = midi_score.makeMeasures()

    # chordified score tells where to look for new notes
    notes_to_parse = midi_score.chordify()
    if not notes_to_parse.hasMeasures():
        notes_to_parse.makeMeasures(inPlace=True)

    """
    ROMAN NUMERAL ANALYSIS
    """

    for measure in notes_to_parse.measures(1, len(notes_to_parse)):
        beat = 0.0
        next_beat = 1.0
        if measure.timeSignature != None:
            time_sig = measure.timeSignature.numerator
            for i in range(time_sig):
                new_items = measure.getElementsByOffset(beat, next_beat)
                beat_chord = chord.Chord(new_items.pitches)

                if len({chord_pitch.name for chord_pitch in beat_chord.pitches}) >= 2:
                    for chord_pitch in beat_chord:
                        if (chord_pitch.name != beat_chord.root().name
                            and (beat_chord.third is None or chord_pitch.name != beat_chord.third.name)
                            and (beat_chord.fifth is None or chord_pitch.name != beat_chord.fifth.name)
                            and (beat_chord.seventh is None or chord_pitch.name != beat_chord.seventh.name)):

                            beat_chord.remove(chord_pitch)
                            #print("removed:" + str(chord_pitch))

                if len(beat_chord.pitches) != 0:
                    roman_numerals.append(roman.romanNumeralFromChord(beat_chord, new_key_sig).figure)
                beat += 1.0
                next_beat += 1.0

                #print("chord_number:" + str(chord_number))
                chord_number += 1
        else:
            for i in range(time_sig):
                new_items = measure.getElementsByOffset(beat, next_beat)
                beat_chord = chord.Chord(new_items.pitches)

                if len({chord_pitch.name for chord_pitch in beat_chord.pitches}) >= 2:
                    for chord_pitch in beat_chord:
                        if (chord_pitch.name != beat_chord.root().name
                            and (beat_chord.third is None or chord_pitch.name != beat_chord.third.name)
                            and (beat_chord.fifth is None or chord_pitch.name != beat_chord.fifth.name)
                            and (beat_chord.seventh is None or chord_pitch.name != beat_chord.seventh.name)):

                            beat_chord.remove(chord_pitch)
                            #print("removed:" + str(chord_pitch))

                if len(beat_chord.pitches) != 0:
                    roman_numerals.append(roman.romanNumeralFromChord(beat_chord, new_key_sig).figure)
                beat += 1.0
                next_beat += 1.0

                #print("chord_number:" + str(chord_number))
                chord_number += 1

    """
    EXTRACT NOTE DATA
    """

    # measure 0 has pickup notes
    current_measure = -1
    for element in notes_to_parse.recurse().notesAndRests:
        element_offset = str(float(element.offset))
        if element_offset == "0.0":
            current_measure += 1
            time_sig_object = original_score[current_measure].timeSignature
            if time_sig_object is not None:
                time_sig = time_sig_object.ratioString

        if isinstance(element, chord.Chord):
            new_items = original_score[current_measure].getElementsByOffset(element.offset)
            new_pitches = '.'.join(str(new_pitch.midi) for new_pitch in new_items.pitches)
            new_durations = []

            for new_event in new_items.notes:
                if isinstance(new_event, chord.Chord):
                    new_durations.extend([new_event.quarterLength for _ in new_event])
                elif isinstance(new_event, note.Note):
                    new_durations.append(new_event.quarterLength)

            # fractions from irregular rhyhtms are left intact
            new_durations = '|'.join(str(note_duration) for note_duration in new_durations)
            notes_durs.append(','.join([new_pitches, new_durations, element_offset, time_sig]))

        elif isinstance(element, note.Rest):
            element_duration = str(float(element.quarterLength))
            notes_durs.append(','.join(['N', element_duration, element_offset, time_sig]))

"""
GET UNIQUE VOCAB AND CREATE TOKENS
"""

#create a vocab variable that is the length of the unique values in notes
#the vocab is the number of unique elements in the notes_durs list and just tells us
#how many *different* elements we're working with,
#so repeated elements are excluded in this value

vocab = len(set(notes_durs))
token_dict = dict(zip(range(vocab), set(notes_durs)))

chord_vocab = set(roman_numerals)
chord_dict = dict(zip(range(len(chord_vocab)), chord_vocab))

"""
MEASURE TIME
"""

t1 = time.time()

print(f"Time to execute: {t1 - t0} \n")

"""
PRINT CHECK
"""

#everything from here to the bottom of this cell is just so you can see what you're working with and check for reasonableness

#roman numeral analysis
print(f"len(roman_numerals): {len(roman_numerals)} \n")

print(f"roman_numerals: \n {roman_numerals} \n")

print(f"len(chord_vocab): {len(chord_vocab)} \n")

print(f"chord_vocab: \n {chord_vocab} \n")

print(f"len(chord_dict): {len(chord_dict)} \n")

print(f"chord_dict: \n {chord_dict} \n")

#music data for algorithm
print(f"len(notes_durs): {len(notes_durs)} \n")

print(f"notes_durs: \n {notes_durs} \n")

print(f"vocab length: {vocab} \n")

print(f"len(token_dict): {len(token_dict)} \n")

print(f"token_dict: \n {token_dict}")

"""###Create sequences for algorithm"""

"""In this cell we convert the string list of notes into integer input that can be fed into the neural net.
sequence models process integer data like this better than categorical string data."""

#decide on a pre-determined sequence length for the input to the neural net
#You should absolutely change this number come training time and test different values.
#Most likely this will overfit
sequence_length = 20

#get all pitch names from the notes list
tokens = sorted(set(item for item in notes_durs)) ###Already created token_dict in previous cell, but this creates it in reverse

print(f"tokens: \n {tokens} \n")

#create a dictionary to map pitches to integers
token_dict = dict((token, number) for number, token in enumerate(tokens)) ###Already created token_dict in previous cell, but this creates it in reverse

print(f"len(token_dict): {len(token_dict)} \n")
print(f"token_dict: \n {token_dict} \n")

#create empty lists to store the network's inputs and outputs
#the input will be all of the notes in the order they appear in the MIDI file
#included in the pre-determined sequence length
network_input = []
#the output will be the single note following the sequence input
network_output = []

#create input sequences and the corresponding outputs
#this for loop with len(notes) - sequence_length ensures we do not go out of bounds when creating
#the input sequences (of which there will be multiple) for the notes_network_inputs
for i in range(0, len(notes_durs) - sequence_length, 1):
    #creates a sequence for input of values from i to i + sequence length
    #this means that the sequences will be overlapping, starting by one to the right upon each iteration
    sequence_in = notes_durs[i:i + sequence_length]
    #print(f"sequence_in {i}: {sequence_in}")
    #get the single note at just after the end of the sequence
    #this will be used as output
    sequence_out = notes_durs[i + sequence_length]
    #print(f"sequence_out {i}: {sequence_out}")
    #append the integer value from note_to_int represented by the
    #character (note) for the length of sequence_in
    network_input.append([token_dict[char] for char in sequence_in])
    #append the single note after the end of sequence length to notes_network_output
    network_output.append(token_dict[sequence_out])

patterns = len(network_input)

#reshape the input into a format compatible with LSTM layers
normalized_input = np.reshape(network_input, (patterns, sequence_length, 1))
#normalize input
normalized_input = normalized_input / float(vocab)

print(f"len(network_output): {len(network_output)} \n")
print(f"network_output: \n {network_output} \n")

print("network_ouptput min and max values")
print(np.array(network_output).min(), np.array(network_output).max())

network_output = np_utils.to_categorical(np.array(network_output)) #network_output = np_utils.to_categorical(np.array(network_output) + 1) #network_output = np_utils.to_categorical(np.array(network_output) - np.array(network_output).min())

"""###Create Algorithm"""

"""In this cell we create the model architecture and compile the model"""

#see Keras documentarion on this line, it's pretty straightforward
#you are basically just saying you want to create a model for sequences
#you will then add layers of different types to that sequence model using model.add()
model = Sequential()
#for the first instance of a layer, you *must* give it an input shape so it knows what shape to expect from the input data
#after this layer it does it automatically
model.add(Bidirectional(LSTM(256, input_shape = (normalized_input.shape[1], normalized_input.shape[2]), return_sequences = True)))
model.add(Dropout(0.3))
model.add(Bidirectional(LSTM(512, return_sequences = True)))
model.add(Dropout(0.3))
model.add(Bidirectional(LSTM(256)))
model.add(Dense(256))
model.add(Dropout(0.3))
#you have to make sure that when the network comes to a close, it ends with the correct number of nodes
#the number of nodes must be equal to the number of expected output classes
#in this case, that number is stored in the n_vocab, which is the number of pitches in the data
model.add(Dense(vocab))
model.add(Activation('softmax'))

#added this instance of Adam for the Bach because it was learning too slowly.
#I adjusted the learning rate to be 0.005 instead of 0.001.
#If you want it to use default settings, then get rid of this line of code
#and just use 'Adam' in the optimizer = part of the next line of code.
###Adam = optimizers.Adam(lr=0.0005, beta_1=0.9, beta_2=0.999, epsilon=None, decay=0.0, amsgrad=False)

model.compile(optimizer = 'Adam', loss = 'categorical_crossentropy')

"""In this cell, we will train the model and save it to a specific filepath"""

#decide where and in what format to save the weights of your model
filepath = "/content/drive/My Drive/Ferre_ai_collaborative/weights/that_green/v8/weights-improvement-{epoch:02d}-{loss:.4f}-bigger.hdf5"
#filepath = "/content/drive/My Drive/Ferre_ai_collaborative/weights/that_green/v8/test.hdf5"

#actually saves the weights of the model
checkpoint = ModelCheckpoint(filepath, monitor = 'loss', verbose = 0, save_best_only = True, mode = 'min')
#setting this so that it can be used as a parameter in the next line of code
#this is a list of "callbacks" which will save your model to the filepath
callbacks_list = [checkpoint]

#train the model
model.fit(normalized_input, network_output, epochs = 500, batch_size = 64, callbacks = callbacks_list)

"""###Import Other Important Things"""

"""This cell may be completely redundant, I should check that"""
#import pickle
import numpy as np
from music21 import instrument, note, stream, chord
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import Dropout
from keras.layers import LSTM
from keras.layers import Activation
from keras.layers import Bidirectional
from keras.models import load_model

"""###Recreate Model for Sequence Generation"""

"""In this cell we create the model architecture and compile the model
This time we will load the weights we have already trained"""

model = Sequential()
model.add(Bidirectional(LSTM(256, input_shape = (normalized_input.shape[1], normalized_input.shape[2]), return_sequences = True)))
model.add(Dropout(0.3))
model.add(Bidirectional(LSTM(512, return_sequences = True)))
model.add(Dropout(0.3))
model.add(Bidirectional(LSTM(256)))
model.add(Dense(256))
model.add(Dropout(0.3))
model.add(Dense(vocab))
model.add(Activation('softmax'))

#Adam = optimizers.Adam(lr=0.0005, beta_1=0.9, beta_2=0.999, epsilon=None, decay=0.0, amsgrad=False)
model.compile(optimizer = 'Adam', loss = 'categorical_crossentropy')


"""THIS IS A WORKAROUND. DO NOT USE MODEL.FIT ONCE THIS HAS BEEN RESOLVED"""
model.fit(normalized_input, network_output, epochs = 0)
"""//////////////////////////////////////////////////////////////////////"""

#load the weights that we just trained
model.load_weights('/content/drive/My Drive/Ferre_ai_collaborative/weights/that_green/v8/weights-improvement-73-1.2295-bigger.hdf5')

"""###Generate Sequences"""

"""In this cell we will begin the generation process"""

#randomly choose starting point from list of MIDI sequences for the generation
start = np.random.randint(0, len(network_input) - 1)
print(f"len(start): {len(network_input[start])}")
#create a dictionary to map the integers to notes
int_to_note = dict((number, note) for number, note in enumerate(tokens))

#create list to store the index pattern in
#start with the randomly selected starting point of start
"""what happens is that this gets fed into prediction input
and each time it goes through the for loop, you are supposed to append the resulting
index to the end of the pattern sequence, but you are also supposed to take away the
first element of the previous pattern sequence. The result should be the same length
every time, which again gets fed to prediction_input to predict the next index to add"""
pattern = network_input[start]

prediction_output = []
#result_prev = None
#result_prev = None
#replaced = False

#generate 500 notes
#feel free to change this to create longer piece
#500 notes is approx 2 minutes of music
for ix in range(500):

    prediction_input = np.reshape(pattern, (1, len(pattern), 1)) #this must be an array in order to make model.predict work

    prediction_input = prediction_input / float(vocab) #regularize the prediction input the same way we did before

    #make prediction using prediction_input
    prediction = model.predict(prediction_input, verbose = 0)

    #choose the most likely prediction
    index = np.argmax(prediction) #returns the index of the highest value, not the highest value itself

    #convert to note from int using index
    result = int_to_note[index]

    """MAY NOT NEED result_prev_prev anymore, could be enough to just get rid of any repeating ntoes
       since they now have the durations tied into their values"""
    #if result == result_prev and result_prev == result_prev_prev:
        #zero_or_one = [0, 1]
        #replace = random.choice(zero_or_one)
        #if replace == 1:
            #prediction = np.argsort(-prediction, axis = 1) #returns an array of the indices from the array sorted from smallest to largest value occuring at the index in the original array
            #replace_index = prediction[0][1]
            #result = int_to_note[replace_index]
            #print("result adjusted:")
            #print(result)
            #replaced = True
        #else:
            #replaced = False
            #continue

    #add result to prediction_output
    prediction_output.append(result)

    #if replaced == False:
    pattern = np.append(pattern, index)
    #elif replaced == True:
        #pattern = np.append(pattern, replace_index)

    #used to make sure the np.reshape reshapes correctly for the prediction_input
    pattern = pattern[1:len(pattern)]

    #result_prev_prev = result_prev
    #result_prev = result
    #replaced = False

prediction_output
