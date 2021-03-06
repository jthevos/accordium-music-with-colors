################################################################################################################
# music.py      Version 4.14         05-Jan-2020       Bill Manaris, John-Anthony Thevos, Marge Marshall, Chris Benson, and Kenneth Hanson

###########################################################################
#
# This file is part of Jython Music.
#
# Copyright (C) 2011-2016 Bill Manaris, Marge Marshall, Chris Benson, and Kenneth Hanson
#
#    Jython Music is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Jython Music is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Jython Music.  If not, see <http://www.gnu.org/licenses/>.
#
###########################################################################

#
# Imports jMusic and jSyn packages into jython.  Also provides additional functionality.
#
#
# REVISIONS:
#
# 4.14	05-Jan-2020	(jt, bm)  Added capability to create arbitrary jSyn instruments easily.  User creates a class inheriting
#					from either WaveInstrument or AudioInstrument.  WaveInstrument is used for oscillator-based instruments.
#					AudioInstrument is used for audio-based (i.e., lineIn or wave file) instruments.
#					Both inherit from parent class Instrument.
#
#					The idea is to provide a simple way for users to create various synth-based instruments to use for playing
#					Scores.  Several instrument examples have also been provided.
#
# 4.13  13-Nov-2019 (bm, jt)  Updated AudioSample by adding polyphony, i.e., a number of indepedent voices.  Also, removed
#					global jSyn synthesizer.  Now, we crete a new jSyn synthesizer inside every new AudioSample.
#					Also, fixed an error in Metronome, related to removing nonRepeated functions.
#
# 4.12  18-Feb-2018 (bm)  Fixed jSyn clicking sounds between subsequent runs.  Now, when the JEM stop button is pressed,
#					we simply delete the current jSyn synthesizer instance.  This takes care of the issue.  (Before, we kept
#					accumulating active jSyn synthesizer instances in JVM memory!  This applies only to JEM which keeps the same
#					JVM running between runs of JythonMusic programs.)
#
# 4.11  21-Mar-2017 (bm)  Fixed Play.setPitchBend() to actually set the pitch bend, as it should.
#
# 4.10  16-Jan-2017 (bm)  Fixed Note.getPitch() to return REST for rest notes, as it should.
#
# 4.9   27-Dec-2016 (bm)  Fixed jMusic Note bug, where, if int pitch is given, both frequency and pitch attributes are populated, but
#					if float pitch is given (i.e., frequency in Hertz), only the frequency attribute is populated - no pitch).
#					Consequently, in the second case, calling getPitch() crashes the system.  We fix it by also calling setFrequency()
#					or setPitch() in our wrapper of the Note constructor.  Also added getPitch() and getPitchBend() to fully convert
#					a frequency to MIDI pitch information.
#
# 4.8   26-Dec-2016 (mm)  Added Envelope class for using with Play.audio().  An envelope contains a list of attack times (in milliseconds,
#					relative from the previous time) and values (to reach at those times), how long to wait (delay time, in milliseconds,
#					relative from the previous time) to get to a sustain value, and then how long to wait to reach a value of zero
#					(in milliseconds, relative from the end time).  Also modified Play.audio() to accept an Envelope as an optional parameter.
#
# 4.7   11-Nov-2016 (bm)  Small bug fix in Play.midi - now we pay attention to global instrument settings, i.e., Play.setInstrument(),
#					unless instrument has been set explicitely locally (e.g., at Phrase level).
#
# 4.6   07-Nov-2016 (bm)  Fixed inefficiency problem in Play.midi (took forever to play long scores, e.g., > 3000 notes).  Now, things work
#                   in real time again.
#
# 4.5   05-Nov-2016 (bm)  Fixed small but important bug in Play.midi (a missing variable in the part scheduling all notes in the chord list).
#
# 4.4   21-Oct-2016 (bm, mm)  Fixed clicking in Play.audio() by adding a timer to lower volume right before the ending of an audio note.
#
# 4.3   28-Aug-2016 (bm, mm)  Added Play.audio(), Play.audioNote(), Play.audioOn(), Play.audioOff(), Play.allAudioNotesOff() to
#                   play musical material via AudioSamples.  These functions parallel the corresponding Play.note(), etc. functions.
#                   The only difference is that audio samples are provided to be used in place of MIDI channels to render the music.
#                   Also fixed bug with rendering panning information in notes in Play.midi() and Play.audio().
#                   Also, if panning information is not provided in Play.noteOn(), Play.audioOn(), etc., the global Play.setPanning()
#                   info is now used.
#
# 4.2   12-Aug-2016 (bm)  Using Timer2() class (based on java.util.Timer) for Play.note(), etc.  More reliable.
#
# 4.1   28-Jul-2016 (bm, mm)  Resolved following issues with Play.midi():
#                   (a) Playback now uses length of a note (vs. its duration) to determine how long it sounds (as it should).
#                   (b) Chord durations were calculated improperly for some chord notes, due to a note sorting error.  This has been fixed by
#                   sorting noteList in Play.midi() by start time, then duration, then pitch then etc.
#                   (c) Fixed race condition which caused some notes from not turning off.  The dictionary used to hold instances of overlapping
#                   notes was changed to a list.  Now, for every note to play, a tuple of pitch and channel is added to by frequencyOn() and
#                   removed from the list by frequencyOff(), respectively. (Race condition is still present, but due to rewritten logic, it
#                   does not cause any trouble anymore.  All concurrent notes are turned off when they should.)
#
# 4.0   14-May-2016 (bm, mm)  Added microtonal capabilities.  Now, we can create and play notes using frequencies (float, in Hz),
#                   instead of pitch (0-127).  Updated new Play.midi() function to handle microtones / frequencies (by using pitchbend).
#                   Only one frequency per channel can be played accurately (since there is only one pitchbend per channel).  Regular notes
#                   can play concurrently as usual (i.e., for chords).  However, for concurrent microtones on a given channel,
#					unless they have same pitchbend, only the last microtone will be rendered accurately (all others will be affected by the
#					latest pichbend - the one used to render the last microtone - again, only one pitchbend is available per channel).
#                   To render concurrent microtones, they have to be spread across different channels.  That's the only way to render
#                   microtonal chords using MIDI (i.e., we are pushing MIDI as far as it goes here).
#                   Also, updated Play.noteOn/Off(), and Play.frequencyOn/Off() accordingly, and added a few more error checks/warnings.
#                   Additionally, now only the last note-off event for a given note-channel is executed, thus allowing overlapping notes with
#                   same pitch (e.g., overlapping A4 notes) to render more accurately.
#                   Finally, Play.setPitchBend() changes the global pitch bend, so if a certain frequency is played, it will be
#                   pitchbended if pitch bend is NOT zero. This is similar to playing any note with pitch bend set to anything other
#                   than zero.
#
# 3.9   30-Mar-2016 (bm)  Changed to new Play.midi() function.  It issues Play.note() calls, instead of using jMusic's Play.midi() -
#                   the latter usually hesitates at the beginning of playing.  New way is more robust / reliable.
#                   Old function is still available under Play.midi2().
#
# 3.8   04-Mar-2016 (bm)  Reverted back to __Active__ lists removing objects.  Not a good idea, especially when loading large audio files.
#                   We need to remove old objects, when we stop, otherwise we quickly run out of memory...
#
# 3.7   28-Feb-2016 (bm)  Updated Metronome class to improve API and implementation - updated method add() to use absolute beats (with
#                   the exception of 0, which means at the next beat), also soundOn() now takes a MIDI pitch to use and volume, as parameters.
#                   Updated __Active__ lists to not remove objects.  This way, when Stop button is pressed, all objects are stopped,
#                   even if they are not referenced in the program anymore (during Live Coding, variables may be redefined and leave
#                   orphan objects still playing - which before could only be stopped by quiting JEM!).
#
# 3.6   05-Feb-2016 (bm)  Added Metronome class - it provides for synchronization of musical tasks, especially for live coding.
#                   Methods include add(), remove(), start(), stop(), show(), hide(), soundOn(), soundOff().
#
# 3.5   17-Jan-2016 (bm)  Fixed Mod.invert() bug, which modified RESTs - now, we only invert non-REST notes.
#
# 3.4   01-Dec-2015 (bm)  Moved LiveSample to audio.py, where we can do more extensive testing for audio card formats
#                   (e.g., Little Endian), which appeared in some Windows boxes.  Also, fixed problem of Java imports
#                   overridding Python's enumerate() function.
#
# 3.3   06-May-2015 (cb)  Added LiveSample(), which implements live recording of audio, and offers
#                   an API similar to AudioSample.  Nice!
#
# 3.2   22-Feb-2015 (bm)  Added Mod.elongate() to fix a problem with jMusic's Mod.elongate (it messes up the
#                   the length of elongated notes).  Added Mod.shift() to shift the start time of material
#                   as a whole; and Mod.merge() to merge two Parts (or two Scores) into one.  Also, updated
#                   Mod.retrograde() to work with Parts and Scores, in addition to Phrases.
#
# 3.1   07-Dec-2014 (bm)  Added Note() wrapping to allow specifying length in the Note constructor (in addition
#                   to pitch, duration, dynamic, and panning.  Updated Phrase.addNoteList() and addChord() to
#                   include a length parameter.  This allows for easier specification of legato and staccato notes.
#                   Also updated Note.setDuration() to adjust the note's length proportionally.
#
# 3.0   06-Nov-2014 (bm)  Added functionality to stop AudioSample and MidiSequence objects via JEM's Stop button
#                       - see registerStopFunction().
#
# 2.9   07-Oct-2014 (bm) Resolved the various Play.midi() issues.  Andrew (Brown) fixed jMusic's MidiSynth, so
#                   we now can use it as documented.  We initialize a total of 12 MidiSynth's (which allows up to
#                   12 concurrent Play.midi()'s).  This should be sufficient for all practical purposes.
#
# 2.8   06-Sep-2014 (bm) Fixed a couple of bugs in Mod.invert() and Mod.mutate().  Also added a more meaningful
#                   error message in Phrase.addNoteList() for the common error of providing lists with different lengths.
#
# 2.7   19-Aug-2014 (bm) INDIAN_SCALE and TURKISH_SCALE were taken out because they were incorrect/misleading,
#                   as per Andrew Brown's recommendation.
#
# 2.6   29-May-2014 (bm) Added JEM's registerStopFunction() to register a callback function to be called,
#                   inside JEM, when the Stop button is pressed.  This is needed to stop Play.midi from
#                   playing music. For now, we register Play.stop(), which stops any music started through
#                   the Play class from sounding.  Also, changed stopMidiSynths() to __stopMidiSynths__()
#                   to hide it, since Play.stop() is now the right way to stop Play generated music from
#                   sounding.
#
# 2.5   27-May-2014 (bm) Added stopMidiSynths() - a function to stop all Play.midi music right away - this
#                   was needed for JEM. Also,Play.midi() returns the MIDI synthesizer used, so
#                   m = Play.midi(), followed by, m.stop(), will stop that synthesizer.
#
# 2.4   02-May-2014 (bm) Updated fixWorkingDirForJEM() solution to work with new JEM editor by Tobias Kohn.
#
# 2.3   17-Dec-2013 (bm, ng) Added AudioSample panning ranging from 0 (left) to 127 (right).  Also
#                   added Envelope class and updated AudioSample to work with it.
#
# 2.2   21-Nov-2013 Added a Play.note(pitch, start, duration, velocity=100, channel=0) function,
#                   which plays a note with given 'start' time (in milliseconds from now),
#                   'duration' (in milliseconds from 'start' time), with given 'velocity' on 'channel'.
#                   This allows scheduling of future note events, and thus should facilitate
#                   playing score-based or event-based musical material.
#
# 2.1   14-Mar-2013 Two classes - AudioSample and MidiSequence.
#
#                   AudioSample is instantiated with a string - the filename of an audio file (.wav or .aiff).
#                   It supports the following functions: play(), loop(), loop(numOfTimes), stop(), pause(), resume(),
#                   setPitch( e.g., A4 ), getPitch(), getDefaultPitch(),
#                   setFrequency( e.g., 440.0 ), getFrequency(),
#                   setVolume( 0-127 ), getVolume().
#
#                   MidiSequence is instantiated with either a string - the filename of a MIDI file (.mid), or
#                   music library material (Score, Part, Phrase, or Note).
#                   It supports the following functions: play(), loop(), stop(), pause(), resume(),
#                   setPitch( e.g., A4 ), getPitch(), getDefaultPitch(),
#                   setTempo( e.g., 80.1 ), getTempo(), getDefaultTempo(),
#                   setVolume( 0-127 ), getVolume().
#
#                   For more information on function parameters, see the class definition.
#
# 2.0  17-Feb-2012  Added jSyn synthesizer functionality.  We now have an AudioSample class for loading audio
#                   files (WAV or AIF), which can be played, looped, paused, resumed, and stopped.
#                   Also, each sound has a MIDI pitch associated with it (default is A4), so we
#                   can play different pitches with it (through pitch shifting).
#                   Finally, we improved code organization overall.
#
# 1.91 13-Feb-2013  Modified mapScale() to add an argument for the key of the scale (default is C).
#
# 1.9  10-Feb-2013  Removed Read.image() and Write.image() - no content coupling with
#                   image library anymore.
# 1.81 03-Feb-2013  Now mapScale() returns an int (since it intended to be used as
#                   a pitch value).  If we return a float, it may be confused as
#                   a note frequency (by the Note() constructor) - that would not be good.
#
# 1.8  01-Jan-2013  Redefine Jython input() function to fix problem with jython 2.5.3
#                   (see
# 1.7  30-Dec-2012  Added missing MIDI instrument constants
# 1.6  26-Nov-2012  Added Play.frequencyOn/Off(), and Play.set/getPitchBend() functions.
# 1.52 04-Nov-2012  Divided complicated mapValue() to simpler mapValue() and mapScale() functions.
# 1.51 20-Oct-2012  Restablished access to jMusic Phrase's toString() via __str__() and __repr__().
#                   Added missing jMusic constants.
#                   Added pitchSet parameter to mapValue()
# 1.5  16-Sep-2012  Added MIDI_INSTRUMENTS to be used in instrument selection menus, etc.
# 1.4  05-Sep-2012  Renamed package to 'music'.
# 1.3  17-Nov-2011  Extended jMusic Phrase, Read, Write by wrapping them in jython classes.
#

# preserve Jython bindings that get overwritten by the following Java imports - a hack!
# (also see very bottom of this file)
enumerate_preserve = enumerate


# import jMusic constants and utilities
from jm.JMC import *
from jm.util import *

from jm.music.tools import *

from jm.gui.cpn import *
from jm.gui.helper import *
from jm.gui.histogram import *
from jm.gui.show import *
from jm.gui.wave import *

from jm.audio.io import *
from jm.audio.synth import *
from jm.audio.Instrument import *

from jm.constants.Alignments import *
from jm.constants.Articulations import *
from jm.constants.DrumMap import *
from jm.constants.Durations import *
from jm.constants.Dynamics import *
from jm.constants.Frequencies import *
from jm.constants.Instruments import *
from jm.constants.Noises import *
from jm.constants.Panning import *
from jm.constants.Pitches import *
from jm.constants.ProgramChanges import *
from jm.constants.Durations import *
from jm.constants.Scales import *
from jm.constants.Tunings import *
from jm.constants.Volumes import *
from jm.constants.Waveforms import *


######################################################################################
# Jython 2.5.3 fix for input()
# see http://python.6.n6.nabble.com/input-not-working-on-Windows-td4987455.html
# also see fix at http://pydev.org/faq.html#PyDevFAQ-Whyrawinput%28%29%2Finput%28%29doesnotworkcorrectlyinPyDev%3F
def input(prompt):
   return eval( raw_input(prompt) )


######################################################################################
# redefine scales as Jython lists (as opposed to Java arrays - for cosmetic purposes)
AEOLIAN_SCALE        = list(AEOLIAN_SCALE)
BLUES_SCALE          = list(BLUES_SCALE)
CHROMATIC_SCALE      = list(CHROMATIC_SCALE)
DIATONIC_MINOR_SCALE = list(DIATONIC_MINOR_SCALE)
DORIAN_SCALE         = list(DORIAN_SCALE)
HARMONIC_MINOR_SCALE = list(HARMONIC_MINOR_SCALE)
LYDIAN_SCALE         = list(LYDIAN_SCALE)
MAJOR_SCALE          = list(MAJOR_SCALE)
MELODIC_MINOR_SCALE  = list(MELODIC_MINOR_SCALE)
MINOR_SCALE          = list(MINOR_SCALE)
MIXOLYDIAN_SCALE     = list(MIXOLYDIAN_SCALE)
NATURAL_MINOR_SCALE  = list(NATURAL_MINOR_SCALE)
PENTATONIC_SCALE     = list(PENTATONIC_SCALE)


######################################################################################
# define text labels for MIDI instruments (index in list is same as MIDI instrument number)
MIDI_INSTRUMENTS = [ # Piano Family
                     "Acoustic Grand Piano", "Bright Acoustic Piano", "Electric Grand Piano",
                    "Honky-tonk Piano", "Electric Piano 1 (Rhodes)", "Electric Piano 2 (DX)",
                    "Harpsichord", "Clavinet",

                    # Chromatic Percussion Family
                    "Celesta", "Glockenspiel", "Music Box", "Vibraphone", "Marimba",
                    "Xylophone", "Tubular Bells", "Dulcimer",

                    # Organ Family
                    "Drawbar Organ", "Percussive Organ", "Rock Organ", "Church Organ",
                    "Reed Organ", "Accordion", "Harmonica", "Tango Accordion",

                    # Guitar Family
                    "Acoustic Guitar (nylon)", "Acoustic Guitar (steel)", "Electric Guitar (jazz)",
                    "Electric Guitar (clean)", "Electric Guitar (muted)", "Overdriven Guitar",
                    "Distortion Guitar", "Guitar harmonics",

                    # Bass Family
                    "Acoustic Bass", "Electric Bass (finger)", "Electric Bass (pick)", "Fretless Bass",
                    "Slap Bass 1", "Slap Bass 2", "Synth Bass 1", "Synth Bass 2",

                    # Strings and Timpani Family
                    "Violin", "Viola", "Cello", "Contrabass", "Tremolo Strings", "Pizzicato Strings",
                    "Orchestral Harp", "Timpani",

                    # Ensemble Family
                    "String Ensemble 1", "String Ensemble 2", "Synth Strings 1", "Synth Strings 2",
                    "Choir Aahs", "Voice Oohs", "Synth Voice", "Orchestra Hit",

                    # Brass Family
                    "Trumpet", "Trombone", "Tuba", "Muted Trumpet", "French Horn",
                    "Brass Section", "SynthBrass 1", "SynthBrass 2",

                    # Reed Family
                    "Soprano Sax", "Alto Sax", "Tenor Sax", "Baritone Sax", "Oboe", "English Horn",
                    "Bassoon", "Clarinet",

                    # Pipe Family
                    "Piccolo", "Flute", "Recorder", "Pan Flute", "Blown Bottle", "Shakuhachi",
                    "Whistle", "Ocarina",

                    # Synth Lead Family
                    "Lead 1 (square)", "Lead 2 (sawtooth)", "Lead 3 (calliope)",  "Lead 4 (chiff)",
                    "Lead 5 (charang)", "Lead 6 (voice)", "Lead 7 (fifths)", "Lead 8 (bass + lead)",

                    # Synth Pad Family
                    "Pad 1 (new age)", "Pad 2 (warm)", "Pad 3 (polysynth)", "Pad 4 (choir)",
                    "Pad 5 (bowed)", "Pad 6 (metallic)", "Pad 7 (halo)", "Pad 8 (sweep)",

                    # Synth Effects Family
                    "FX 1 (rain)", "FX 2 (soundtrack)", "FX 3 (crystal)", "FX 4 (atmosphere)",
                    "FX 5 (brightness)", "FX 6 (goblins)", "FX 7 (echoes)", "FX 8 (sci-fi)",

                    # Ethnic Family
                    "Sitar",  "Banjo", "Shamisen", "Koto", "Kalimba", "Bag pipe", "Fiddle", "Shanai",

                    # Percussive Family
                    "Tinkle Bell", "Agogo", "Steel Drums", "Woodblock", "Taiko Drum", "Melodic Tom",
                    "Synth Drum", "Reverse Cymbal",

                    # Sound Effects Family
                    "Guitar Fret Noise", "Breath Noise", "Seashore", "Bird Tweet", "Telephone Ring",
                    "Helicopter", "Applause", "Gunshot" ]

# define text labels for inverse-lookup of MIDI pitches (index in list is same as MIDI pitch number)
# (for enharmonic notes, e.g., FS4 and GF4, uses the sharp version, e.g. FS4)
MIDI_PITCHES = ["C_1", "CS_1", "D_1", "DS_1", "E_1", "F_1", "FS_1", "G_1", "GS_1", "A_1", "AS_1", "B_1",
                "C0", "CS0", "D0", "DS0", "E0", "F0", "FS0", "G0", "GS0", "A0", "AS0", "B0",
                "C1", "CS1", "D1", "DS1", "E1", "F1", "FS1", "G1", "GS1", "A1", "AS1", "B1",
                "C2", "CS2", "D2", "DS2", "E2", "F2", "FS2", "G2", "GS2", "A2", "AS2", "B2",
                "C3", "CS3", "D3", "DS3", "E3", "F3", "FS3", "G3", "GS3", "A3", "AS3", "B3",
                "C4", "CS4", "D4", "DS4", "E4", "F4", "FS4", "G4", "GS4", "A4", "AS4", "B4",
                "C5", "CS5", "D5", "DS5", "E5", "F5", "FS5", "G5", "GS5", "A5", "AS5", "B5",
                "C6", "CS6", "D6", "DS6", "E6", "F6", "FS6", "G6", "GS6", "A6", "AS6", "B6",
                "C7", "CS7", "D7", "DS7", "E7", "F7", "FS7", "G7", "GS7", "A7", "AS7", "B7",
                "C8", "CS8", "D8", "DS8", "E8", "F8", "FS8", "G8", "GS8", "A8", "AS8", "B8",
                "C9", "CS9", "D9", "DS9", "E9", "F9", "FS9", "G9"]

######################################################################################
# provide additional MIDI rhythm constant

DOTTED_WHOLE_NOTE = 4.5
DWN = 4.5

######################################################################################
# provide additional MIDI pitch constants (for first octave, i.e., minus 1 octave)
BS_1 = 12
bs_1 = 12
B_1 = 11
b_1 = 11
BF_1 = 10
bf_1 = 10
AS_1 = 10
as_1 = 10
A_1 = 9
a_1 = 9
AF_1 = 8
af_1 = 8
GS_1 = 8
gs_1 = 8
G_1 = 7
g_1 = 7
GF_1 = 6
gf_1 = 6
FS_1 = 6
fs_1 = 6
F_1 = 5
f_1 = 5
FF_1 = 4
ff_1 = 4
ES_1 = 5
es_1 = 5
E_1 = 4
e_1 = 4
EF_1 = 3
ef_1 = 3
DS_1 = 3
ds_1 = 3
D_1 = 2
d_1 = 2
DF_1 = 1
df_1 = 1
CS_1 = 1
cs_1 = 1
C_1 = 0
c_1 = 0

######################################################################################
# provide additional MIDI instrument constants (missing from jMusic specification)
EPIANO1 = 4
RHODES_PIANO = 4
DX_PIANO = 5
DX = 5
DULCIMER = 15
DRAWBAR_ORGAN = 16
PERCUSSIVE_ORGAN = 17
ROCK_ORGAN = 18
TANGO_ACCORDION = 23
BANDONEON = 23
OVERDRIVEN_GUITAR = 29
DISTORTION_GUITAR = 30
SLAP_BASS1 = 36
SLAP_BASS2 = 37
SYNTH_BASS1 = 38
SYNTH_BASS2 = 39
ORCHESTRAL_HARP = 46
STRING_ENSEMBLE1 = 48
STRING_ENSEMBLE2 = 49
SYNTH = 50
SYNTH_STRINGS1 = 50
SYNTH_STRINGS2 = 51
CHOIR_AHHS = 52
VOICE_OOHS = 53
SYNTH_VOICE = 54
BRASS_SECTION = 61
SYNTH_BRASS1 = 62
SYNTH_BRASS2 = 63
BLOWN_BOTTLE = 76
LEAD_1_SQUARE = 80
LEAD_2_SAWTOOTH = 81
LEAD_3_CALLIOPE = 82
CALLIOPE = 82
LEAD_4_CHIFF = 83
CHIFF = 83
LEAD_5_CHARANG = 84
LEAD_6_VOICE = 85
LEAD_7_FIFTHS = 86
FIFTHS = 86
LEAD_8_BASS_LEAD = 87
BASS_LEAD = 87
PAD_1_NEW_AGE = 88
NEW_AGE = 88
PAD_2_WARM = 89
PAD_3_POLYSYNTH = 90
POLYSYNTH = 90
PAD_4_CHOIR = 91
SPACE_VOICE = 91
PAD_5_GLASS = 92
PAD_6_METTALIC = 93
METALLIC = 93
PAD_7_HALO = 94
HALO = 94
PAD_8_SWEEP = 95
FX_1_RAIN = 96
FX_2_SOUNDTRACK = 97
FX_3_CRYSTAL = 98
FX_4_ATMOSPHERE = 99
FX_5_BRIGHTNESS = 100
FX_6_GOBLINS = 101
GOBLINS = 101
FX_7_ECHOES = 102
ECHO_DROPS = 102
FX_8_SCI_FI = 103
SCI_FI = 103
TAIKO_DRUM = 116
MELODIC_TOM = 117
TOM_TOM = 117      # this is a fix (jMusic defines this as 119!)
GUITAR_FRET_NOISE = 120
FRET_NOISE = 120
BREATH_NOISE = 121
BIRD_TWEET = 123
TELEPHONE_RING = 124
GUNSHOT = 127

# and MIDI drum and percussion abbreviations
ABD = 35
BASS_DRUM = 36
BDR = 36
STK = 37
SNARE = 38
SNR = 38
CLP = 39
ESN = 40
LFT = 41
CHH = 42
HFT = 43
PHH = 44
LTM = 45
OHH = 46
LMT = 47
HMT = 48
CC1 = 49
HGT = 50
RC1 = 51
CCM = 52
RBL = 53
TMB = 54
SCM = 55
CBL = 56
CC2 = 57
VSP = 58
RC2 = 59
HBG = 60
LBG = 61
MHC = 62
OHC = 63
LCG = 64
HTI = 65
LTI = 66
HAG = 67
LAG = 68
CBS = 69
MRC = 70
SWH = 71
LWH = 72
SGU = 73
LGU = 74
CLA = 75
HWB = 76
LWB = 77
MCU = 78
OCU = 79
MTR = 80
OTR = 81


######################################################################################
#### Free music library functions ####################################################
######################################################################################

def mapValue(value, minValue, maxValue, minResultValue, maxResultValue):
   """
   Maps value from a given source range, i.e., (minValue, maxValue),
   to a new destination range, i.e., (minResultValue, maxResultValue).
   The result will be converted to the result data type (int, or float).
   """
   # check if value is within the specified range
   if value < minValue or value > maxValue:
      raise ValueError("value, " + str(value) + ", is outside the specified range, " \
                                 + str(minValue) + " to " + str(maxValue) + ".")

   # we are OK, so let's map
   value = float(value)  # ensure we are using float (for accuracy)
   normal = (value - minValue) / (maxValue - minValue)   # normalize source value

   # map to destination range
   result = normal * (maxResultValue - minResultValue) + minResultValue

   destinationType = type(minResultValue)  # find expected result data type
   result = destinationType(result)        # and apply it

   return result

def mapScale(value, minValue, maxValue, minResultValue, maxResultValue, scale=CHROMATIC_SCALE, key=None):
   """
   Maps value from a given source range, i.e., (minValue, maxValue), to a new destination range, i.e.,
   (minResultValue, maxResultValue), using the provided scale (pitch row) and key.  The scale provides
   a sieve (a pattern) to fit the results into.  The key determines how to shift the scale pattern to
   fit a particular key - if key is not provided, we assume it is the same as minResultValue (e.g., C4
   and C5 both refer to the key of C)).

   The result will be within the destination range rounded to closest pitch in the
   provided pitch row.   It always returns an int (since it is intended to be used
   as a pitch value).

   NOTE:  We are working within a 12-step tonal system (MIDI), i.e., octave is 12 steps away,
          so pitchRow must contain offsets (from the root) between 0 and 11.
   """
   # check if value is within the specified range
   if value < minValue or value > maxValue:
      raise ValueError("value, " + str(value) + ", is outside the specified range, " \
                                 + str(minValue) + " to " + str(maxValue) + ".")

   # check pitch row - it should contain offsets only from 0 to 11
   badOffsets = [offset for offset in scale if offset < 0 or offset > 11]
   if badOffsets != []:  # any illegal offsets?
      raise TypeError("scale, " + str(scale) + ", should contain values only from 0 to 11.")

   # figure out key of scale
   if key == None:             # if they didn't specify a key
      key = minResultValue % 12   # assume that minResultValue the root of the scale
   else:                       # otherwise,
      key = key % 12              # ensure it is between 0 and 11 (i.e., C4 and C5 both mean C, or 0).

   # we are OK, so let's map
   value = float(value)  # ensure we are using float (for accuracy)
   normal = (value - minValue) / (maxValue - minValue)   # normalize source value

   # NOTE:  The following calculation has a problem, exhibited below:
   #
   #   >>> x = 0
   #   >>> mapScale(x, 0, 10, 127, 0, MAJOR_SCALE)
   #   127
   #
   #   This is fine.
   #
   #   >>> x = 10
   #   >>> mapScale(x, 0, 10, 127, 0, MAJOR_SCALE)
   #   11
   #
   #   Problem:  This should be 0, not 11 !!

   # map to destination range (i.e., chromatic scale)
   # (subtracting 'key' aligns us with indices in the provided scale - we need to add it back later)
   chromaticStep = normal * (maxResultValue - minResultValue) + minResultValue - key

   # map to provided pitchRow scale
   pitchRowStep = chromaticStep * len(scale) / 12   # note in pitch row
   scaleDegree  = int(pitchRowStep % len(scale))    # find index into pitchRow list
   register     = int(pitchRowStep / len(scale))    # find pitch register (e.g. 4th, 5th, etc.)

   # calculate the octave (register) and add the pitch displacement from the octave.
   result = register * 12 + scale[scaleDegree]

   # adjust for key (scale offset)
   result = result + key

   # now, result has been sieved through the pitchSet (adjusted to fit the pitchSet)

   #result = int(round(result))   # force an int data type
   result = int(result)   # force an int data type

   return result

def frange(start, stop, step):
   """
   A range function for floats, with variable accuracy (controlled by
   number of digits in decimal part of 'step').
   """
   import math

   if step == 0:   # make sure we do not get into an infinite loop
     raise ValueError, "frange() step argument must not be zero"

   result = []                         # holds resultant list
   # since Python's represetation of real numbers may not be exactly what we expect,
   # let's round to the number of decimals provided in 'step'
   accuracy = len(str(step-int(step))[1:])-1  # determine number of decimals in 'step'

   # determine which termination condition to use
   if step > 0:
      done = start >= stop
   else:
      done = start <= stop

   # generate sequence
   while not done:
      start = round(start, accuracy)  # use same number of decimals as 'step'
      result.append(start)
      start += step
      # again, determine which termination condition to use
      if step > 0:
         done = start >= stop
      else:
         done = start <= stop

   return result

def xfrange(start, stop, step):
   """
   A generator range function for floats, with variable accuracy (controlled by
   number of digits in decimal part of 'step').
   """
   import math

   if step == 0:   # make sure we do not get into an infinite loop
     raise ValueError, "frange() step argument must not be zero"

   # since Python's represetation of real numbers may not be exactly what we expect,
   # let's round to the number of decimals provided in 'step'
   accuracy = len(str(step-int(step))[1:])-1  # determine number of decimals in 'step'

   # determine which termination condition to use
   if step > 0:
      done = start >= stop
   else:
      done = start <= stop

   # generate sequence
   while not done:
      start = round(start, accuracy)  # use same number of decimals as 'step'
      yield start
      start += step
      # again, determine which termination condition to use
      if step > 0:
         done = start >= stop
      else:
         done = start <= stop

######################################################################################
#### jMusic library extensions #########################################################
######################################################################################

# A wrapper to turn class functions into "static" functions (e.g., for Mod functions).
#
# See http://code.activestate.com/recipes/52304-static-methods-aka-class-methods-in-python/
#

class Callable:
    def __init__(self, functionName):
        self.__call__ = functionName


######################################################################################
#### jMusic Mod extensions #########################################################
######################################################################################

from jm.music.tools import Mod as jMod  # needed to wrap more functionality below

# Create various Mod functions, in addition to Mod's default functionality.
# This class is not meant to be instantiated, hence no "self" in function definitions.
# Functions are made callable through class Callable, above.

class Mod(jMod):

   def normalize(material):
      """Same as jMod.normalise()."""

      jMod.normalise(material)

   def invert(phrase, pitchAxis):
      """Invert phrase using pitch as the mirror (pivot) axis."""

      # traverse list of notes, and adjust pitches accordingly
      for note in phrase.getNoteList():

         if not note.isRest():  # modify regular notes only (i.e., do not modify rests)

            invertedPitch = pitchAxis + (pitchAxis - note.getPitch())  # find mirror pitch around axis (by adding difference)
            note.setPitch( invertedPitch )                             # and update it

      # now, all notes have been updated

   def mutate(phrase):
      """Same as jMod.mutate()."""

      # adjust jMod.mutate() to use random durations from phrase notes
      durations = [note.getDuration() for note in phrase.getNoteList()]

      jMod.mutate(phrase, 1, 1, CHROMATIC_SCALE, phrase.getLowestPitch(),
                  phrase.getHighestPitch(), durations)

   def elongate(material, scaleFactor):
      """Same as jMod.elongate(). Fixing a bug."""

      # define helper functions
      def elongateNote(note, scaleFactor):
         """Helper function to elongate a single note."""
         note.setDuration( note.getDuration() * scaleFactor)

      def elongatePhrase(phrase, scaleFactor):
         """Helper function to elongate a single phrase."""
         for note in phrase.getNoteList():
            elongateNote(note, scaleFactor)

      def elongatePart(part, scaleFactor):
         """Helper function to elongate a single part."""
         for phrase in part.getPhraseList():
            elongatePhrase(phrase, scaleFactor)

      def elongateScore(score, scaleFactor):
         """Helper function to elongate a score."""
         for part in score.getPartList():
            elongatePart(part, scaleFactor)

      # check type of material and call the appropriate function
      if type(material) == Score:
         elongateScore(material, scaleFactor)
      elif type(material) == Part:
         elongatePart(material, scaleFactor)
      elif type(material) == Phrase or type(material) == jPhrase:
         elongatePhrase(material, scaleFactor)
      elif type(material) == Note:
         elongateNote(material, scaleFactor)
      else:   # error check
         raise TypeError( "Unrecognized time type " + str(type(material)) + " - expected Note, Phrase, Part, or Score." )

   def shift(material, time):
      """It shifts all phrases' start time by 'time' (measured in QN's, i.e., 1.0 equals QN).
         If 'time' is positive, phrases are moved later.
         If 'time' is negative, phrases are moved earlier (at most, at the piece's start time, i.e., 0.0),
         as negative start times make no sense.
         'Material' can be Phrase, Part, or Score (since Notes do not have a start time).
      """

      # define helper functions
      def shiftPhrase(phrase, time):
         """Helper function to shift a single phrase."""
         newStartTime = phrase.getStartTime() + time
         newStartTime = max(0, newStartTime)          # ensure that the new start time is at most 0 (negative start times make no sense)
         phrase.setStartTime( newStartTime )

      def shiftPart(part, time):
         """Helper function to shift a single part."""
         for phrase in part.getPhraseList():
            shiftPhrase(phrase, time)

      def shiftScore(score, time):
         """Helper function to shift a score."""
         for part in score.getPartList():
            shiftPart(part, time)

      # check type of time
      if not (type(time) == float or type(time) == int):
         raise TypeError( "Unrecognized time type " + str(type(time)) + " - expected int or float." )

      # check type of material and call the appropriate function
      if type(material) == Score:
         shiftScore(material, time)
      elif type(material) == Part:
         shiftPart(material, time)
      elif type(material) == Phrase or type(material) == jPhrase:
         shiftPhrase(material, time)
      else:   # error check
         raise TypeError( "Unrecognized material type " + str(type(material)) + " - expected Phrase, Part, or Score." )

   def merge(material1, material2):
      """Merges 'material2' into 'material1'.  'Material1' is changed, 'material2' is unmodified.
         Both 'materials' must be of the same type, either Part or Score.
         It does not worry itself about instrument and channel assignments - it is left to the caller
         to ensure that the two 'materials' are compatible this way.
      """

      # define helper functions
      def mergeParts(part1, part2):
         """Helper function to merge two parts into one."""
         for phrase in part2.getPhraseList():
            part1.addPhrase(phrase)

      def mergeScores(score1, score2):
         """Helper function to merge two scores into one."""
         for part in score2.getPartList():
            score1.addPart(part)

      # check type of material and call the appropriate function
      if type(material1) == Score and type(material2) == Score:
         mergeScores(material1, material2)
      elif type(material1) == Part and type(material2) == Part:
         mergeParts(material1, material2)
      elif (type(material1) == Part and type(material2) == Score) or \
           (type(material1) == Score and type(material2) == Part):
         raise TypeError( "Cannot merge Score and Part - arguments must be of the same type (both Score or both Part)." )
      else:
         raise TypeError( "Arguments must be both either Score or Part." )


   def retrograde(material):
      """It reverses the start times of notes in 'material'.
         'Material' can be Phrase, Part, or Score.
      """

      # define helper functions
      def getPartStartTime(part):
         """Helper function to return the start time of a part."""

         minStartTime = 10000000000.0   # holds the earliest start time among all phrases (initialize to a very large value)
         for phrase in part.getPhraseList():
            minStartTime = min(minStartTime, phrase.getStartTime())   # accumulate the earliest start time, so far
         # now, minStartTime holds the earliest start time of a phrase in this part

         return minStartTime   # so return it

      def getPartEndTime(part):
         """Helper function to return the end time of a part."""

         maxEndTime   = 0.0             # holds the latest end time among all phrases
         for phrase in part.getPhraseList():
            maxEndTime   = max(maxEndTime, phrase.getEndTime())       # accumulate the latest end time, so far
         # now, maxEndTime hold the latest end time of a phrase in this part

         return maxEndTime   # so return it

      def retrogradePart(part):
         """Helper function to retrograde a single part."""

         startTime = getPartStartTime(part)  # the earliest start time among all phrases
         endTime   = getPartEndTime(part)    # the latest end time among all phrases

         # retrograde each phrase and adjust its start time accordingly
         for phrase in part.getPhraseList():
            distanceFromEnd = endTime - phrase.getEndTime()  # get this phrase's distance from end

            jMod.retrograde(phrase)                          # retrograde it

            # the retrograded phrase needs to start as far from the beginning of the part as its orignal end used to be
            # from the end of the part
            phrase.setStartTime( distanceFromEnd + startTime )

         # now, all phrases in this part have been retrograded and their start times have been aranged
         # to mirror their original end times

      def retrogradeScore(score):
         """Helper function to retrograde a score."""

         # calculate the score's start and end times
         startTime = 10000000000.0   # holds the earliest start time among all parts (initialize to a very large value)
         endTime   = 0.0             # holds the latest end time among all parts
         for part in score.getPartList():
            startTime = min(startTime, getPartStartTime(part))   # accumulate the earliest start time, so far
            endTime   = max(endTime, getPartEndTime(part))       # accumulate the latest end time, so far
         # now, startTime and endTime hold the score's start and end time, respectively

         print "score startTime =", startTime, "endTime =", endTime

         # retrograde each part and adjust its start time accordingly
         for part in score.getPartList():
            # get this part's distance from the score end
            distanceFromEnd = endTime - (getPartEndTime(part) + getPartStartTime(part))

            # retrograde this part
            retrogradePart(part)

            # the retrograded part needs to start as far as
            # the orignal part's distance from the score end
            Mod.shift(part, distanceFromEnd)
         # now, all parts have been retrograded and their start times have been aranged to mirror their original
         # end times


      # check type of material and call the appropriate function
      if type(material) == Score:
         retrogradeScore(material)
      elif type(material) == Part:
         retrogradePart(material)
      elif type(material) == Phrase or type(material) == jPhrase:
         jMod.retrograde(material)
      else:   # error check
         raise TypeError( "Unrecognized material type " + str(type(material)) + " - expected Phrase, Part, or Score." )


   # make these function callable without having to instantiate this class
   normalize = Callable(normalize)
   invert = Callable(invert)
   mutate = Callable(mutate)
   elongate = Callable(elongate)
   shift = Callable(shift)
   merge = Callable(merge)
   retrograde = Callable(retrograde)


######################################################################################
# JEM working directory fix
#
# JEM (written partially in Java) does not allow changing current directory.
# So, when we have the user's desired working directory we CANNOT use it to read/write
# jMusic media files, unless we add it as a prefix here to every Read/Write operation.
# We do so only if the filepath passed to Read/Write is just a filename (as opposed
# to a path).
#
# Let's define some useful stuff here, for this fix

import os.path

def fixWorkingDirForJEM( filename ):
   """It prefixes the provided filename with JEM's working directory, if available,
      only if filename is NOT an absolute path (in which case the user truly knows
      where they want to store it).
   """

   try:

      JEM_getMainFilePath   # check if function JEM_getMainFilePath() is defined (this happens only inside JEM)

      # get working dir, if JEM is available
      workDir = JEM_getMainFilePath()

      # two cases for filename:
      #
      # 1. a relative filepath (e.g., just a filename, or "../filename")
      # 2. an absolute filepath

      if os.path.isabs( filename ):          # if an absolute path, the user knows what they are doing
         return filename                     # ...so, do nothing
      else:                                  # else (if a relative pathname),
         return workDir + filename           # ...fix it

   except:
      # if JEM is not available, do nothing (e.g., music.py is being run outside of JEM)
      return filename


######################################################################################
#### jMusic Read extensions ##########################################################
######################################################################################

from jm.util import Read as jRead  # needed to wrap more functionality below
from image import *                # import Image class and related Java libraries

# Create Read.image("test.jpg") to return an image, in addition to Read's default functionality.
# This class is not meant to be instantiated, hence no "self" in function definitions.
# Functions are made callable through class Callable, above.
class Read(jRead):

   def midi(score, filename):
      """Import a standard MIDI file to a jMusic score."""

      # JEM working directory fix (see above)
      filename = fixWorkingDirForJEM( filename )   # does nothing if not in JEM

      # use fixed filename with jMusic's Read.midi()
      jRead.midi(score, filename)

   # make this function callable without having to instantiate this class
   midi = Callable(midi)

######################################################################################
#### jMusic Write extensions #########################################################
######################################################################################

from jm.util import Write as jWrite  # needed to wrap more functionality below

# Create Write.image(image, "test.jpg") to write an image to file, in addition
# to Write's default functionality.
# This class is not meant to be instantiated, hence no "self" in function definitions.
# Functions are made callable through class Callable, above.

class Write(jWrite):

   def midi(score, filename):
      """Save a standard MIDI file from a jMusic score."""

      # JEM working directory fix (see above)
      filename = fixWorkingDirForJEM( filename )   # does nothing if not in JEM

      #***
      #print "fixWorkingDirForJEM( filename ) =", filename

      # use fixed filename with jMusic's Write.midi()
      jWrite.midi(score, filename)

   # make this function callable without having to instantiate this class
   midi = Callable(midi)

######################################################################################
#### jMusic Note extensions ########################################################
######################################################################################

###############################################################################
# freqToNote   Convert frequency to MIDI note number
#        freqToNote(f) converts frequency to the closest MIDI note
#        number with pitch bend value for finer control.  A4 corresponds to
#        the note number 69 (concert pitch is set to 440Hz by default).
#        The default pitch bend range is 2 half tones above and below.
#
#        2005-10-13 by MARUI Atsushi
#        See http://www.geidai.ac.jp/~marui/octave/node3.html
#
# For example, "sliding" from A4 (MIDI pitch 69, frequency 440 Hz)
#              to a bit over AS4 (MIDI pitch 70, frequency 466.1637615181 Hz).
#
#>>>for f in range(440, 468):
#...    print freqToNote(f)
#...
#(69, 0)
#(69, 322)
#(69, 643)
#(69, 964)
#(69, 1283)
#(69, 1603)
#(69, 1921)
#(69, 2239)
#(69, 2555)
#(69, 2872)
#(69, 3187)
#(69, 3502)
#(69, 3816)
#(70, -4062)
#(70, -3750)
#(70, -3438)
#(70, -3126)
#(70, -2816)
#(70, -2506)
#(70, -2196)
#(70, -1888)
#(70, -1580)
#(70, -1272)
#(70, -966)
#(70, -660)
#(70, -354)
#(70, -50)
#(70, 254)
#
# The above overshoots AS4 (MIDI pitch 70, frequency 466.1637615181 Hz).
# So, here is converting the exact frequency:
#
#>>> freqToNote(466.1637615181)
#(70, 0)
###############################################################################

def freqToNote(frequency):
   """Converts frequency to the closest MIDI note number with pitch bend value
      for finer control.  A4 corresponds to the note number 69 (concert pitch
      is set to 440Hz by default).  The default pitch bend range is 4 half tones.
   """

   from math import log

   concertPitch = 440.0   # 440Hz
   bendRange = 4          # 4 half tones (2 below, 2 above)

   x = log(frequency / concertPitch, 2) * 12 + 69
   note = round(x)
   pitchBend = round((x - note) * 8192 / bendRange * 2)

   return int(note), int(pitchBend)


def noteToFreq(note):
   """Converts a MIDI note to the corresponding frequency.  A4 corresponds to the note number 69 (concert pitch
      is set to 440Hz by default).
   """

   concertPitch = 440.0   # 440Hz

   frequency = concertPitch * 2 ** ( (note - 69) / 12.0 )

   return frequency



from jm.music.data import *
from jm.music.data import Note as jNote  # needed to wrap more functionality below

# update Note to accept length which specifies the actual length (performance) of the note,
# (whereas duration specifies the score (or denoted) length of the note).
class Note(jNote):

   def __str__(self):
      # we disrupted access to jMusic's (Java's) Note.toString() method,
      # so, let's fix it
      return self.toString()

   def __repr__(self):
      # we disrupted access to jMusic's (Java's) Note.toString() method,
      # so, let's fix it
      return self.toString()

   def __init__(self, value, duration, dynamic=85, pan=0.5, length=None):

      # NOTE: If value is an int, it signifies pitch; otherwise, if it is a float,
      # it signifies a frequency.

      # set note length (if needed)
      if length == None:   # not provided?
         length = duration * jNote.DEFAULT_LENGTH_MULTIPLIER  # normally, duration * 0.9

      # do some basic error checking
      if type(value) == int and value != REST and (value < 0 or value > 127):
        raise TypeError( "Note pitch should be an integer between 0 and 127 (it was " + str(value) + ")." )
      elif type(value) == float and not value > 0.0:
        raise TypeError( "Note frequency should be a float greater than 0.0 (it was " + str(value) + ")." )
      elif (type(value) != int) and (type(value) != float):
        raise TypeError( "Note first parameter should be a pitch (int) or a frequency (float) - it was " + str(type(value)) + "." )

      # now, construct a jMusic Note with the proper attributes
      jNote.__init__(self, value, duration, dynamic, pan)     # construct note
      self.setLength( length )                                # and set its length

      # NOTE: jMusic Notes if int pitch is given, they populate both frequency and pitch;
      # (if float pitch is given, they treat if as frequency and populate only frequency - no pitch).
      # This is a bug.  Below, we fix it by also using setPitch() or setFrequency(), which may appear
      # redundant, but they fix this problem (as they do the proper cross-updating of pitch and frequency).

      # fix jMusic Note bug (see above)
      if type(value) == int:
      	 self.setPitch(value)
      elif type(value) == float:
      	 self.setFrequency(value)


   # fix set duration to also adjust length proportionally
   def setDuration(self, duration):

      # calculate length fector from original values
      lengthFactor = self.getLength() / self.getDuration()

      # and set new duration and length appropriately
      jNote.setDuration(self, duration )
      self.setLength(duration * lengthFactor )

   # fix error message returned from getPitch() if frequency and pitch are not equivalent
   def getPitch(self):

      # get frequency
      frequency = self.getFrequency()

      # convert to corresponding pitch
      if frequency == float(REST):    # is it a rest?
         pitch = REST                    # yes, so update accordingly
      else:   # it's a regular note, so...
         # calculate corresponding pitch and pith bend
         pitch, bend = freqToNote(frequency)

      # return only pitch
      return pitch

   # also, create a way to get the difference between frequency and pitch, in pitch bend units (see Play class)
   def getPitchBend(self):

      # get frequency
      frequency = self.getFrequency()

      # and calculate corresponding pitch and pith bend
      pitch, bend = freqToNote(frequency)

      # return only pitch bend (from 0 to )
      return bend + PITCHBEND_NORMAL


######################################################################################
#### jMusic Phrase extensions ########################################################
######################################################################################

from jm.music.data import Phrase as jPhrase  # needed to wrap more functionality below

# update Phrase's addNoteList to handle chords, i.e., lists of pitches,
# in addition to single pitches (the default functionality).
class Phrase(jPhrase):

   def __str__(self):
      # we disrupted access to jMusic's (Java's) Phrase.toString() method,
      # so, let's fix it
      return self.toString()

   def __repr__(self):
      # we disrupted access to jMusic's (Java's) Phrase.toString() method,
      # so, let's fix it
      return self.toString()

   def addChord(self, pitches, duration, dynamic=85, panoramic=0.5, length=None):
      # set chord length (if needed)
      if length == None:   # not provided?
         length = duration * jNote.DEFAULT_LENGTH_MULTIPLIER  # normally, duration * 0.9

      # add all notes, minus the last one, as having no duration, yet normal length
      # (exploiting how Play.midi() and Write.midi() work)
      for i in range( len(pitches)-1 ):
         n = Note(pitches[i], 0.0, dynamic, panoramic, length)
         self.addNote(n)

      # now, add the last note with the proper duration (and length)
      n = Note(pitches[-1], duration, dynamic, panoramic, length)
      self.addNote(n)

   def addNoteList(self, pitches, durations, dynamics=[], panoramics=[], lengths=[]):
      """Add notes to the phrase using provided lists of pitches, durations, etc. """

      # check if provided lists have equal lengths
      if len(pitches) != len(durations) or \
         (len(dynamics) != 0) and (len(pitches) != len(dynamics)) or \
         (len(panoramics) != 0) and (len(pitches) != len(panoramics)) or \
         (len(lengths) != 0) and (len(pitches) != len(lengths)):
         raise ValueError("The provided lists should have the same length.")

      # if dynamics was not provided, construct it with max value
      if dynamics == []:
         dynamics = [85] * len(pitches)

      # if panoramics was not provided, construct it at CENTER
      if panoramics == []:
         panoramics = [0.5] * len(pitches)

      # if note lengths was not provided, construct it at 90% of note duration
      if lengths == []:
         lengths = [duration * jNote.DEFAULT_LENGTH_MULTIPLIER for duration in durations]

      # traverse the pitch list and handle every item appropriately
      for i in range( len(pitches) ):
         if type(pitches[i]) == list:              # is it a chord?
            self.addChord(pitches[i], durations[i], dynamics[i], panoramics[i], lengths[i])  # yes, so add it
         else:                                     # else, it's a note
            n = Note(pitches[i], durations[i], dynamics[i], panoramics[i], lengths[i])       # create note
            self.addNote(n)                                                                  # and add it

# Do NOT make these functions callable - Phrase class is meant to be instantiated,
# i.e., we will always call these from a Phrase object - not the class, e.g., as in Mod.

######################################################################################
#### jMusic Play extensions ##########################################################
######################################################################################

from jm.util import Play as jPlay  # needed to wrap more functionality below

# Create Play.noteOn(pitch, velocity, channel) to start a MIDI note sounding,
#        Play.noteOff(pitch, channel) to stop the corresponding note from sounding, and
#        Play.setInstrument(instrument, channel) to change instrument for this channel.
#
# This adds to existing Play functionality.
# This class is not meant to be instantiated, hence no "self" in function definitions.
# Functions are made callable through class Callable, above.

from javax.sound.midi import *

# NOTE: Opening the Java synthesizer below generates some low-level noise in the audio output.
# But we need it to be open, in case the end-user wishes to use functions like Play.noteOn(), below.
# ( *** Is there a way to open it just-in-time, and/or close it when not used? I cannot think of one.)

Java_synthesizer = MidiSystem.getSynthesizer()  # get a Java synthesizer
Java_synthesizer.open()                         # and activate it (should we worry about close()???)

# make all instruments available
Java_synthesizer.loadAllInstruments(Java_synthesizer.getDefaultSoundbank())


# The MIDI specification stipulates that pitch bend be a 14-bit value, where zero is
# maximum downward bend, 16383 is maximum upward bend, and 8192 is the center (no pitch bend).
PITCHBEND_MIN = 0
PITCHBEND_MAX = 16383
PITCHBEND_NORMAL = 8192

# calculate constants from the way we handle pitch bend
OUR_PITCHBEND_MAX    = PITCHBEND_MAX - PITCHBEND_NORMAL
OUR_PITCHBEND_MIN    = -PITCHBEND_NORMAL
OUR_PITCHBEND_NORMAL = 0

# initialize pitchbend across channels to 0
CURRENT_PITCHBEND = {}    # holds pitchbend to be used when playing a note / frequency (see below)
for i in range(16):
   CURRENT_PITCHBEND[i] = 0   # set this channel's pitchbend to zero


#########
# NOTE:  The following code addresses Play.midi() functionality.  In order to be able to stop music
# that is currently playing, we wrap the jMusic Play class inside a Python Play class and rebuild
# play music functionality from basic elements.

from jm.midi import MidiSynth  # needed to play and loop MIDI
from time import sleep         # needed to implement efficient busy-wait loops (see below)
from timer import *            # needed to schedule future tasks

# allocate enough MidiSynths and reuse them (when available)
__midiSynths__ = []            # holds all available jMusic MidiSynths
MAX_MIDI_SYNTHS = 12           # max number of concurrent MidiSynths allowed
                               # NOTE: This is an empirical value - not documented - may change.

def __getMidiSynth__():
   """Returns the next available MidiSynth (if any), or None."""

   # make sure all possible MidiSynths are allocated
   if __midiSynths__ == []:
      for i in range(MAX_MIDI_SYNTHS):
         __midiSynths__.append( MidiSynth() )   # create a new MIDI synthesizer
   # now, all MidiSynths are allocated

   # find an available MidiSynth to play the material (it's possible that all are allocated,
   # since this function may be called repeatedly, while other music is still sounding
   i = 0
   while i < MAX_MIDI_SYNTHS and __midiSynths__[i].isPlaying():
      i = i + 1     # check if the next MidiSynth is available
   # now, i either points to the next available MidiSynth, or MAX_MIDI_SYNTHS if none is available

   # did we find an available MidiSynth?
   if i < MAX_MIDI_SYNTHS:
      midiSynth = __midiSynths__[i]
   else:
      midiSynth = None

   return midiSynth    # let them have it (hopefully, they will use it right away)

# Provide a way to stop all MidiSynths from playing.
def __stopMidiSynths__():
   """Stops all MidiSynths from playing."""
   for midiSynth in __midiSynths__:
      if midiSynth.isPlaying():    # if playing, stop it
         midiSynth.stop()


#########
# An envelope contains a list of attack times (in milliseconds, relative from the previous time) and values (to reach at those times),
# how long to wait (delay time, in milliseconds, relative from the previous time) to get to a sustain value, and
# then how long to wait to reach a value of zero (in milliseconds, relative from the end time).

class Envelope():
    def __init__(self, attackTimes = [2], attackValues = [1.0], delayTime = 1, sustainValue = 1.0, releaseTime = 2):

        # make sure attack times and values are parallel
        if len(attackValues) != len(attackTimes):

            raise IndexError("Envelope: attack times and values need to have the same length")

        else:  # all seems well

            self.attackTimes = attackTimes    # in milliseconds, relative from the previous time...
            self.attackValues = attackValues  # and the corresponding values
            self.delayTime = delayTime        # in milliseconds, relative from the previous time...
            self.sustainValue = sustainValue  # to reach this value
            self.releaseTime = releaseTime    # in milliseconds, relative from the end time

    # get list of attack times
    def getAttackTimes(self):
        return self.attackTimes

    # get list of attack values
    def getAttackValues(self):
        return self.attackValues

    # get list of lists - first element is list of attack times and second element is list attack values
    def getAttackTimesAndValues(self):
        return [self.attackTimes, self.attackValues]

    # update attack times
    def setAttackTimes(self, attackTimes):
        # make sure attack times and values are parallel
        if len(self.attackValues) != len(attackTimes):

            raise IndexError("Envelope.setAttackTimes(): attack times and values need to have the same length")

        else:  # all seems well
            self.attackTimes = attackTimes

    #
    def setAttackValues(self, attackValues):
        # make sure attack times and values are parallel
        if len(attackValues) != len(self.attackTimes):

            raise IndexError("Envelope.setAttackValues(): attack times and values need to have the same length")

        else:  # all seems well
            self.attackValues = attackValues

    def setAttackTimesAndValues(self, attackTimes, attackValues):
        # make sure attack times and values are parallel
        if len(self.attackValues) != len(attackTimes):

            raise IndexError("Envelope.setAttackTimesAndValues(): attack times and values need to have the same length")

        else:  # all seems well
            self.attackTimes = attackTimes
            self.attackValues = attackValues

    def getSustain(self):
        return self.sustainValue

    def setSustain(self, sustainValue):
        self.sustainValue = sustainValue

    def getDelay(self):
        return self.delayTime

    def setDelay(self, delayTime):
        self.delayTime = delayTime

    def getRelease(self):
        return self.releaseTime

    #update release
    def setRelease(self, releaseTime):
        self.releaseTime = releaseTime

    # get length of envelope
    def getLength(self):
        return self.__getAbsoluteDelay__() + self.releaseTime

    # get list of absolute attack times, attack time distance from start of envelope
    def __getAbsoluteAttackTimes__(self):
        # now convert relative attack times to absolute from the start time
        absoluteAttackTimes = [ self.attackTimes[0] ]   # initialize first list element
        for i in range(1, len(self.attackTimes)):            # process remaining times
            absoluteAttackTimes.append(self.attackTimes[i] + absoluteAttackTimes[i-1])
        return absoluteAttackTimes

    def __getAbsoluteDelay__(self):
        # same for delay
        absoluteAttackTimes = self.__getAbsoluteAttackTimes__()
        absoluteDelayTime =  absoluteAttackTimes[len(absoluteAttackTimes) - 1] + self.delayTime
        return absoluteDelayTime



# Holds notes currently sounding, in order to prevent premature NOTE-OFF for overlapping notes on the same channel
# For every frequencyOn() we add the tuple (pitch, channel), and for every frequencyOff() we rmove the tuple.
# If it is the last one, we execute a NOTE-OFF (otherwise, we don't).
notesCurrentlyPlaying = []

class Play(jPlay):

   # redefine Play.midi to fix jMusic bug (see above) - now, we can play as many times as we wish.
   def midi(material):
      """Play jMusic material (Score, Part, Phrase, Note) using our own Play.note() function."""

      # do necessary datatype wrapping (MidiSynth() expects a Score)
      if type(material) == Note:
         material = Phrase(material)
      if type(material) == jNote:    # (also wrap jMusic default Notes, in addition to our own)
         material = Phrase(material)
      if type(material) == Phrase:   # no elif - we need to successively wrap from Note to Score
         material = Part(material)
         material.setInstrument(-1)     # indicate no default instrument (needed to access global instrument)
      if type(material) == jPhrase:  # (also wrap jMusic default Phrases, in addition to our own)
         material = Part(material)
         material.setInstrument(-1)     # indicate no default instrument (needed to access global instrument)
      if type(material) == Part:     # no elif - we need to successively wrap from Note to Score
         material = Score(material)
      if type(material) == Score:

         # we are good - let's play it then!

         score = material   # by now, material is a score, so create an alias (for readability)


         # loop through all parts and phrases to get all notes
         noteList = []               # holds all notes
         tempo = score.getTempo()    # get global tempo (can be overidden by part and phrase tempos)
         for part in score.getPartArray():   # traverse all parts
            channel = part.getChannel()        # get part channel
            instrument = Play.getInstrument(channel)  # get global instrument for this channel
            if part.getInstrument() > -1:      # has the part instrument been set?
               instrument = part.getInstrument()  # yes, so it takes precedence
            if part.getTempo() > -1:           # has the part tempo been set?
               tempo = part.getTempo()            # yes, so update tempo
            for phrase in part.getPhraseArray():   # traverse all phrases in part
               if phrase.getInstrument() > -1:        # is this phrase's instrument set?
                  instrument = phrase.getInstrument()    # yes, so it takes precedence
               if phrase.getTempo() > -1:          # has the phrase tempo been set?
                  tempo = phrase.getTempo()           # yes, so update tempo

               # time factor to convert time from jMusic Score units to milliseconds
               # (this needs to happen here every time, as we may be using the tempo from score, part, or phrase)
               FACTOR = 1000 * 60.0 / tempo

               # process notes in this phrase
               startTime = phrase.getStartTime() * FACTOR   # in milliseconds
               for note in phrase.getNoteArray():
                  frequency = note.getFrequency()
                  panning = note.getPan()
                  panning = mapValue(panning, 0.0, 1.0, 0, 127)    # map from range 0.0..1.0 (Note panning) to range 0..127 (as expected by Java synthesizer)
                  start = int(startTime)                           # remember this note's start time (in milliseconds)

                  # NOTE:  Below we use note length as opposed to duration (getLength() vs. getDuration())
                  # since note length gives us a more natural sounding note (with proper decay), whereas
                  # note duration captures the more formal (printed score) duration (which sounds unnatural).
                  duration = int(note.getLength() * FACTOR)             # get note length (as oppposed to duration!) and convert to milliseconds
                  startTime = startTime + note.getDuration() * FACTOR   # update start time (in milliseconds)
                  velocity = note.getDynamic()

                  # accumulate non-REST notes
                  if (frequency != REST):
                     noteList.append((start, duration, frequency, velocity, channel, instrument, panning))   # put start time first and duration second, so we can sort easily by start time (below),
                     # and so that notes that are members of a chord as denoted by having a duration of 0 come before the note that gives the specified chord duration

         # sort notes by start time
         noteList.sort()

         # Schedule playing all notes in noteList
         chordNotes = []      # used to process notes belonging in a chord
         for start, duration, pitch, velocity, channel, instrument, panning in noteList:
            # set appropriate instrument for this channel
            Play.setInstrument(instrument, channel)

            # handle chord (if any)
            # Chords are denoted by a sequence of notes having the same start time and 0 duration (except the last note
            # of the chord).
            if duration == 0:   # does this note belong in a chord?
               chordNotes.append([start, duration, pitch, velocity, channel, panning])  # add it to the list of chord notes

            elif chordNotes == []:   # is this a regular, solo note (not part of a chord)?

               # yes, so schedule it to play via a Play.note event
               Play.note(pitch, start, duration, velocity, channel, panning)
               #print "Play.note(" + str(pitch) + ", " + str(int(start * FACTOR)) + ", " + str(int(duration * FACTOR)) + ", " + str(velocity) + ", " + str(channel) + ")"

            else:   # note has a normal duration and it is part of a chord

               # first, add this note together with this other chord notes
               chordNotes.append([start, duration, pitch, velocity, channel, panning])

               # now, schedule all notes in the chord list using last note's duration
               for start, ignoreThisDuration, pitch, velocity, channel, panning in chordNotes:
                  # schedule this note using chord's duration (provided by the last note in the chord)
                  Play.note(pitch, start, duration, velocity, channel, panning)
                  #print "Chord: Play.note(" + str(pitch) + ", " + str(int(start * FACTOR)) + ", " + str(int(duration * FACTOR)) + ", " + str(velocity) + ", " + str(channel) + ")"
               # now, all chord notes have been scheduled

               # so, clear chord notes to continue handling new notes (if any)
               chordNotes = []

         # now, all notes have been scheduled for future playing - scheduled notes can always be stopped using
         # JEM's stop button - this will stop all running timers (used by Play.note() to schedule playing of notes)
         #print "Play.note(" + str(pitch) + ", " + str(int(start * FACTOR)) + ", " + str(int(duration * FACTOR)) + ", " + str(velocity) + ", " + str(channel) + ")"

      else:   # error check
         print "Play.midi(): Unrecognized type " + str(type(material)) + ", expected Note, Phrase, Part, or Score."


   # old way - should be removed in future release (together will *all* references of __midiSynths__'s)
   def midi2(material):
      """This is the original Play.midi() - retained for backup and testing purposes.
         Play jMusic material (Score, Part, Phrase, Note) using next available MidiSynth (if any)."""

      from jm.music.data import Phrase as jPhrase   # since we extend Phrase later

      midiSynth = __getMidiSynth__()  # get next available MidiSynth (or None if all busy)
      #midiSynth = MidiSynth()    # create a new MIDI synthesizer

      # did we find an available midiSynth?
      if midiSynth:
         # play the music
         # do necessary datatype wrapping (MidiSynth() expects a Score)
         if type(material) == Note:
            material = Phrase(material)
         if type(material) == jNote:    # (also wrap jMusic default Notes, in addition to our own)
            material = Phrase(material)
         if type(material) == Phrase:   # no elif - we need to successively wrap from Note to Score
            material = Part(material)
         if type(material) == jPhrase:  # (also wrap jMusic default Phrases, in addition to our own)
            material = Part(material)
         if type(material) == Part:     # no elif - we need to successively wrap from Note to Score
            material = Score(material)
         if type(material) == Score:

            midiSynth.play( material )   # play it!

         else:   # error check
            print "Play.midi(): Unrecognized type" + str(type(material)) + ", expected Note, Phrase, Part, or Score."

      else:   # error check
         print "Play.midi(): All", MAX_MIDI_SYNTHS, "MIDI synthesizers are busy - (try again later?)"

      return midiSynth  # return midiSynth playing


   # NOTE:  Here we connect noteOn() and frequencyOn() with noteOnPitchBend() to allow for
   # playing microtonal music.  Although this may seem as cyclical (i.e., that in noteOn() we
   # convert pitch to frequency, and then call frequencyOn() which convert the frequency back to pitch,
   # so that it can call noteOnPitchBend() ), this is the only way we can make everything work.
   # We are constrained by the fact that jMusic Note objects are limited in how they handle pitch and
   # frequency (i.e., that creating a Note with pitch will set the Note's corresponding frequency,
   # but not the other way around), and the fact that we can call Note.getFrequency() above in Play.midi()
   # without problem, but NOT Note.getPitch(), which will crash if the Note was instantiated with a frequency
   # (i.e., pitch is not available / set).
   # Therefore, we need to make the run about here, so that we keep everything else easier to code / maintain,
   # and also keep the API (creating and play notes) simpler.  So, do NOT try to simplify the following code,
   # as it is the only way (I think) that can make everything else work simply - also see Play.midi().
   def noteOn(pitch, velocity=100, channel=0, panning = -1):
      """Send a NOTE_ON message for this pitch to the Java synthesizer object.  Default panning of -1 means to
         use the default (global) panning setting of the Java synthesizer."""

      if (type(pitch) == int) and (0 <= pitch <= 127):   # a MIDI pitch?
         # yes, so convert pitch from MIDI number (int) to Hertz (float)
         pitch = noteToFreq(pitch)

      if type(pitch) == float:        # a pitch in Hertz?
         Play.frequencyOn(pitch, velocity, channel, panning)  # start it

      else:

         print "Play.noteOn(): Unrecognized pitch " + str(pitch) + ", expected MIDI pitch from 0 to 127 (int), or frequency in Hz from 8.17 to 12600.0 (float)."


   def frequencyOn(frequency, velocity=100, channel=0, panning = -1):
      """Send a NOTE_ON message for this frequency (in Hz) to the Java synthesizer object.  Default panning of -1 means to
         use the default (global) panning setting of the Java synthesizer."""

      if (type(frequency) == float) and (8.17 <= frequency <= 12600.0): # a pitch in Hertz (within MIDI pitch range 0 to 127)?

         pitch, bend = freqToNote( frequency )                     # convert to MIDI note and pitch bend

         # also, keep track of how many overlapping instances of this pitch are currently sounding on this channel
         # so that we turn off only the last one - also see frequencyOff()
         noteID = (pitch, channel)              # create an ID using pitch-channel pair
         notesCurrentlyPlaying.append(noteID)   # add this note instance to list

         Play.noteOnPitchBend(pitch, bend, velocity, channel, panning)      # and start it

      else:

         print "Play.frequencyOn(): Invalid frequency " + str(frequency) + ", expected frequency in Hz from 8.17 to 12600.0 (float)."

   def noteOff(pitch, channel=0):
      """Send a NOTE_OFF message for this pitch to the Java synthesizer object."""

      if (type(pitch) == int) and (0 <= pitch <= 127):   # a MIDI pitch?
         # yes, so convert pitch from MIDI number (int) to Hertz (float)
         pitch = noteToFreq(pitch)

      if type(pitch) == float:        # a pitch in Hertz?
         Play.frequencyOff(pitch, channel)  # stop it

      else:

         print "Play.noteOff(): Unrecognized pitch " + str(pitch) + ", expected MIDI pitch from 0 to 127 (int), or frequency in Hz from 8.17 to 12600.0 (float)."

   def frequencyOff(frequency, channel=0):
      """Send a NOTE_OFF message for this frequency (in Hz) to the Java synthesizer object."""

      global Java_synthesizer

      if (type(frequency) == float) and (8.17 <= frequency <= 12600.0): # a frequency in Hertz (within MIDI pitch range 0 to 127)?

         pitch, bend = freqToNote( frequency )                     # convert to MIDI note and pitch bend

         # also, keep track of how many overlapping instances of this frequency are currently playing on this channel
         # so that we turn off only the last one - also see frequencyOn()
         noteID = (pitch, channel)                   # create an ID using pitch-channel pair

         # next, remove this noteID from the list, so that we may check for remaining instances
         notesCurrentlyPlaying.remove(noteID)        # remove noteID
         if noteID not in notesCurrentlyPlaying:     # is this last instance of note?

            # yes, so turn it off!
            channelHandle = Java_synthesizer.getChannels()[channel]   # get a handle to channel
            channelHandle.noteOff(pitch)                              # and turn it off

      else:     # frequency was outside expected range

         print "Play.frequencyOff(): Invalid frequency " + str(frequency) + ", expected frequency in Hz from 8.17 to 12600.0 (float)."

      # NOTE: Just to be good citizens, also turn pitch bend to normal (i.e., no bend).
      # Play.setPitchBend(0, channel)

# Commented out below, because it might give the impression that different pitch bends
# signify different notes to be turned off - not so.  NOTE_OFF messages are based solely on pitch.
#
#   def noteOffPitchBend(pitch, bend = 0, channel=0):
#      """Send a NOTE_OFF message for this pitch to the Java synthesizer object."""
#      # NOTE_OFF messages are based on pitch (i.e., pitch bend is irrelevant / ignored)
#      Play.noteOff(pitch, channel)

   def note(pitch, start, duration, velocity=100, channel=0, panning = -1):
      """Plays a note with given 'start' time (in milliseconds from now), 'duration' (in milliseconds
         from 'start' time), with given 'velocity' on 'channel'.  Default panning of -1 means to
         use the default (global) panning setting of the Java synthesizer. """

      # TODO: We should probably test for negative start times and durations.

      # create a timer for the note-on event
      noteOn = Timer2(start, Play.noteOn, [pitch, velocity, channel, panning], False)

      # create a timer for the note-off event
      noteOff = Timer2(start+duration, Play.noteOff, [pitch, channel], False)

      # and activate timers (set things in motion)
      noteOn.start()
      noteOff.start()

      # NOTE:  Upon completion of this function, the two Timer objects become unreferenced.
      #        When the timers elapse, then the two objects (in theory) should be garbage-collectable,
      #        and should be eventually cleaned up.  So, here, no effort is made in reusing timer objects, etc.

   def frequency(frequency, start, duration, velocity=100, channel=0, panning = -1):
      """Plays a frequency with given 'start' time (in milliseconds from now), 'duration' (in milliseconds
         from 'start' time), with given 'velocity' on 'channel'.  Default panning of -1 means to
         use the default (global) panning setting of the Java synthesizer."""

      # NOTE:  We assume that the end-user will ensure that concurrent microtones end up on
      # different channels.  This is needed since MIDI has only one pitch band per channel,
      # and most microtones require their unique pitch bending.

      # TODO: We should probably test for negative start times and durations.

      # create a timer for the frequency-on event
      frequencyOn = Timer2(start, Play.frequencyOn, [frequency, velocity, channel, panning], False)

      # create a timer for the frequency-off event
      frequencyOff = Timer2(start+duration, Play.frequencyOff, [frequency, channel], False)

      # call pitchBendNormal to turn off the timer, if it is on
      #setPitchBendNormal(channel)
      # and activate timers (set things in motion)
      frequencyOn.start()
      frequencyOff.start()

      #setPitchBendNormal(channel, start+duration, True)


# (Repeated here for convenience...)
# The MIDI specification stipulates that pitch bend be a 14-bit value, where zero is
# maximum downward bend, 16383 is maximum upward bend, and 8192 is the center (no pitch bend).
#PITCHBEND_MIN = 0
#PITCHBEND_MAX = 16383
#PITCHBEND_NORMAL = 8192

# calculate constants from the way we handle pitch bend
#OUR_PITCHBEND_MAX    = PITCHBEND_MAX - PITCHBEND_NORMAL
#OUR_PITCHBEND_MIN    = -PITCHBEND_NORMAL
#OUR_PITCHBEND_NORMAL = 0


   # No (normal) pitch bend in JythonMusic (as opposed to MIDI) is 0, max downward bend is -8192, and max upward bend is 8191.
   # (Result is undefined if you exceed these values - it may wrap around or it may cap.)
   def setPitchBend(bend = 0, channel=0):
      """Set global pitchbend variable to be used when a note / frequency is played."""

      if (bend <= OUR_PITCHBEND_MAX) and (bend >= OUR_PITCHBEND_MIN):   # is pitchbend within appropriate range?

         CURRENT_PITCHBEND[channel] = bend        # remember the pitch bend (e.g., for Play.noteOn() )

         # and set the pitchbend on the Java synthesizer (this is the only place this is done!)
         MIDI_pitchbend = bend + PITCHBEND_NORMAL                  # convert to MIDI pitchbend to set
         channelHandle = Java_synthesizer.getChannels()[channel]   # get a handle to channel
         channelHandle.setPitchBend( MIDI_pitchbend )              # and set it (send message)!

      else:     # frequency was outside expected range

         print "Play.setPitchBend(): Invalid pitchbend " + str(bend) + ", expected pitchbend in range " + \
               str(OUR_PITCHBEND_MIN) + " to " + str(OUR_PITCHBEND_MAX) + "."


   def getPitchBend(channel=0):
      """returns the current pitchbend for this channel."""

      return CURRENT_PITCHBEND[channel]


   # No (normal) pitch bend is 0, max downward bend is -8192, and max upward bend is 8191.
   # (Result is undefined if you exceed these values - it may wrap around or it may cap.)

   def noteOnPitchBend(pitch, bend = 0, velocity=100, channel=0, panning = -1):
      """Send a NOTE_ON message for this pitch and pitch bend to the Java synthesizer object.
         Default panning of -1 means to use the default (global) panning setting of the Java synthesizer."""

      global Java_synthesizer

      #Play.setPitchBend(bend, channel)  # remember current pitchbend for this channel


      # NOTE: Our normal (or no) pitch bend is 0, max downward bend is -8192, and max upward bend is 8191.
      # However, internally, the MIDI specification wants normal pitch bend to be 8192, max downward
      # bend to be 0, and max upward bend to be 16383).
      # So, convert it and add the current global pitchbend, as set previously.
      MIDI_pitchbend = bend + PITCHBEND_NORMAL + CURRENT_PITCHBEND[channel]

      # Since it is possible that, together with the global pitchbend, we may be out of range,
      # let's check to make sure.
      if (MIDI_pitchbend <= PITCHBEND_MAX) and (MIDI_pitchbend >= PITCHBEND_MIN):   # is pitchbend within appropriate range?

         # we are OK, so set pitchbend on the Java synthesizer!
         channelHandle = Java_synthesizer.getChannels()[channel]   # get a handle to channel
         channelHandle.setPitchBend( MIDI_pitchbend )              # send message

         # then, also send message to start the note on this channel
         if panning != -1:                              # if we have a specific panning...
            channelHandle.controlChange(10, panning)       # ... use it (otherwise, we use the default global panning)

         channelHandle.noteOn(pitch, velocity)          # and start the note on Java synthesizer

      else:     # frequency was outside expected range

         print "Play.noteOnPitchBend(): Invalid pitchbend " + str(pitchbend - PITCHBEND_NORMAL) + \
               ", expected pitchbend in range " + str(PITCHBEND_MIN-PITCHBEND_NORMAL) + " to " + str(PITCHBEND_MAX-PITCHBEND_NORMAL) + \
               ".  Perhaps reset global pitch bend via Play.setPitchBend(0)... ?"


   def allNotesOff():
      """It turns off all notes on all channels."""

      Play.allFrequenciesOff()


   def allFrequenciesOff():
      """It turns off all notes on all channels."""

      global Java_synthesizer

      for channel in range(16):  # cycle through all channels
         channelHandle = Java_synthesizer.getChannels()[channel]   # get a handle to channel
         channelHandle.allNotesOff()                               # send the message

         # also reset pitch bend
         Play.setPitchBend(0, channel)


   def stop():
      """It stops all Play music from sounding."""

      # NOTE:  This could also handle Play.note() notes, which may have been
      #        scheduled to start sometime in the future.  For now, we assume that timer.py
      #        (which provides Timer objects) handles stopping of timers on its own.  If so,
      #        this takes care of our problem, for all practical purposes.  It is possible
      #        to have a race condition (i.e., a note that starts playing right when stop()
      #        is called, but a second call of stop() (e.g., double pressing of a stop button)
      #        will handle this, so we do not concern ourselves with it.

      # first, stop the internal __getMidiSynth__ synthesizers
      __stopMidiSynths__()

      # then, stop all sounding notes
      Play.allNotesOff()
      Play.allAudioNotesOff()

      # NOTE: In the future, we may also want to handle scheduled notes through Play.note().  This could be done
      # by creating a list of Timers created via note() and looping through them to stop them here.


   def setInstrument(instrument, channel=0):
      """Send a patch change message for this channel to the Java synthesizer object."""

      global Java_synthesizer

      channelHandle = Java_synthesizer.getChannels()[channel]   # get a handle to channel
      channelHandle.programChange(channel, instrument)          # send the message

   def getInstrument(channel=0):
      """Gets the current instrument for this channel of the Java synthesizer object."""

      global Java_synthesizer

      channelHandle = Java_synthesizer.getChannels()[channel]   # get a handle to channel
      instrument = channelHandle.getProgram()                   # get the instrument
      return instrument

   def setVolume(volume, channel=0):
      """Sets the current coarse volume for this channel to the Java synthesizer object."""

      global Java_synthesizer

      channelHandle = Java_synthesizer.getChannels()[channel]   # get a handle to channel
      channelHandle.controlChange(7, volume)                    # send the message

   def getVolume(channel=0):
      """Gets the current coarse volume for this channel of the Java synthesizer object."""

      global Java_synthesizer

      channelHandle = Java_synthesizer.getChannels()[channel]   # get a handle to channel
      return channelHandle.getController(7)                     # obtain the current value for volume controller

   def setPanning(panning, channel=0):
      """Sets the current panning setting for this channel to the Java synthesizer object."""

      global Java_synthesizer

      channelHandle = Java_synthesizer.getChannels()[channel]   # get a handle to channel
      channelHandle.controlChange(10, panning)                  # send the message

   def getPanning(channel=0):
      """Gets the current panning setting for this channel of the Java synthesizer object."""

      global Java_synthesizer

      channelHandle = Java_synthesizer.getChannels()[channel]   # get a handle to channel
      return channelHandle.getController(10)                # obtain the current value for panning controller


   def audio(material, listOfAudioSamples, listOfEnvelopes = []):
      """Play jMusic material using a list of audio samples as voices"""

      # do necessary datatype wrapping (MidiSynth() expects a Score)
      if type(material) == Note:
         material = Phrase(material)
      if type(material) == jNote:    # (also wrap jMusic default Notes, in addition to our own)
         material = Phrase(material)
      if type(material) == Phrase:   # no elif - we need to successively wrap from Note to Score
         material = Part(material)
      if type(material) == jPhrase:  # (also wrap jMusic default Phrases, in addition to our own)
         material = Part(material)
      if type(material) == Part:     # no elif - we need to successively wrap from Note to Score
         material = Score(material)
      if type(material) == Score:

         # we are good - let's play it then!

         score = material   # by now, material is a score, so create an alias (for readability)

        # loop through all parts and phrases to get all notes
         noteList = []               # holds all notes
         tempo = score.getTempo()    # get global tempo (can be overidden by part and phrase tempos)
         for part in score.getPartArray():   # traverse all parts
            #NOTE: channel is used as an index for the audio voice
            channel = part.getChannel()        # get part channel
            instrument = part.getInstrument()  # get part instrument
            if part.getTempo() > -1:           # has the part tempo been set?
               tempo = part.getTempo()            # yes, so update tempo
            for phrase in part.getPhraseArray():   # traverse all phrases in part
               if phrase.getInstrument() > -1:        # is this phrase's instrument set?
                  instrument = phrase.getInstrument()    # yes, so it takes precedence
               if phrase.getTempo() > -1:          # has the phrase tempo been set?
                  tempo = phrase.getTempo()           # yes, so update tempo

               # time factor to convert time from jMusic Score units to milliseconds
               # (this needs to happen here every time, as we may be using the tempo from score, part, or phrase)
               FACTOR = 1000 * 60.0 / tempo

               for index in range(phrase.length()):      # traverse all notes in this phrase
                  note = phrase.getNote(index)              # and extract needed note data
                  frequency = note.getFrequency()
                  panning = note.getPan()
                  panning = mapValue(panning, 0.0, 1.0, 0, 127)    # map from range 0.0..1.0 (Note panning) to range 0..127 (as expected by Java synthesizer)
                  start = int(phrase.getNoteStartTime(index) * FACTOR)  # get time and convert to milliseconds

                  # NOTE:  Below we use note length as opposed to duration (getLength() vs. getDuration())
                  # since note length gives us a more natural sounding note (with proper decay), whereas
                  # note duration captures the more formal (printed score) duration (which sounds unnatural).
                  duration = int(note.getLength() * FACTOR)             # get note length (as oppposed to duration!) and convert to milliseconds
                  velocity = note.getDynamic()

                  # accumulate non-REST notes
                  if (frequency != REST):
                     noteList.append((start, duration, frequency, velocity, channel, instrument, panning))   # put start time first and duration second, so we can sort easily by start time (below),
                     # and so that notes that are members of a chord as denoted by having a duration of 0 come before the note that gives the specified chord duration

         # sort notes by start time
         noteList.sort()

         # Schedule playing all notes in noteList
         chordNotes = []      # used to process notes belonging in a chord
         for start, duration, pitch, velocity, channel, instrument, panning in noteList:
            # set appropriate instrument for this channel
            Play.setInstrument(instrument, channel)

            # handle chord (if any)
            # Chords are denoted by a sequence of notes having the same start time and 0 duration (except the last note
            # of the chord).
            if duration == 0:   # does this note belong in a chord?
               chordNotes.append([start, duration, pitch, velocity, channel, panning])  # add it to the list of chord notes

            elif chordNotes == []:   # is this a regular, solo note (not part of a chord)?

               # yes, so schedule it to play via a Play.audioNote event
               if len(listOfEnvelopes) != 0:
                  Play.audioNote(pitch, start, duration, listOfAudioSamples[channel], velocity, panning, listOfEnvelopes[channel])
               else:
                  Play.audioNote(pitch, start, duration, listOfAudioSamples[channel], velocity, panning)
               #***print "Play.note(" + str(pitch) + ", " + str(int(start * FACTOR)) + ", " + str(int(duration * FACTOR)) + ", " + str(velocity) + ", " + str(channel) + ")"

            else:   # note has a normal duration and it is part of a chord

               # first, add this note together with this other chord notes
               chordNotes.append([start, duration, pitch, velocity, channel, panning])

               # now, schedule all notes in the chord list using last note's duration
               for start, ignoreThisDuration, pitch, velocity, channel, panning in chordNotes:
                  # schedule this note using chord's duration (provided by the last note in the chord)
                  if len(listOfEnvelopes) != 0:
                     Play.audioNote(pitch, start, duration, listOfAudioSamples[channel], velocity, panning, listOfEnvelopes[channel])
                  else:
                     Play.audioNote(pitch, start, duration, listOfAudioSamples[channel], velocity, panning)

                  #***print "Chord: Play.note(" + str(pitch) + ", " + str(int(start * FACTOR)) + ", " + str(int(duration * FACTOR)) + ", " + str(velocity) + ", " + str(channel) + ")"
               # now, all chord notes have been scheduled

               # so, clear chord notes to continue handling new notes (if any)
               chordNotes = []

         # now, all notes have been scheduled for future playing - scheduled notes can always be stopped using
         # JEM's stop button - this will stop all running timers (used by Play.note() to schedule playing of notes)
         #print "Play.note(" + str(pitch) + ", " + str(int(start * FACTOR)) + ", " + str(int(duration * FACTOR)) + ", " + str(velocity) + ", " + str(channel) + ")"

      else:   # error check
         print "Play.audio(): Unrecognized type " + str(type(material)) + ", expected Note, Phrase, Part, or Score."



   def audioNote(pitch, start, duration, audioSample, velocity = 127, panning = -1, envelope = Envelope()):
      """Play a note using an AudioSample for generating the sound."""

      if (type(pitch) == int) and (0 <= pitch <= 127):   # a MIDI pitch?
         # yes, so convert pitch from MIDI number (int) to Hertz (float)
         pitch = noteToFreq(pitch)

      # ***
      # NOTE:  To work with AdditiveSynthesisInstrument (where such an instrument may actually consist of many normal instruments, each with
      #        its own envelope (e.g., instrument.getEnvelope() and insrument.setEnvelope())...),
      #        we use AdditiveSynthesisInstrument.getInstruments(), and then we iterate / repeat the following code, for each
      #        componennt instrument / envelope pair. ***

      # apply envelope to note
      if envelope.getLength() > duration:
         print("Play.audioNote(): Envelope is too large for this note,\n midi: " + str(pitch) + "\nnote length: " + str(duration) + "\nenvelope length: " + str(envelope.getLength()))
      else:

         # now, make everything happen
         playAudioNoteNowTimer = Timer2(start, Play.__playAudioNoteNow__, [pitch, duration, audioSample, velocity, panning, envelope], False)
         playAudioNoteNowTimer.start()


   def __playAudioNoteNow__(pitch, duration, audioSample, velocity, panning, envelope):
      """To play an audio note, using an AudioSample, we need a voice.  Since other notes may be playing in parallel,
	     we need to wait until the last possible moment to get the AudioSample voice through which this note will be sounded.
         This function performs just that, and then schedules all other timers needed to apply envelope changes, to start
         the note sounding, and then stop the note from sounding.

         NOTE:  This is a little convoluted, but required, due to the use of envelopes and Timers to schedule the playing of notes
         into the future.
      """

      # allocate a AudioSample voice to play this pitch
      voice = audioSample.allocateVoiceForPitch(pitch)

      if voice == None:   # is there an available voice?
         raise ValueError("AudioSample does not have enough free voices to play this pitch, " + str(pitch) + ".")

      # now, we have a voice to play this pitch, so do it!!!


      # now create the list of delays that will be passed to the setVolume method
      # convert delays to seconds for the amplitude smoother
      attackDelays = []
      attackTimes = envelope.getAttackTimes()
      for i in range(len(attackTimes)):
         attackDelays.append(float(attackTimes[i]) / 1000.0)
      # now we have a list of how long each attack lasts in seconds

      delayDelay = float(envelope.getDelay() / 1000.0)
      releaseDelay = float(envelope.getRelease() / 1000.0)
      # and how long the delay and release lasts in seconds

      # adjust attackValues relative to note velocity
      relativeAttackValues = []
      for i in range( len(envelope.getAttackValues() ) ):
         relativeValue = mapValue( envelope.getAttackValues()[i], 0.0, 1.0, 0, velocity )   # adjust
         relativeAttackValues.append( relativeValue )                                       # and remember

      # adjust sustainValue relative to note velocity
      relativeSustainValue = mapValue( envelope.sustainValue, 0.0, 1.0, 0, velocity )

      # ***
      # NOTE:  Here is probably where we get clicking sound... to test (perhaps add a little bit extra to release time,
      #        i.e., to lower the volume competely a little before the actual end of the note...).


      # get absolute release time
      absoluteReleaseTime = duration - envelope.getRelease()

      # create list of timers to perform volume changes
      attackTimers = []

      # first, create timers for envelope attack
      for i in range( len(relativeAttackValues) ):
          timerOffset = envelope.__getAbsoluteAttackTimes__()[i]
          volume = relativeAttackValues[i]
          delay = attackDelays[i]
          timer = Timer2(timerOffset, audioSample.setVolume, [volume, voice, delay], False)
          attackTimers.append( timer )

      # now, create timers for envelope sustain and release
      sustainTimer = Timer2(envelope.__getAbsoluteDelay__(), audioSample.setVolume, [relativeSustainValue, voice, delayDelay], False)
      releaseTimer = Timer2(absoluteReleaseTime, audioSample.setVolume, [0, voice, releaseDelay], False)


      # finally, create timers for note-on and note-off events
      audioOn  = Timer2(0, Play.__audioOn__, [pitch, audioSample, voice, velocity, panning], False)
      audioOff = Timer2(duration, Play.__audioOff__, [pitch, audioSample, voice], False)

      # everything is ready, so start timers to schedule playng of note
      audioOn.start()                      # start note

      # start envelopes
      for i in range(len(attackTimers)):
        attackTimers[i].start()
      sustainTimer.start()
      releaseTimer.start()

      # stop note
      audioOff.start()

      # and, finally, deallocate this AudioSample voice, to free it for other / future pitches
      deallocateVoiceTimer = Timer2(duration, audioSample.deallocateVoiceForPitch, [pitch], False)
      deallocateVoiceTimer.start()


   def __audioOn__(pitch, audioSample, voice, velocity = 127, panning = -1):
      """Start playing a specific pitch at a given volume using provided audio sample."""

      if panning != -1:                              # if we have a specific panning...
         audioSample.setPanning(panning, voice)         # then, use it (otherwise let default / global panning stand
      else:                                          # otherwise...
         audioSample.setPanning( Play.getPanning(), voice )   # use the global / default panning

      audioSample.setFrequency(pitch, voice)         # set the sample to the specified frequency
      audioSample.setVolume(velocity, voice)         # and specified volume

      # NOTE: Here we have a choice - either use audioSample.play() or audioSample.loop()
      # This makes a difference IF the length of note being played is longer than the audio sample
      # being used.  In this case, play() will end before the note's end, whereas loop() will
      # keep looping the audio sample until the end of the note.  We opt for loop(), hoping that
      # the audio sample has been prepared to be nicely loopable (and also, stopping in the midst of it,
      # still sounds OK).  So, this puts extra work on the audio sample preparer / end-user...
      # but makes better sense overall...

      audioSample.loop(voice)                        # and play the pitch!


   def __audioOff__(pitch, audioSample, voice):
      """Stop playing the specified pitch on the provided audio sample."""
      audioSample.stop(voice)



   def allAudioNotesOff():
      """It turns off all notes on all audio samples."""

      # NOTE:  We are probably overreaching here... as this will stop *all* AudioSamples from playing.
      # This is a quick way to stop music played via Play.audio().
      __stopActiveAudioInstruments__()

      # NOTE: In the future, we may also want to handle scheduled notes through Play.audio().  This could be done
      # by creating a list of AudioSamples and Timers created via audioNote() and looping through them to stop them here.


   # NOTE: Experimental - plays scores with audio instruments and MIDI instruments - without chords
   def sound(material, listOfAudioSamples, listOfEnvelopes = []):
      """Play jMusic material using a list of audio samples or MIDI instruments as voices"""

      # do necessary datatype wrapping (MidiSynth() expects a Score)
      if type(material) == Note:
         material = Phrase(material)
      if type(material) == jNote:    # (also wrap jMusic default Notes, in addition to our own)
         material = Phrase(material)
      if type(material) == Phrase:   # no elif - we need to successively wrap from Note to Score
         material = Part(material)
      if type(material) == jPhrase:  # (also wrap jMusic default Phrases, in addition to our own)
         material = Part(material)
      if type(material) == Part:     # no elif - we need to successively wrap from Note to Score
         material = Score(material)
      if type(material) == Score:

         # we are good - let's play it then!

         score = material   # by now, material is a score, so create an alias (for readability)

        # loop through all parts and phrases to get all notes
         noteList = []               # holds all notes
         tempo = score.getTempo()    # get global tempo (can be overidden by part and phrase tempos)
         for part in score.getPartArray():   # traverse all parts
            #NOTE: channel is used as an index for the audio voice
            channel = part.getChannel()        # get part channel
            instrument = part.getInstrument()  # get part instrument
            if part.getTempo() > -1:           # has the part tempo been set?
               tempo = part.getTempo()            # yes, so update tempo
            for phrase in part.getPhraseArray():   # traverse all phrases in part
               if phrase.getInstrument() > -1:        # is this phrase's instrument set?
                  instrument = phrase.getInstrument()    # yes, so it takes precedence
               if phrase.getTempo() > -1:          # has the phrase tempo been set?
                  tempo = phrase.getTempo()           # yes, so update tempo

               # time factor to convert time from jMusic Score units to milliseconds
               # (this needs to happen here every time, as we may be using the tempo from score, part, or phrase)
               FACTOR = 1000 * 60.0 / tempo

               for index in range(phrase.length()):      # traverse all notes in this phrase
                  note = phrase.getNote(index)              # and extract needed note data
                  frequency = note.getFrequency()
                  panning = note.getPan()
                  panning = mapValue(panning, 0.0, 1.0, 0, 127)    # map from range 0.0..1.0 (Note panning) to range 0..127 (as expected by Java synthesizer)
                  start = int(phrase.getNoteStartTime(index) * FACTOR)  # get time and convert to milliseconds

                  # NOTE:  Below we use note length as opposed to duration (getLength() vs. getDuration())
                  # since note length gives us a more natural sounding note (with proper decay), whereas
                  # note duration captures the more formal (printed score) duration (which sounds unnatural).
                  duration = int(note.getLength() * FACTOR)             # get note length (as oppposed to duration!) and convert to milliseconds
                  velocity = note.getDynamic()

                  # accumulate non-REST notes
                  if (frequency != REST):
                     noteList.append((start, duration, frequency, velocity, channel, instrument, panning))   # put start time first and duration second, so we can sort easily by start time (below),
                     # and so that notes that are members of a chord as denoted by having a duration of 0 come before the note that gives the specified chord duration

         # sort notes by start time
         noteList.sort()

         # Schedule playing all notes in noteList
         for start, duration, pitch, velocity, channel, instrument, panning in noteList:

            # this function only supports a regular, solo note (not part of a chord)

            if type(listOfAudioSamples[channel]) == int:   # is this a MIDI instrument?

               # set appropriate instrument for this channel
               Play.setInstrument(listOfAudioSamples[channel], channel)

               # schedule this note using MIDI synthesizer
               Play.note(pitch, start, duration, velocity, channel, panning)

            # else, check if this is an audio instrument
            elif isinstance( listOfAudioSamples[channel], AudioSample ):

               # yes, so play it accordingly
               if len(listOfEnvelopes) != 0:
                  Play.audioNote(pitch, start, duration, listOfAudioSamples[channel], velocity, panning, listOfEnvelopes[channel])
               else:
                  Play.audioNote(pitch, start, duration, listOfAudioSamples[channel], velocity, panning)

            # else, this is a mistake
            else:
               raise TypeError( "Play.sound(): Unrecognized instrument type " + str(type(listOfAudioSamples[channel])) + ", expected AudioSample, or int (i.e., a MIDI instrument)." )

         # now, all notes have been scheduled for future playing - scheduled notes can always be stopped using
         # JEM's stop button - this will stop all running timers (used by Play.note() to schedule playing of notes)
         #print "Play.note(" + str(pitch) + ", " + str(int(start * FACTOR)) + ", " + str(int(duration * FACTOR)) + ", " + str(velocity) + ", " + str(channel) + ")"

      else:   # error check
         print "Play.sound(): Unrecognized type " + str(type(material)) + ", expected Note, Phrase, Part, or Score."


   ########################################################################
   # make these functions callable without having to instantiate this class
   midi = Callable(midi)
   midi2 = Callable(midi2)
   noteOn = Callable(noteOn)
   noteOnPitchBend = Callable(noteOnPitchBend)
   noteOff = Callable(noteOff)
   note = Callable(note)
   frequency = Callable(frequency)
   #microtonal = Callable(microtonal)
   #noteOffPitchBend = Callable(noteOffPitchBend)
   allNotesOff = Callable(allNotesOff)
   frequencyOn = Callable(frequencyOn)
   frequencyOff = Callable(frequencyOff)
   allFrequenciesOff = Callable(allFrequenciesOff)
   stop = Callable(stop)
   setInstrument = Callable(setInstrument)
   getInstrument = Callable(getInstrument)
   setVolume = Callable(setVolume)
   getVolume = Callable(getVolume)
   setPanning = Callable(setPanning)
   getPanning = Callable(getPanning)
   setPitchBend = Callable(setPitchBend)
   getPitchBend = Callable(getPitchBend)
   #setPitchBendNormal = Callable(setPitchBendNormal)
   audioNote = Callable(audioNote)
   __playAudioNoteNow__ = Callable(__playAudioNoteNow__)
   audio = Callable(audio)
   __audioOn__ = Callable(__audioOn__)
   __audioOff__ = Callable(__audioOff__)
   allAudioNotesOff = Callable(allAudioNotesOff)
   sound = Callable(sound)


######################################################################################
# If running inside JEM, register function that stops music from playing, when the
# Stop button is pressed inside JEM.
######################################################################################

try:

    # if we are inside JEM, registerStopFunction() will be available
    registerStopFunction(Play.stop)   # tell JEM which function to call when the Stop button is pressed

except:  # otherwise (if we get an error), we are NOT inside JEM

    pass    # so, do nothing.




######################################################################################
#### AudioInstruments and supporting classes #########################################
######################################################################################


from java.io import *  # for File

from math import *

# used to keep track which AudioSample and LiveSample objects are active, so we can stop them when
# JEM's Stop button is pressed
__ActiveAudioInstruments__ = []     # holds active AudioSample and LiveSample objects


from com.jsyn import JSyn

class Synthesizer():
   """
   This implementation of synthesizer follows the Singleton design pattern. Only one
   instance of Synthesizer may exist. Any new ones create will point to this instance.
   https://en.wikipedia.org/wiki/Singleton_pattern
   """

   instance = None     # ensure one instance by keeping instance outside of the init
   synthRunning = False

   def __init__(self):
      if not Synthesizer.instance:
         Synthesizer.instance = JSyn.createSynthesizer()

   def getInstance(self):
      return  Synthesizer.instance

   def startSynth(self):
      """
      Starts the synthesizer with the appropriate parameters.
      """
      if not Synthesizer.synthRunning:
         temporarySynth  =   JSyn.createSynthesizer()
         framerate       = temporarySynth.getFrameRate()

         audioDeviceManager  = temporarySynth.getAudioDeviceManager()                  # create an audioDeviceManager to access import and output devices
         inputPortID         = audioDeviceManager.getDefaultInputDeviceID()            # use default audio input
         inputChannels       = audioDeviceManager.getMaxInputChannels( inputPortID )   # get the max number of channels for default input device
         outputPortID        = audioDeviceManager.getDefaultOutputDeviceID()           # use default audio output
         outputChannels      = audioDeviceManager.getMaxOutputChannels( outputPortID ) # get the max number of channels for default output device

         del temporarySynth

         Synthesizer.instance.start( framerate, inputPortID, inputChannels, outputPortID, outputChannels )
         Synthesizer.synthRunning = True

   def stopSynth(self):
      """
      Both stop and delete this synth.
      """
      if Synthesizer.synthRunning:
         Synthesizer.instance.stop()
         del Synthesizer.instance
         Synthesizer.instance = None
         Synthesizer.synthRunning = False

   def getFrameRate(self):
      return self.instance.getFrameRate()


from com.jsyn.unitgen import Multiply, LinearRamp


class SynthUnit():
   """
   Creates a pass-through audio pipeline, which has one input and one output port per channel (default is 1, i.e., mono).
   It also provides an amplitude (volume) control (which is global, i.e., same across all channels).
   Finally, it provides a way to inject special effect units into this pipeline (e.g., filters, reverb, etc.) into the pipeline.

   NOTE:  This is intended to create mono (1 channel) or stereo (2 channel) pipelines.  However, it has been
          build to work for an arbitrary number of channels (if ever needed)...
   """

   def __init__(self, synth, channels=1):

      self.numChannels = channels  # how many channels to provide (1 means mono, 2 means stereo)

      self.inputs = []  # list of input ports (as many as channels)
      self.outputs = []  # list of output ports (as many as channels)
      self.amplitudes = []  # list of amplitude controls (linear ramps) used to control amplitude (as many as channels)
      # self.lastUnits   = []         # list of last units in channel pipelines (used to add more units as needed)

      self.synth = synth  # remember synth used to add units to

      # self.lastUnit = self

      # NOTE: This is empirically determined, and should NOT require modification.
      self.DELAY = 0.0002  # how slowly to adjust volume (to avoid clicking)

      # now, create all channels (1 means mono, 2 means stereo, etc.)
      for channel in range(self.numChannels):
         self.__createChannel__()  # create next channel

   def __createChannel__(self):
      """
      Create a single channel of the audio pipeline.  May be called repeatedly for more (independent) channels.
      """

      # create the initial multiplier unit (we use this to provide an input port, and to control volume)
      multiplyUnit = Multiply()  # create unit

      # self.lastUnits.append( multiplyUnit )          # remember it
      self.inputs.append(multiplyUnit.inputA)  # remember the input port (this becomes the SynthUnit's input)
      self.outputs.append( multiplyUnit.output)  # remember the output port (for now, this becomes the SynthUnit's output...
      # NOTE: This output may change, if more units added (e.g., filters, reverb, etc.) )

      # create amplitude control and connect it to multiplier's inputB (used as amplitude aka volume)
      amplitudeControlUnit = LinearRamp()  # create unit

      self.amplitudes.append(amplitudeControlUnit)  # remember it
      amplitudeControlUnit.output.connect(multiplyUnit.inputB)  # connect it to multiplier's inputB
      amplitudeControlUnit.input.setup(0.0, 0.5, 1.0)  # set minimum, current, and maximum settings for control
      amplitudeControlUnit.time.set(self.DELAY)  # and how many seconds to take for smoothing amplitude changes

      # add units to synth
      self.synth.add(multiplyUnit)
      self.synth.add(amplitudeControlUnit)

   def setAmplitude(self, amplitude):
      """
      Set amplitude (volume) for all channels.
      """

      if amplitude < 0.0 or amplitude > 1.0:
         print "Amplitude (" + str(volume) + ") should range from 0.0 to 1.0."
      else:
         # everything is OK, so set amplitude to all channels
         for channel in range(self.numChannels):
            amplitudeControlUnit = self.amplitudes[channel]  # get handle to amplitude control unit
            amplitudeControlUnit.input.set(amplitude)  # and adjust amplitude (volume)

   def getAmplitude(self):
      """
      Return amplitude (volume) for all channels.
      """

      # since all amplitude control units share the same amplitude, only one is needed to access the current value
      amplitudeControlUnit = self.amplitudes[0]  # get handle to amplitude control unit
      amplitude = amplitudeControlUnit.input.get()  # and get amplitude (volume)

      return amplitude

   def addUnit(self, unit):
      """
      Add a new unit to the audio pipeline, once per channel.  Assumes the unit has been created already externally,
      and that it is compatible with the pipeline (i.e., it has input and output ports - as many channels as needed).
      """

      if self.numChannels != unit.numChannels:
         print "Unit provided has " + str(unit.numChannels + " channels - instead expected " + str(self.numChannels)) + "."
      else:
         # loop through all channels
         for channel in range(self.numChannels):
         # get last unit in pipeline (may be multiplyUnit, if this is the first unit added, or other (e.g., filter, etc.))

         # connect current last output to this unit's input
            currentOutput = self.outputs[channel]  # get last output in pipeline for current channel
         currentInput = unit.inputs[channel]  # get last output in pipeline for current channel

         # and connect them!!!
         currentOutput.connect(0, currentInput, 0)

         # now that the connection is done, update the new output of the pipeline
         newOutput = unit.outputs[channels]  # get new output of pipeline
         self.outputs[channel] = newOutput  # and remember it (for next time we need to connect something!!!)

         # finally, add this unit to the synth
         channelUnit = unit.units[channel]
         self.synth.add(channelUnit)

         # now, all channels of new unit have been connected to the end of original pipeline,
         # also, the output ports of the new pipeline have been updated to those of the new unit...

         # Ready to roll!!!

from com.jsyn.unitgen import FilterLowPass
class LowPassFilter():
   """
   Creates low-pass filter, where threshold is desired frequency cutoff (i.e., all frequencies BELOW threshold will pass through,
   while all other frequencies will be eliminated).

   NOTE:  This is intended to create mono (1 channel) or stereo (2 channel) pipelines.  However, it has been
          build to work for an arbitrary number of channels (if ever needed)...
   """

   def __init__(self, threshold, channels=1):

      self.numChannels = channels  # how many channels to provide (1 means mono, 2 means stereo)

      self.units = []  # holds units for all channels (1 for mono, 2 for stereo)
      self.inputs = []  # list of input ports (as many as channels)
      self.outputs = []  # list of output ports (as many as channels)

      # loop through all channels
      for channel in range(self.numChannels):
         unit = FilterLowPass()  # create next filter
         unit.frequency.set(threshold)  # set its frequency

         self.units.append(unit)  # and remember it...
         self.inputs.append(unit.input)  # also its input port...
         self.outputs.append(unit.output)  # and its output port

      # now, we have created enough units per channel,
      # also updated the input and output port parallel lists (so that others can find them!)

   def setThreshold(self, threshold):
      """
      Adjust frequency cutoff (i.e., all frequencies BELOW threshold will pass through,
      while all other frequencies will be eliminated).
      """

      if threshold < 8.17 or threshold > 12600.0:
         print "Frequency cutoff (" + str(threshold) + ") should range from 8.17 to 12600.0 (in Hz)."
      else:
         # loop through all channels
         for unit in self.units:
            unit.frequency.set(threshold)  # set frequency cutoff for this channel


   def getThreshold(self):
      """
      Return current frequency cutoff.
      """


      # since all channels have the same frequency cutoff, just get first one...
      threshold = self.units[0].frequency.get()

      return threshold



class AudioInstrument():
   """
   Encapsulates the construction of the audio pipeline shared between all instruments. It is the top most
   class in the instrument hierarchy. This class is voice player agnostic. Subclasses specificy which voice
   player should be instantiated by this super class.
   Volume, panning, starting, stopping, and pausing are handled by this class.
   """

   def __init__(self, channels, voices, volume, voiceClass, *voiceClassArgs):
      # import shared jSyn classes here, so as to not polute the global namespace
      # subclasses will import jSyn classes specific to their own needs
      from com.jsyn.unitgen import LineOut, Pan

      # define the variables that are independent from the polyphonic voices
      self.channels  = channels
      self.maxVoices = voices

      # create the singleton synthsizer
      self.synthesizer = Synthesizer()
      self.synth = Synthesizer().getInstance()

      # initialize the parallel voice pipelines as empty lists
      self.voices             = []   # holds the voiceClass objects supplied by the contructor
                                     # these players are the beginning of the parallel pipeline shared by all instruments
      self.voicesPitches      = []   # holds the corresponding player's set pitch as an integer between 0 and 127
      self.voicesFrequencies  = []   # holds the corresponding player's set frequency as a float
      self.panLefts           = []   # holds panLeft objects to work in tandem with panRights
      self.panRights          = []   # holds panRight objects to work in tandem with panLefts
      self.pannings           = []   # holds panning settings as an integer between 0 and 127 for corresponding players
      self.volumes            = []   # holds volume settings as an integer between 0 and 127 for corresponding players
      self.paused             = []   # holds boolean paused flags for corresponding players
      self.muted              = []   # holds boolean muted flags for corresponding players
      self.playing            = []   # holds boolean playing flags for corresponding players
      self.lineOuts           = []   # holds lineOut objects from which all sound output is produced
                                     # LineOut is the last component in the parallel pipeline
                                     # It mixes output to computer's audio (DAC) card

      self.pitchSounding      = {}  # holds associations between a pitch currently sounding and corresponding voice (one pitch per voice)
                                    # NOTE: Here we are simulating a MIDI synthesizer, which is polyphonic, i.e., allows several pitches to sound simultaneously on a given channel.
                                    # We accomplish this by utilizing the various voices defined by the pipeline above and associating each sounding pitch with a single voice.
                                    # Different pitches are associated with different voices.  We can reserve or allocate a voice to sound a specific pitch, and we can release that
                                    # voice (presumably after the pitch has stopped sounding).  This allows us to easily play polyphonic Scores via Play.audio().

      self.defaultPitch     = A4               # set the default pitch to A4 - voices will modify this on their own
      self.defaultFrequency = 440.0            # set default frequency to 440.0 - voices will modify this on their own

      # interate to produce the appropriate number of parallel voice pipelines
      for voiceIndex in range( self.maxVoices ):
         voice = voiceClass( self.synth, *voiceClassArgs )   # instantiate single player
         self.voices.append( voice )   # add it to list of players

         # initialze voice pitch and frequency lists with their defaults
         self.voicesPitches.append( self.defaultPitch )
         self.voicesFrequencies.append( self.defaultFrequency )

         # create panning control (we simulate this using two pan controls, one for the left channel and
         # another for the right channel) - to pan we adjust their respective pan
         self.panLefts.append( Pan() )
         self.panRights.append( Pan() )

         # now, that panning is set up, initialize it to center
         self.pannings.append( 63 )                      # ranges from 0 (left) to 127 (right) - 63 is center
         self.setPanning( self.pannings[voiceIndex], voiceIndex )  # and initialize

         # NOTE: The two pan controls have only one of their outputs (as their names indicate)
         # connected to LineOut.  This way, we can set their pan value as we would normally, and not worry
         # about clipping (i.e., doubling the output amplitude).  Also, this works for both mono and
         # stereo samples.

         if channels == 1:
            self.voices[voiceIndex].outputs[0].connect( 0, self.panLefts[voiceIndex].input, 0 )
            self.voices[voiceIndex].outputs[0].connect( 0, self.panRights[voiceIndex].input, 0 )
         elif channels == 2:
            self.voices[voiceIndex].outputs[0].connect( 0, self.panLefts[voiceIndex].input, 0 )
            self.voices[voiceIndex].outputs[1].connect( 0, self.panRights[voiceIndex].input, 0 )
         else:
            raise TypeError( "Can only handle mono or stereo input." )              # overkill error checking to cover possible future features


         # set volume for this voice (0 - 127)
         self.volumes.append( volume )                                             # create volume setting for this player
         self.setVolume( volume, voiceIndex )

         # now we are ready for the LineOuts
         self.lineOuts.append( LineOut() )

         # connect inputs of the LineOuts to the outputs of the panners
         self.panLefts[voiceIndex].output.connect( 0, self.lineOuts[voiceIndex].input, 0 )
         self.panRights[voiceIndex].output.connect( 1, self.lineOuts[voiceIndex].input, 1 )

         # initialize the three boolean flag lists
         self.playing.append( True )   # we ARE playing
         self.muted.append( False )    # we are NOT muted
         self.paused.append( False )   # we are NOT paused

         # add everything to the synth
         self.synth.add( self.panLefts[voiceIndex] )
         self.synth.add( self.panRights[voiceIndex] )
         self.synth.add( self.lineOuts[voiceIndex] )

      # This concludes the set up of the parallel voice pipelines. The subclasses can now govern their own specific implementations of certain functionality


   def pause(self, voice=0):
      """
      Pause playing corresponding sample.
      """

      if voice < 0 or voice >= self.maxVoices:

         print "Voice (" + str(voice) + ") should range from 0 to " + str(self.maxVoices) + "."

      else:

         if self.paused[voice]:
            print "This voice is already paused!"
         else:
            self.lineOuts[voice].stop()   # pause playing
            self.paused[voice] = True     # remember sample is paused


   def resume(self, voice=0):
      """
      Resume playing the corresponding sample from the paused position.
      """

      if voice < 0 or voice >= self.maxVoices:

         print "Voice (" + str(voice) + ") should range from 0 to " + str(self.maxVoices) + "."

      else:

         if not self.paused[voice]:
            print "This voice is already playing!"

         else:
            self.lineOuts[voice].start()   # resume playing
            self.isPaused[voice] = False   # remember sample is NOT paused


   def stop(self, voice=0):
      """
      Stop the specified voice.
      """

      if voice < 0 or voice >= self.maxVoices:

         print "Voice (" + str(voice) + ") should range from 0 to " + str(self.maxVoices) + "."
         return None

      else:
         self.lineOuts[voice].stop()


   def stopAll(self):
      """
      Stop all voices.
      """

      for voice in range(self.maxVoices):
         self.lineOuts[voice].stop()


   def isPaused(self, voice=0):
      """
      Return True if the player is paused.  Returns None, if error.
      """

      if voice < 0 or voice >= self.maxVoices:

         print "Voice (" + str(voice) + ") should range from 0 to " + str(self.maxVoices) + "."
         return None

      else:

         return self.isPaused[voice]


   def getVolume(self, voice=0):
      """
      Return coresponding player's current volume (volume ranges from 0 - 127).  Returns None, if error.
      """

      if voice < 0 or voice >= self.maxVoices:

         print "Voice (" + str(voice) + ") should range from 0 to " + str(self.maxVoices) + "."
         return None

      else:

         return self.volumes[voice]


   def setVolume(self, volume, voice=0, delay=0.0002):
      """
      Set corresponding voice's volume (volume ranges from 0 - 127).
      """

      if volume < 0 or volume > 127:
         print "Volume (" + str(volume) + ") should range from 0 to 127."
      else:
         if voice < 0 or voice >= self.maxVoices:

            print "Voice (" + str(voice) + ") should range from 0 to " + str(self.maxVoices) + "."

         else:
            self.volumes[voice] = volume                                  # remember new volume
            amplitude = mapValue(self.volumes[voice], 0, 127, 0.0, 1.0)   # map volume to amplitude
            self.voices[voice].setAmplitude( amplitude )


   def getPanning(self, voice=0):
      """
      Return voice's current panning (panning ranges from 0 - 127).  Returns None, if error.
      """

      if voice < 0 or voice >= self.maxVoices:

         print "Voice (" + str(voice) + ") should range from 0 to " + str(self.maxVoices) + "."
         return None

      else:

         return self.pannings[voice]


   def setPanning(self, panning, voice=0):
      """
      Set panning of a voice (panning ranges from 0 - 127).
      """

      if panning < 0 or panning > 127:
         print "Panning (" + str(panning) + ") should range from 0 to 127."
      else:

         if voice < 0 or voice >= self.maxVoices:

            print "Voice (" + str(voice) + ") should range from 0 to " + str(self.maxVoices) + "."

         else:

            self.pannings[voice] = panning                       # remember it

            panValue = mapValue(panning, 0, 127, -1.0, 1.0)      # map panning from 0,127 to -1.0,1.0

            self.panLefts[voice].pan.set(panValue)               # and set it
            self.panRights[voice].pan.set(panValue)


   def resetVoices(self):
      """
      Loop through all voices, stop them, and reset them to their defaults
      """
      for voice in range( self.maxVoices):
         if self.playing(voice):
            self.stop(voice)      # stop each playing voice

         # proceed to reset defaults
         self.paused[voice]            = False
         self.voicesPitches[voice]     = self.defaultPitch
         self.voicesFrequencies[voice] = self.defaultFrequency
         self.pannings[voice]          = self.setPanning(63, voice)     # setPanning also resets self.panLefts[voice] and self.panRights[voice]
         self.volumes[voice]           = self.setVolume(127, voice)     # setVolume also resets self.linearRamps[voice]

   ### functions associated with allocating and deallocating a voice to play a specific pitch - done to simulating a polyhonic MIDI synthesizer ####

   # NOTE: Here we are simulating a MIDI synthesizer, which is polyphonic, i.e., allows several pitches to sound simultaneously on a given channel.
   # We accomplish this by utilizing the various voices now available within an AudioSample, by associating each sounding pitch with a single voice.
   # Different pitches are associated with different voices.  We can reserve or allocate a voice to sound a specific pitch, and we can release that
   # voice (presumably after the pitch has stopped sounding).  This allows us to easily play polyphonic Scores via Play.audio() - very useful / powerful!!!

   ### Also see Play.audio()

   def allocateVoiceForPitch(self, pitch):
      """
      If pitch is currently sounding, it returns the voice that plays this pitch.
      If pitch is NOT currently sounding, it returns the next available free voice,
      and allocates as associated with this pitch.
      Returns None, if pitch is NOT sounding, and all voices / players are occupied.
      """

      if (type(pitch) == int) and (0 <= pitch <= 127):   # a MIDI pitch?
         # yes, so convert pitch from MIDI number (int) to Hertz (float)
         pitch = noteToFreq(pitch)

      elif type(pitch) != float:                                   # if reference pitch a frequency (a float, in Hz)?

         raise TypeError("Pitch (" + str(pitch) + ") should be an int (range 0 and 127) or float (such as 440.0).")

      # now, assume pitch contains a frequency (float)

      # is pitch currently sounding?
      if self.pitchSounding.has_key(pitch):

         voiceForThisPitch = self.pitchSounding[pitch]   # get voice already allocated for this pitch

      else:   # pitch does not have a voice already allocated, so...

         voiceForThisPitch = self.getNextFreeVoice()     # get next free voice (if any)

         # if a free voice exists...
         if voiceForThisPitch != None:

            self.pitchSounding[pitch] = voiceForThisPitch   # and allocate it!

      # now, return voice for this pitch (it could be None, if pitch is not sounding and no free voices exist!)
      return voiceForThisPitch


   def deallocateVoiceForPitch(self, pitch):
      """
      It assumes this pitch is currently sounding, and returns the voice that plays this pitch.
      If this pitch is NOT currently sounding, it returns the next available free voice.
      Returns None, if the pitch is NOT sounding, and all voices / players are occupied.
      """

      if (type(pitch) == int) and (0 <= pitch <= 127):   # a MIDI pitch?
         # yes, so convert pitch from MIDI number (int) to Hertz (float)
         pitch = noteToFreq(pitch)

      elif type(pitch) != float:                                   # if reference pitch a frequency (a float, in Hz)?

         raise TypeError("Pitch (" + str(pitch) + ") should be an int (range 0 and 127) or float (such as 440.0).")

      # now, assume pitch contains a frequency (float)

      # is pitch currently sounding?
      if self.pitchSounding.has_key(pitch):

         del self.pitchSounding[pitch]   # deallocate voice for this pitch

      else:   # pitch is not currently sounding, so...

         print "But pitch", pitch, "is currently not sounding!!!"


   def getNextFreeVoice(self):
      """
      Return the next available voice, i.e., a player that is not currently playing.
      Returns None, if all voices / players are occupied.
      """

      # find all free voices (not currently playing)
      freeVoices = [voice for voice in range(self.maxVoices) if not voice in self.pitchSounding.values()]

      if len(freeVoices) > 0:   # are there some free voices
         freeVoice = freeVoices[0]
      else:
          freeVoice = None

      return freeVoice


   # Calculate frequency in Hertz based on MIDI pitch. Middle C is 60.0. You
   # can use fractional pitches so 60.5 would give you a pitch half way
   # between C and C#.  (by Phil Burk (C) 2009 Mobileer Inc)
   def __convertPitchToFrequency__(self, pitch):
      """
      Convert MIDI pitch to frequency in Hertz.
      """

      concertA = 440.0
      return concertA * 2.0 ** ((pitch - 69) / 12.0)

   def __convertFrequencyToPitch__(self, freq):
      """
      Converts pitch frequency (in Hertz) to MIDI pitch.
      """

      concertA = 440.0
      return log(freq / concertA, 2.0) * 12.0 + 69

   # following conversions between frequencies and semitones based on code
   # by J.R. de Pijper, IPO, Eindhoven
   # see http://users.utu.fi/jyrtuoma/speech/semitone.html
   def __getSemitonesBetweenFrequencies__(self, freq1, freq2):
      """
      Calculate number of semitones between two frequencies.
      """

      semitones = (12.0 / log(2)) * log(freq2 / freq1)
      return int(semitones)

   def __getFrequencyChangeBySemitones__(self, freq, semitones):
      """
      Calculates frequency change, given change in semitones, from a frequency.
      """

      freqChange = (exp(semitones * log(2) / 12) * freq) - freq
      return freqChange


class SampleInstrument(AudioInstrument):
   """
   This class encapsulates shared functionality between AudioSample and LiveSample. It also possesses
   two inner classes that are passed to the super constructor depending on mono or stereo output.
   """

   def __init__(self, channels, samplePitch, voices, volume, voiceClass, *voiceClassArgs):
      # SampleInstrument.__init__(self, channels, samplePitch, voices, voiceClass, *voiceClassArgs)
      # define locally used variables
      self.samplePitch   = samplePitch               # remember the reference pitch from the constructor
      self.sampleFrequency = None                        # Set reference frequency to None. This will be appropriately reassigned later

      # check if the reference is a midi pitch (int) or a frequency (float)
      # If the reference is neither an int or a float, this is an error. Catch this error in the else block
      if (type(samplePitch) == int) and (0 <= samplePitch <= 127):         # is reference pitch in MIDI (an int)?
         self.sampleFrequency = self.__convertPitchToFrequency__(samplePitch)   # convert the MIDI pitch to a float frequency for use in polyphony pipeline
      elif type(samplePitch) == float:                                  # if reference pitch a frequency (a float, in Hz)?
         self.sampleFrequency = samplePitch                                     # correctly assign the float frequency
         self.samplePitch     = self.__convertFrequencyToPitch__(samplePitch)   # convert the float frequency to MIDI pitch, reassign referencePitch, use in the polyphony pipeline
      else:
         raise TypeError("Reference pitch (" + str(samplePitch) + ") should be an int (range 0 and 127) or float (such as 440.0).")


      AudioInstrument.__init__(self, channels, voices, volume, voiceClass, *voiceClassArgs)

      framerate = self.synthesizer.getFrameRate()

      # ensure the sample is playing at correct pitch by syncing its playback rate and the synth framerate
      for voice in range(self.maxVoices):
         self.voices[voice].__syncFramerate__( framerate )

         # overwrite voice pitch and frequency lists with samplePitch NOT default pitch
         self.voicesPitches[voice] = self.samplePitch
         self.voicesFrequencies[voice] = self.sampleFrequency

         # initialze to correct frequency
         self.setFrequency(self.sampleFrequency, voice)


   def play(self, voice=0, start=0, size=-1):
      """
      Play the corresponding sample once from the millisecond 'start' until the millisecond 'start'+'size'
      (size == -1 means to the end). If 'start' and 'size' are omitted, play the complete sample.
      """

      if voice < 0 or voice >= self.maxVoices:

         print "Voice (" + str(voice) + ") should range from 0 to " + str(self.maxVoices) + "."

      else:
         # for faster response, we restart playing (as opposed to queue at the end)
         if self.isPlaying(voice):      # is another play is on?
            self.stop(voice)            # yes, so stop it

         self.loop(voice, 1, start, size)


   def loop(self, voice=0, times = -1, start=0, size=-1):
      """
      Repeat the corresponding sample indefinitely (times = -1), or the specified number of times
      from millisecond 'start' until millisecond 'start'+'size' (size == -1 means to the end).
      If 'start' and 'size' are omitted, repeat the complete sample.
      """

      if voice < 0 or voice >= self.maxVoices:

         print "Voice (" + str(voice) + ") should range from 0 to " + str(self.maxVoices) + "."

      else:

         startFrames = self.__msToFrames__(start)
         sizeFrames = self.__msToFrames__(size)

         # should this be here?  ***
         self.lineOuts[voice].start()

         if size == -1:    # to the end?
            sizeFrames = self.sample.getNumFrames() - startFrames  # calculate number of frames to the end

         if times == -1:   # loop forever?
            self.voices[voice].samplePlayer.dataQueue.queueLoop( self.sample, startFrames, sizeFrames )

         else:             # loop specified number of times
            self.voices[voice].samplePlayer.dataQueue.queueLoop( self.sample, startFrames, sizeFrames, times-1 )


   def stop(self, voice=0):
      """
      Stop playing the corresponding sample any further and restart it from the beginning.
      """

      if voice < 0 or voice >= self.maxVoices:

         print "Voice (" + str(voice) + ") should range from 0 to " + str(self.maxVoices) + "."

      else:

         self.voices[voice].samplePlayer.dataQueue.clear()
         self.paused[voice] = False  # remember this voice is NOT paused


   def isPlaying(self, voice=0):
      """
      Returns True if the corresponding sample is still playing.  In case of error, returns None.
      """

      print not self.paused[voice]

      if voice < 0 or voice >= self.maxVoices:

         print "Voice (" + str(voice) + ") should range from 0 to " + str(self.maxVoices) + "."
         return None

      else:

         return self.voices[voice].samplePlayer.dataQueue.hasMore()


   def getFrequency(self, voice=0):
      """
      Return sample's playback frequency.  Returns None if error.
      """

      if voice < 0 or voice >= self.maxVoices:

         print "Voice (" + str(voice) + ") should range from 0 to " + str(self.maxVoices) + "."
         return None

      else:
         return self.voicesFrequencies[voice]


   def setFrequency(self, freq, voice=0):
      """
      Set sample's playback frequency.
      """

      if voice < 0 or voice >= self.maxVoices:

         print "Voice (" + str(voice) + ") should range from 0 to " + str(self.maxVoices) + "."

      else:

         #self.voices[voice].setFrequency( freq )
         rateChangeFactor = float(freq) / self.voicesFrequencies[voice]                         # calculate change on playback rate
         self.voicesFrequencies[voice] = freq                                                   # remember new frequency
         self.voicesPitches[voice]     = self.__convertFrequencyToPitch__(freq)                 # and corresponding pitch

         self.voices[voice].setFrequency( rateChangeFactor )


   def getPitch(self, voice=0):
      """
      Return voice's current pitch (it may be different from the default pitch).
      """

      if voice < 0 or voice >= self.maxVoices:

         print "Voice (" + str(voice) + ") should range from 0 to " + str(self.maxVoices) + "."
         return None

      else:

         return self.voicesPitches[voice]


   def setPitch(self, pitch, voice=0):
      """
      Set voice's playback pitch.
      """

      if voice < 0 or voice >= self.maxVoices:

         print "Voice (" + str(voice) + ") should range from 0 to " + str(self.maxVoices) + "."

      else:
         self.setFrequency(self.__convertPitchToFrequency__(pitch), voice)   # update playback frequency (this changes the playback rate)


   def __setPlaybackRate__(self, newRate, voice=0):
      """
      Set the corresponding sample's playback rate (e.g., 44100.0 Hz).
      """

      if voice < 0 or voice >= self.maxVoices:

         print "Voice (" + str(voice) + ") should range from 0 to " + str(self.maxVoices) + "."
         return None

      else:

         self.voices[voice].rate.set( newRate )


   def __getPlaybackRate__(self, voice=0):
      """
      Return the corresponding sample's playback rate (e.g., 44100.0 Hz).
      """

      if voice < 0 or voice >= self.maxVoices:

         print "Voice (" + str(voice) + ") should range from 0 to " + str(self.maxVoices) + "."
         return None

      else:

         return self.voices[voice].rate.get()


   def __msToFrames__(self, milliseconds):
      """
      Converts milliseconds to frames based on the frame rate of the sample
      """

      return int(self.sample.getFrameRate() * (milliseconds / 1000.0))



class LiveSample(SampleInstrument):
   """
   Encapsulates a sound object created from live sound via the computer microphone (or line-in),
   which can be played once, looped, paused, resumed, stopped, copied and erased.
   The first parameter, maxSizeInSeconds, is the recording capacity (default is 30 secs).
   The larger this value, the more memory the object occupies, so this needs to be handled carefully.
   Finally, we can set/get its volume (0-127), panning (0-127), pitch (0-127), and frequency (in Hz).
   """

   def __init__(self, maxRecordingTime=30, samplePitch=A4, effects=[], voices=16, volume=127):
      # import LiveSample specific classes. We need JSyn here because LiveSample needs access to
      # audioDeviceManager. ChannelIn and LineIn allow input from a microphone. FixedRateMonoWriter
      # and FixedRateStereoWriter allow recording from that input. FloatSample holds this recorded audio
      from com.jsyn import JSyn
      from com.jsyn.unitgen import ChannelIn, LineIn, FixedRateMonoWriter, FixedRateStereoWriter, VariableRateMonoReader, VariableRateStereoReader
      from com.jsyn.data import FloatSample

      voiceClass = self.Voice


      self.maxRecordingTime        = maxRecordingTime
      self.actualRecordingTime     = None  # initialize to None, not zero.
      self.beginRecordingTimeStamp = None
      self.endRecordingTimeStamp   = None
      self.isRecording             = False

      self.samplePitch             = samplePitch   # remember the pitch

      self.sampleSize = maxRecordingTime * 1000 # convert seconds into milliseconds
      maxLoopTime     = self.__msToFrames__( self.sampleSize, framerate )

      # create time stamp variables
      self.beginRecordingTimeStamp = None    # holds timestamp of when we start recording into the sample
      self.endRecordingTimeStamp   = None    # holds timestamp of when we stop recording into the sample
      self.isRecording             = False   # boolean flag that is only true when the sample is being written to
      self.recordedSampleSize      = None    # holds overall length of time of the sample rounded to nearest int

      self.sample = FloatSample( maxLoopTime, channels )   # holds recorded audio

      channels = self.__getInputChannels__()   # get the number of input channels from the default input device

      voiceClassArgs = []
      voiceClassArgs.append(channels)
      voiceClassArgs.append(samplePitch)
      voiceClassArgs.append(effects)

      # ensure mono or stereo audio input
      if not (channels == 1 or channels == 2):    # not mono or stereo audio?
         raise TypeError( "Can only record from mono or stereo input." )
      else:
         if channels == 2:    # stereo audio input?
            # If input is stereo, we must use a LineIn. LineIn assumes stereo and we have stereo in this case.
            self.lineIn = LineIn()                                    # create input line (stereo)
            self.recorder = FixedRateStereoWriter()                   # captures incoming audio (stereo)
            self.lineIn.output.connect( 0, self.recorder.input, 0 )   # connect line input to the sample writer (recorder)
            self.lineIn.output.connect( 0, self.recorder.input, 1 )

         elif channels == 1:  # mono audio input?
            # If input is mono, we must use a single channelIn. LineIn assumes stereo. For simplicity, we still name the variable lineIn.
            self.lineIn = ChannelIn()                                   # create input line (mono)
            self.recorder = FixedRateMonoWriter()                       # captures incoming audio (mono)
            self.lineIn.output.connect( 0, self.recorder.input, 0 )     # connect channel input to the sample writer (recorder)

      # Now that LiveSample specific information has been set, initialize the Instrument
      SampleInstrument.__init__( self, channels, samplePitch, voices, volume, voiceClass, *voiceClassArgs)

      # add LiveSample specific data to the synthesizer
      self.synth.add( self.lineIn )
      self.synth.add( self.recorder )

      # start the synth correctly
      self.synthesizer.startSynth()

      # remember that this Instrument has been created and is active (so that it can be stopped by JEM, if desired)
      __ActiveAudioInstruments__.append(self)


   # LiveSample has it's own play function because we need to check if anything exists to play
   def play(self, voice=0, start=0, size=-1):
      """
      Play the corresponding sample once from the millisecond 'start' until the millisecond 'start'+'size'
      (size == -1 means to the end). If 'start' and 'size' are omitted, play the complete sample.
      """
      if voice < 0 or voice >= self.maxVoices:

         print "Voice (" + str(voice) + ") should range from 0 to " + str(self.maxVoices) + "."

      else:
         if self.recordedSampleSize == None:
            print "Sample is empty!  You need to record before you can play."
         else:
            # for faster response, we restart playing (as opposed to queue at the end)
            if self.isPlaying(voice):      # is the sample already playing?
               self.stop(voice)            # yes, so stop it

            self.loop(voice, 1, start, size)

   # LiveSample has a specific loop function because it requires more error checking than other audio sources.
   # LiveSample must be sure all durations and framerates are acceptable before looping can be successful.
   def loop(self, voice=0, times = -1, start=0, size=-1):
      """
      Repeat the corresponding sample indefinitely (times = -1), or the specified number of times
      from millisecond 'start' until millisecond 'start'+'size' (size == -1 means to the end).
      If 'start' and 'size' are omitted, repeat the complete sample.
      """

      if voice < 0 or voice >= self.maxVoices:

         print "Voice (" + str(voice) + ") should range from 0 to " + str(self.maxVoices) + "."

      else:
         if self.recordedSampleSize == None: # is the sample currently empty?
            print "Sample is empty!  You need to record before you can loop."
            return -1

         sampleTotalDuration = (self.recordedSampleSize / self.synth.getFrameRate()) * 1000 # total time of sample in milliseconds

         # is specified start time within the total duration of sample?
         if start < 0 or start > sampleTotalDuration:
            print "Start time provided (" + str(start) + ") should be between 0 and sample duration (" + str(sampleTotalDuration) + ")."
            return -1

         # does the size specified exceed the total duration of the sample or is size an invalid value?
         if size == 0 or start + size > sampleTotalDuration:
            print "Size (" + str(size) + ") exceeds total sample duration (" + str(sampleTotalDuration) + "), given start ("+ str(start) + ")."
            return -1

         # was the size specified less than the lowest value allowed?
         if size <= -1:
            size = self.recordedSampleSize # play to the end of the sample
         else:
            size = (size/1000) * self.framerate # convert milliseconds into frames
            start = (start/1000) * self.framerate

         # loop the sample continuously?
         if times == -1:
            self.voices[voice].samplePlayer.dataQueue.queueLoop(self.sample, start, size)

         if times == 0:
            print "But, don't you want to play the sample at least once?"
            return -1

         else:
            # Subtract 1 from number of times a sample should be looped.
            # 'times' is the number of loops of the sample after the initial playing.
            self.voices[voice].samplePlayer.dataQueue.queueLoop(self.sample, start, size, times - 1)

         self.lineOuts[voice].start()   # starts playing the voice


   def startRecording(self):
      """
      Writes lineIn data to the sample data structure.
      Gets a time stamp so that, when we stop, we may calculate the duration of the recording.
      """

      # make sure sample is empty
      if self.recordedSampleSize != None:
         print "Warning: cannot record over an existing sample.  Use erase() first, to clear it."

      else:   # sample is empty, so it's OK to record
         print "Recording..."

         # make sure we are not already recording
         if not self.isRecording:

            # get timestamp of when we started recording,
            # so, later, we can calculate duration of recording
            self.beginRecordingTimeStamp = self.synth.createTimeStamp()

            # start recording into the sample
            # (self.recorder will update self.sample - the latter is passive, just a data holder)
            self.recorder.dataQueue.queueOn( self.sample )    # connect the writer to the sample

            self.recorder.start()                             # and write into it

            self.isRecording = True  # remember that recording has started

         else:   # otherwise, we are already recording, so let them know
            print "But, you are already recording..."


   def stopRecording(self):
      """
      Stops the writer from recording into the sample data structure.
      Also, gets another time stamp so that, now, we may calculate the duration of the recording.
      """

      # make sure we are currently recording
      if not self.isRecording:
         print "But, you are not recording!"

      else:
         print "Stopped recording."

         # stop writer from recording into the sample
         self.recorder.dataQueue.queueOff( self.sample )
         self.recorder.stop()

         self.isRecording = False  # remember that recording has stopped

         # now, let's calculate duration of recording

         # get a new time stamp
         self.endRecordingTimeStamp =  self.synth.createTimeStamp()

         # calculate number of frames in the recorded sample
         # (i.e., total duration in seconds x framerate)
         startTime = self.beginRecordingTimeStamp.getTime()  # get start time
         endTime = self.endRecordingTimeStamp.getTime()      # get end time
         recordingTime = endTime - startTime                 # recording duration (in seconds)

         # if we have recorded more than we can store, then we will truncate
         # (that's the least painful solution...)
         recordingCapacity = self.sampleSize / 1000   # convert to seconds
         if recordingTime > recordingCapacity:

         # let them know
            exceededSeconds = recordingTime-recordingCapacity  # calculate overun
            print "Warning: Recording too long (by", round(exceededSeconds, 2), " secs)... truncating!"

                # truncate extra recording (by setting sample duration to max recording capacity)
            sampleDuration = self.sampleSize / 1000
         else:
            # sample duration is within the recording capacity
            sampleDuration = recordingTime

         framerate = self.synth.getFrameRate()
         # let's remember duration of recording (convert to frames - an integer)
         self.recordedSampleSize = int(framerate * sampleDuration)


   # erase makes use of both self.recorder and self.sample and self.referencePitch. We will need these.
   def erase(self):
      """
      Erases all contents of the LiveSample.
      """

      # is sample currently recording?
      if self.isRecording:
         print "Cannot erase while recording!"

      self.resetVoices()   # reset all voices to their defaults

      # Now that individual voices have been stopped and reset, we can reset the source recorder by
      # clearing the dataQueue. Now, recording of the sample will start at the beginning
      self.recorder.dataQueue.clear()

      # rewrite audio data within sample frame by frame (0.0 means empty frame - no sound)
      for i in range(self.sample.getNumFrames()):
         self.sample.writeDouble(i, 0.0)

      # set sample size to empty
      self.recordedSampleSize = None


   def __getInputChannels__(self):
      """
      Creates a temportary synth to poll the audio card for input device information.
      The number of input channels is necessary to determine which recording unit
      we need to use.
      """
      temporarySynth      =   JSyn.createSynthesizer()
      audioDeviceManager  = temporarySynth.getAudioDeviceManager()                  # create an audioDeviceManager to access import and output devices

      inputPortID         = audioDeviceManager.getDefaultInputDeviceID()            # use default audio input
      inputChannels       = audioDeviceManager.getMaxInputChannels( inputPortID )   # get the max number of channels for default input device

      del audioDeviceManager
      del temporarySynth

      return inputChannels


   def __msToFrames__(self, milliseconds, framerate):
      """
      Converts milliseconds to frames based on the frame rate of the sample
      """
      return int(framerate * (milliseconds / 1000.0))


   class Voice(SynthUnit):
      def __init__(self, synth, channels, samplePitch=A4):
         from com.jsyn.unitgen import VariableRateMonoReader, VariableRateStereoReader

         SynthUnit.__init__(self, synth, channels)


         if channels == 1:
            self.samplePlayer = VariableRateMonoReader()
            audioPipelineInput = self.inputs[0]
            self.samplePlayer.output.connect(0, audioPipelineInput, 0)
         elif channels == 2:
            self.samplePlayer = VariableRateStereoReader()
            audioPipelineInputLeft  = self.inputs[0]
            audioPipelineInputRight = self.inputs[1]
            self.samplePlayer.output.connect(0, audioPipelineInputLeft, 0)
            self.samplePlayer.output.connect(1, audioPipelineInputRight, 0)
         else:
            raise("Can only play mono or stereo samples.")


         self.setAmplitude(1.0)

         # next, let's add all effects to audio pipeline
         for unit in effects:
            self.addUnit(unit, synth)

         synth.add(self.samplePlayer)


      def setFrequency(self, rateChangeFactor):
         """
         Changes the frequency/pitch of the sample.
         """
         self.samplePlayer.rate.set( rateChangeFactor )
         #self.__setPlaybackRate__(self.__getPlaybackRate__() * rateChangeFactor)   # and set new playback rate


      def __getPlaybackRate__(self):
         """
         Returns the current playback rate of the sample player.
         """
         return self.samplePlayer.rate.get()


      def __setPlaybackRate__(self, newRate):
         """
         Changes frequency/pitch by changing the sample players' playback rate.
         """
         self.samplePlayer.rate.set( newRate )


      def __syncFramerate__(self, framerate):
         """
         Sets the playback rate of the sample player to the framerate of the synth.
         """
         self.samplePlayer.rate.set( framerate )


class AudioSample(SampleInstrument):
   """
   Encapsulates a sound object created from an external audio file, which can be played once,
   looped, paused, resumed, and stopped.  Also, each sound has a MIDI pitch associated with it
   (default is A4), so we can play different pitches with it (through pitch shifting).
   The soud object allows for polyphony - the default is 16 different voices, which can be played,
   pitch-shifted, looped, etc. indepedently from each other.
   Finally, we can set/get its volume (0-127), panning (0-127), pitch (0-127), and frequency (in Hz).
   Ideally, an audio object will be created with a specific pitch in mind.
   Supported data formats are WAV or AIF files (16, 24 and 32 bit PCM, and 32-bit float).
   """

   def __init__(self, filename, samplePitch=A4, effects=[], voices=16, volume=127):
      # import AudioSample specific jSyn classes here. We need os to ensure a source
      # file exists. SampleLoader retrieves the sample and stores it in FloatSample
      import os
      from com.jsyn.data import FloatSample
      from com.jsyn.util import SampleLoader
      from com.jsyn.unitgen import VariableRateMonoReader, VariableRateStereoReader

      # do we have a file?
      if not os.path.isfile(filename):
         raise ValueError("File '" + str(filename) + "' does not exist.")

      voiceClass = self.Voice

      # load and create the audio sample
      SampleLoader.setJavaSoundPreferred( False )             # use internal jSyn sound processes
      datafile = File(filename)                               # get sound file
      self.sample = SampleLoader.loadFloatSample( datafile )  # load it as a a jSyn sample
      channels = self.sample.getChannelsPerFrame()            # get number of channels in sample (1 or 2)

      voiceClassArgs = []
      voiceClassArgs.append(channels)
      voiceClassArgs.append(samplePitch)
      voiceClassArgs.append(effects)

      framerate = self.sample.getFrameRate()                  # get framerate from the SAMPLE, not the synthesizer

      # call the super constructor with
      SampleInstrument.__init__(self, channels, samplePitch, voices, volume, voiceClass, *voiceClassArgs)

                  #def __init__(self, channels, samplePitch, voices, volume, voiceClass, *voiceClassArgs):

      self.synthesizer.startSynth()

      # also, the original audio sample uses the SAMPLE's framerate, not the synth's
      # self.player.rate.set( self.sample.getFrameRate()

      # remember that this Instrument has been created and is active (so that it can be stopped by JEM, if desired)
      __ActiveAudioInstruments__.append(self)


   def play(self, voice=0, start=0, size=-1):
      """
      Play the corresponding sample once from the millisecond 'start' until the millisecond 'start'+'size'
      (size == -1 means to the end). If 'start' and 'size' are omitted, play the complete sample.
      """

      if voice < 0 or voice >= self.maxVoices:

         print "Voice (" + str(voice) + ") should range from 0 to " + str(self.maxVoices) + "."

      else:

         # for faster response, we restart playing (as opposed to queue at the end)
         if self.isPlaying(voice):      # is another play is on?
            self.stop(voice)            # yes, so stop it

         self.loop(voice, 1, start, size)


   def loop(self, voice=0, times = -1, start=0, size=-1):
      """
      Repeat the corresponding sample indefinitely (times = -1), or the specified number of times
      from millisecond 'start' until millisecond 'start'+'size' (size == -1 means to the end).
      If 'start' and 'size' are omitted, repeat the complete sample.
      """

      if voice < 0 or voice >= self.maxVoices:

         print "Voice (" + str(voice) + ") should range from 0 to " + str(self.maxVoices) + "."

      else:

         startFrames = self.__msToFrames__(start)
         sizeFrames = self.__msToFrames__(size)

         if size == -1:    # to the end?
            sizeFrames = self.sample.getNumFrames() - startFrames  # calculate number of frames to the end

         if times == -1:   # loop forever?
            self.voices[voice].samplePlayer.dataQueue.queueLoop( self.sample, startFrames, sizeFrames )

         else:             # loop specified number of times
            self.voices[voice].samplePlayer.dataQueue.queueLoop( self.sample, startFrames, sizeFrames, times-1 )

         self.lineOuts[voice].start()


   def isPlaying(self, voice=0):
      """
      Returns True if the corresponding sample is still playing.  In case of error, returns None.
      """

      print not self.paused[voice]

      if voice < 0 or voice >= self.maxVoices:

         print "Voice (" + str(voice) + ") should range from 0 to " + str(self.maxVoices) + "."
         return None

      else:

         return self.voices[voice].samplePlayer.dataQueue.hasMore()


   def stop(self, voice=0):
      """
      Stop playing the corresponding sample any further and restart it from the beginning.
      """

      if voice < 0 or voice >= self.maxVoices:

         print "Voice (" + str(voice) + ") should range from 0 to " + str(self.maxVoices) + "."

      else:

         self.voices[voice].samplePlayer.dataQueue.clear()
         self.paused[voice] = False  # remember this voice is NOT paused

   class Voice(SynthUnit):
      def __init__(self, synth, channels, samplePitch=A4, effects=[]):
         from com.jsyn.unitgen import VariableRateMonoReader, VariableRateStereoReader


         SynthUnit.__init__(self, synth, channels)


         if channels == 1:
            self.samplePlayer = VariableRateMonoReader()
            audioPipelineInput = self.inputs[0]
            self.samplePlayer.output.connect(0, audioPipelineInput, 0)
         elif channels == 2:
            self.samplePlayer = VariableRateStereoReader()
            audioPipelineInputLeft  = self.inputs[0]
            audioPipelineInputRight = self.inputs[1]
            self.samplePlayer.output.connect(0, audioPipelineInputLeft, 0)
            self.samplePlayer.output.connect(1, audioPipelineInputRight, 0)
         else:
            raise("Can only play mono or stereo samples.")


         self.setAmplitude(1.0)

         # next, let's add all effects to audio pipeline
         for unit in effects:
            self.addUnit(unit, synth)

         synth.add(self.samplePlayer)


      def setFrequency(self, rateChangeFactor):
         """
         Changes the frequency/pitch of the sample.
         """
         #self.samplePlayer.rate.set( rateChangeFactor )

         self.__setPlaybackRate__(self.__getPlaybackRate__() * rateChangeFactor)   # and set new playback rate


      def __getPlaybackRate__(self):
         """
         Returns the current playback rate of the sample player.
         """
         return self.samplePlayer.rate.get()


      def __setPlaybackRate__(self, newRate):
         """
         Changes frequency/pitch by changing the sample players' playback rate.
         """
         self.samplePlayer.rate.set( newRate )


      def __syncFramerate__(self, framerate):
         """
         Sets the playback rate of the sample player to the framerate of the synth.
         """
         self.samplePlayer.rate.set( framerate )



################################################################
### Wave Instruments ###

class WaveInstrument(AudioInstrument):
   """
   Encapsulates shared behavior of all oscillating instruments.
   """

   def __init__(self, channels, voices, volume, voiceClass, *voiceClassArgs):
      """
      Initialize the needed arguments for the super constructor and call it.
      """
      # build basic infrastructure for voices
      AudioInstrument.__init__(self, channels, voices, volume, voiceClass, *voiceClassArgs)


   def start(self, voice=0):
      """
      Begin playing the specified voice.
      """

      if voice < 0 or voice >= self.maxVoices:

         print "Voice (" + str(voice) + ") should range from 0 to " + str(self.maxVoices) + "."
         return None

      else:
         self.lineOuts[voice].start()


   def loop(self, voice=0):
      """
      Calls the start() function because oscillators do not require looping.
      """

      self.start(voice)


   def getFrequency(self, frequency, voice=0):
      """
      Returns the frequency of the specified voice. Returns None if invalid voice is given.
      """

      if voice < 0 or voice >= self.maxVoices:

         print "Voice (" + str(voice) + ") should range from 0 to " + str(self.maxVoices) + "."
         return None

      else:
         return self.voicesFrequencies[voice]


   def setFrequency(self, frequency, voice=0):
      """
      Changes the frequency (i.e., pitch) of the specified voice.
      """

      self.voices[voice].setFrequency( frequency )                              # set frequency of this voice
      self.voicesFrequencies[voice] = frequency
      self.voicesPitches[voice] = self.__convertFrequencyToPitch__( frequency ) # also adjust pitch accordingly (since they are coupled)


   def isPlaying(self, voice=0):
      """
      Returns true if voice is playing. Returns None otherwise.
      """

      if voice < 0 or voice >= self.maxVoices:

         print "Voice (" + str(voice) + ") should range from 0 to " + str(self.maxVoices) + "."
         return None

      else:
         return self.voices[voice].playing


class SinewaveInstrument(WaveInstrument):
   """
   Encapsulates an oscillating sine wave.
   """
   def __init__(self, frequency=440.0, volume=127, effects=[], voices=16, envelope=None):


      if volume < 0 or volume > 127:
         print "Volume (" + str(volume) + ") should range from 0 to 127."
      else:

         if envelope == None:
            self.envelope = Envelope([20],[1.0], 5, 0.8, 15)
         else:
            self.envelope = envelope

         voiceClass = self.Voice

         channels = 1

         voiceClassArgs = []
         voiceClassArgs.append( frequency )
         voiceClassArgs.append( volume )
         voiceClassArgs.append( effects )
         voiceClassArgs.append( channels )

         WaveInstrument.__init__(self, channels, voices, volume, voiceClass, *voiceClassArgs)   # call super constructor
         self.synthesizer.startSynth()

         # remember that this Instrument has been created and is active (so that it can be stopped by JEM, if desired)
         __ActiveAudioInstruments__.append(self)

   def getEnvelope(self):
      """
      Returns the instruments current envelope.
      """
      return self.envelope

   def setEnvelope(self, envelope):
      """
      Sets a new envelope for this instrument.
      """
      # do we need sanity checking here for valid envelopes?
      self.envelope = envelope


   class Voice(SynthUnit):
      def __init__(self, synth, frequency, volume, effects, channels):
         from com.jsyn.unitgen import SineOscillator

         SynthUnit.__init__(self, synth, channels)

         for unit in effects:
            self.addUnit(unit, synth)

         amplitude = mapValue(volume, 0, 127, 0.0, 1.0)
         self.oscillator = SineOscillator()
         self.setFrequency( frequency )

         if channels == 1:
            audioPipelineInput = self.inputs[0]
            self.oscillator.output.connect(0, audioPipelineInput, 0)
         elif channels == 2:
            audioPipelineInputLeft  = self.inputs[0]
            audioPipelineInputRight = self.inputs[1]
            self.oscillator.output.connect(0, audioPipelineInputLeft, 0)
            self.oscillator.output.connect(0, audioPipelineInputRight, 0)
         else:
            raise("Can only play mono or stereo samples.")

         self.oscillator.amplitude.set( amplitude )   # preserve max volume of this instrument
         self.setAmplitude(1.0)

         synth.add(self.oscillator)


      def setFrequency(self, frequency):
         """
         Changes the frequency (i.e., pitch) of the specified voice.
         """
         self.oscillator.frequency.set( frequency )

      def getFrequency(self):
         """
         Returns the current frequency of the oscillator as a float.
         """
         return self.oscillator.frequency.get()


class SquarewaveInstrument(WaveInstrument):
   """
   Encapsulates an oscillating square wave. Defaults to a frequency of 440.0 (A4).
   """
   from com.jsyn.unitgen import SquareOscillator

   def __init__(self, frequency=440.0, volume=127, effects=[], voices=16, envelope=None):

      if volume < 0 or volume > 127:
         print "Volume (" + str(volume) + ") should range from 0 to 127."
      else:

         if envelope == None:
            self.envelope = Envelope([20],[1.0], 5, 0.8, 15)
         else:
            self.envelope = envelope

         voiceClass = self.Voice   # class to create each voice

         channels = 1

         voiceClassArgs = []
         voiceClassArgs.append(frequency)
         voiceClassArgs.append(volume)
         voiceClassArgs.append(effects)
         voiceClassArgs.append(channels)

         WaveInstrument.__init__(self, channels, voices, volume, voiceClass, *voiceClassArgs)

         self.synthesizer.startSynth()

         # remember that this Instrument has been created and is active (so that it can be stopped by JEM, if desired)
         __ActiveAudioInstruments__.append(self)

   def getEnvelope(self):
      """
      Returns the instruments current envelope.
      """
      return self.envelope

   def setEnvelope(self, envelope):
      """
      Sets a new envelope for this instrument.
      """
      # do we need sanity checking here for valid envelopes?
      self.envelope = envelope


   class Voice(SynthUnit):
      def __init__(self, synth, frequency, volume, effects, channels):
         from com.jsyn.unitgen import SquareOscillator

         SynthUnit.__init__(self, synth, channels)

         amplitude = mapValue( volume, 0, 127, 0.0, 1.0)
         self.amplitude  = amplitude
         self.oscillator = SquareOscillator()
         self.setFrequency(frequency)

         if channels == 1:
            audioPipelineInput = self.inputs[0]
            self.oscillator.output.connect(0, audioPipelineInput, 0)
         elif channels == 2:
            audioPipelineInputLeft  = self.inputs[0]
            audioPipelineInputRight = self.inputs[1]
            self.oscillator.output.connect(0, audioPipelineInputLeft, 0)
            self.oscillator.output.connect(0, audioPipelineInputRight, 0)
         else:
            raise("Can only play mono or stereo samples.")

         self.oscillator.amplitude.set( amplitude )   # preserve max volume of this instrument
         self.setAmplitude(1.0)

         synth.add(self.oscillator)


      def setFrequency(self, frequency):
         """
         Changes the frequency (i.e., pitch) of the specified voice.
         """
         self.oscillator.frequency.set( frequency )

      def getFrequency(self):
         """
         Returns the current frequency of the oscillator as a float.
         """
         return self.oscillator.frequency.get()


class TrianglewaveInstrument(WaveInstrument):
   """
   Encapsulates an oscillating triangle wave. Defaults to a frequency of 440.0 (A4).
   """

   from com.jsyn.unitgen import TriangleOscillator

   def __init__(self, frequency=440.0, volume=127, effects=[], voices=16, envelope=None):

      if volume < 0 or volume > 127:
         print "Volume (" + str(volume) + ") should range from 0 to 127."
      else:
         if envelope == None:
            self.envelope = Envelope([20],[1.0], 5, 0.8, 15)
         else:
            self.envelope = envelope

         voiceClass = self.Voice   # class to create each voice
         channels = 1

         voiceClassArgs = []
         voiceClassArgs.append(frequency)
         voiceClassArgs.append(volume)
         voiceClassArgs.append(effects)
         voiceClassArgs.append(channels)

         WaveInstrument.__init__(self, channels, voices, volume, voiceClass, *voiceClassArgs)

         self.synthesizer.startSynth()

         # remember that this Instrument has been created and is active (so that it can be stopped by JEM, if desired)
         __ActiveAudioInstruments__.append(self)

   def getEnvelope(self):
      """
      Returns the instruments current envelope.
      """
      return self.envelope

   def setEnvelope(self, envelope):
      """
      Sets a new envelope for this instrument.
      """
      # do we need sanity checking here for valid envelopes?
      self.envelope = envelope


   class Voice(SynthUnit):
      def __init__(self, synth, frequency, volume, effects, channels):
         from com.jsyn.unitgen import TriangleOscillator

         SynthUnit.__init__(self, synth, channels)

         amplitude = mapValue( volume, 0, 127, 0.0, 1.0)
         self.amplitude  = amplitude
         self.oscillator = TriangleOscillator()
         self.setFrequency( frequency )


         if channels == 1:
            audioPipelineInput = self.inputs[0]
            self.oscillator.output.connect(0, audioPipelineInput, 0)
         elif channels == 2:
            audioPipelineInputLeft  = self.inputs[0]
            audioPipelineInputRight = self.inputs[1]
            self.oscillator.output.connect(0, audioPipelineInputLeft, 0)
            self.oscillator.output.connect(0, audioPipelineInputRight, 0)
         else:
            raise("Can only play mono or stereo samples.")

         self.oscillator.amplitude.set( amplitude )   # preserve max volume of this instrument
         self.setAmplitude(1.0)

         synth.add(self.oscillator)


      def setFrequency(self, frequency):
         """
         Changes the frequency (i.e., pitch) of the specified voice.
         """
         self.oscillator.frequency.set( frequency )

      def getFrequency(self):
         """
         Returns the current frequency of the oscillator as a float.
         """
         return self.oscillator.frequency.get()


### FM Synthesis Instrument ###

class FMSynthesisInstrument(WaveInstrument):
   """
   Encapsulates a frequency modulated sinewave.
   The frequency of the *carrier* wave, equals centerFrequency/timbreQuality.
   Using a ratio like this preserves the timbre of the instrument you have just
   created.
   """
   def __init__(self, frequency, timbreRatio, volume=127, voices=16, envelope=None):
      """
      Specify the class needed to play the voice, then call the super constructor. Lastly, start the synth.
      """
      from com.jsyn import JSyn

      if volume < 0 or volume > 127:
         print "Volume (" + str(volume) + ") should range from 0 to 127."
      else:

         if envelope == None:
            self.envelope = Envelope([20],[1.0], 5, 0.8, 15)
         else:
            self.envelope = envelope


         voiceClass = self.Voice   # class to create each voice

         channels = 1   # oscillators have one output channel

         voiceClassArgs = []                  # create empty list to hold parameters
         voiceClassArgs.append(frequency)     # append each parameter to the list
         voiceClassArgs.append(timbreRatio)
         voiceClassArgs.append(volume)
         voiceClassArgs.append(channels)

         WaveInstrument.__init__(self, channels, voices, volume, voiceClass, *voiceClassArgs)   # call super constructor

         self.synthesizer.startSynth()

         # add this instrument to the global list for external tracking by JEM
         __ActiveAudioInstruments__.append(self)


   def getEnvelope(self):
      """
      Returns the instruments current envelope.
      """
      return self.envelope


   def setEnvelope(self, envelope):
      """
      Sets a new envelope for this instrument.
      """
      # do we need sanity checking here for valid envelopes?
      self.envelope = envelope


   class Voice(SynthUnit):
      """
      Extending SynthUnit provides access to the amplitude attribute - needed by all players.
      """

      def __init__(self, synth, frequency, timbreRatio, volume, channels):
         """
         This constructor establishes a pattern for instrument creation.
            1. Call the super constructor
            2. Define a `createInstrument` method that does the heavy lifting
            3. add self to synth
         """
         from com.jsyn.unitgen import SineOscillator, Multiply

         # first, let's call superconstructor to create basic circuit (output port, and amplitude control)
         SynthUnit.__init__(self, synth)

         self.timbreRatio = timbreRatio
         # now, create the specific instrument (i.e., build circuitry responsible for this timbre)

         # we now have the necessary self.frequency and self.divisor
         # so we get up the rest of what is needed for FMSynthesis

         self.carrier    = SineOscillator()   # create carrier wave
         self.modulator  = SineOscillator()   # create modulator wave
         self.multiplier = Multiply()         # create multiplier linking carrier and modulator

         self.modulator.output.connect( self.multiplier.inputA )        # connect modulator output to one of multiplier's inputs
         self.multiplier.output.connect( self.carrier.frequency )       # connect multiplier's output to control carrier frequency


         if channels == 1:
            audioPipelineInput = self.inputs[0]
            self.carrier.output.connect(0, audioPipelineInput, 0)
         elif channels == 2:
            audioPipelineInputLeft  = self.inputs[0]
            audioPipelineInputRight = self.inputs[1]
            self.carrier.output.connect(0, audioPipelineInputLeft, 0)
            self.carrier.output.connect(0, audioPipelineInputRight, 0)
         else:
            raise("Can only play mono or stereo samples.")


         amplitude = mapValue( volume, 0, 127, 0.0, 1.0)   # map volume (0-127) to amplitude (0.0-1.0)
         self.carrier.amplitude.set(amplitude)             # set carrier amplitude to control max volume
         #self.inputB.set(amplitude)
         self.modulator.amplitude.set(1.0)                 # keep modulator amplitude at 1.0 to preserve timbre

         # circuit is built, so set it's base frequency
         self.setFrequency(frequency)


         # add all units to synth (including self)
         synth.add( self.carrier )
         synth.add( self.modulator )
         synth.add( self.multiplier )


      def setFrequency(self, frequency):
         self.modulator.frequency.set( frequency / self.timbreRatio )
         #self.carrier.frequency.set( frequency )
         self.multiplier.inputB.set( frequency )

      def getFrequency(self):
         """
         Returns the current frequency of the oscillator as a float.
         """
         return self.multiplier.inputB.get()


class AdditiveInstrument(AudioInstrument):
   """
   Encapualtes an additive synthesis instrument. A list of instruments are provided and
   one voice of each is instantiated. A paralell list of amplitudes corresponds to how much
   that particular intrument affects the sound.

   No middle layer is needed for AdditiveSynthesis. Thus, it extends directly from Instrument.
   """

   def __init__(self, instrumentList, volumesList, volume=127, voices=16):

      channels = 1   # assume one input channels

      voiceClass = self.Voice
      voiceClassArgs = []
      voiceClassArgs.append(volumesList)
      voiceClassArgs.append(channels)
      voiceClassArgs.append(volume)

      AudioInstrument.__init__(self, channels, voices, volume, voiceClass, *voiceClassArgs)

      for instrument in instrumentList:
         for i in range(len(instrument.voices)):
            self.voices[i].initializeVoice( self.synth, instrument.voices[i] )

      self.synthesizer.startSynth()

      __ActiveAudioInstruments__.append(self)


   def stopAll(self):
      """
      Allow each voice to control its own stop all.
      """
      for voice in self.voices:
         voice.stopAll()

   def start(self, voice=0):
      """
      Begin playing the specified voice.
      """

      if voice < 0 or voice >= self.maxVoices:

         print "Voice (" + str(voice) + ") should range from 0 to " + str(self.maxVoices) + "."
         return None

      else:
         self.lineOuts[voice].start()


   def loop(self, voice=0):
      """
      Calls the start() function because oscillators do not require looping.
      """

      self.start(voice)


   def getFrequency(self, frequency, voice=0):
      """
      Returns the frequency of the specified voice. Returns None if invalid voice is given.
      """

      if voice < 0 or voice >= self.maxVoices:

         print "Voice (" + str(voice) + ") should range from 0 to " + str(self.maxVoices) + "."
         return None

      else:
         return self.voicesFrequencies[voice]


   def setFrequency(self, frequency, voice=0):
      """
      Changes the frequency (i.e., pitch) of the specified voice.
      """

      self.voices[voice].setFrequency( frequency )                              # set frequency of this voice
      self.voicesFrequencies[voice] = frequency
      self.voicesPitches[voice] = self.__convertFrequencyToPitch__( frequency ) # also adjust pitch accordingly (since they are coupled)


   def isPlaying(self, voice=0):
      """
      Returns true if voice is playing. Returns None otherwise.
      """

      if voice < 0 or voice >= self.maxVoices:

         print "Voice (" + str(voice) + ") should range from 0 to " + str(self.maxVoices) + "."
         return None

      else:
         return self.voices[voice].playing


   class Voice(SynthUnit):
      def __init__(self, synth, volumesList, channels, volume=127):
         """
         The addititive synthesis voice is a compound voice consisting of one or more
         sub voices. These sub voices are one instance of a voice for each instrument
         in the instrument list.
         """

         self.subVoices = []
         self.volumesList = volumesList   # do something with this later
         self.channels = channels

         SynthUnit.__init__(self, synth)   # intialize the synth unit so we have access to inputA and inputB.



      def initializeVoice(self, synth, subvoice):
         """
         Take in a voice from the and connect it to self.inputA. This should only be
         called once at creation time. Thus, it is safe to append to the components
         list here.
         """
         self.subVoices.append( subvoice )        # append this subvoice to the list of subvoices

         if self.channels == 1:
            audioPipelineInput = self.inputs[0]
            subvoice.outputs[0].connect(0, audioPipelineInput, 0)
         elif self.channels == 2:
            audioPipelineInputLeft  = self.inputs[0]
            audioPipelineInputRight = self.inputs[1]
            subvoice.outputs[0].connect(0, audioPipelineInputLeft, 0)
            subvoice.outputs[1].connect(0, audioPipelineInputRight, 0)
         else:
            raise("Can only play mono or stereo samples.")

      def setFrequency(self, frequency):
         """
         Loop through each component voice and change its frequency to the
         desired frequency of the composite voice.
         """

         for subvoice in self.subVoices:
            subvoice.setFrequency( frequency )

      def stopAll(self):
         """
         Stops all sub voices.
         """
         for subvoice in self.subVoices:
            subvoice.stop()



######################################################################################
# If running inside JEM, register function that stops everything, when the Stop button
# is pressed inside JEM.
######################################################################################

# function to stop and clean-up all active AudioSamples
def __stopActiveAudioInstruments__():

   global __ActiveAudioInstruments__

   # first, stop them
   for a in __ActiveAudioInstruments__:
      a.stopAll()         # no need to check if they are playing - just do it (it's fine)

   Synthesizer.stopSynth()

   # also empty list, so things can be garbage collected
   __ActiveAudioInstruments__ = []   # remove access to deleted items

# now, register function with JEM (if possible)
try:

    # if we are inside JEM, registerStopFunction() will be available
    registerStopFunction(__stopActiveAudioInstruments__)   # tell JEM which function to call when the Stop button is pressed

except:  # otherwise (if we get an error), we are NOT inside JEM

    pass    # so, do nothing.




# used to keep track which MidiSequence objects are active, so we can stop them when
# JEM's Stop button is pressed
__ActiveMidiSequences__ = []     # holds active MidiSequence objects

##### MidiSequence class ######################################

class MidiSequence():
   """Encapsulates a midi sequence object created from the provided material, which is either a string
      - the filename of a MIDI file (.mid), or music library object (Score, Part, Phrase, or Note).
      The midi sequence has a default MIDI pitch (e.g., A4) and volume.  The sequence can be played once, looped,
      and stopped.  Also, we may change its pitch, tempo, and volume.  These changes happen immediately.
   """

   def __init__(self, material, pitch=A4, volume=127):

      # determine what type of material we have
      if type(material) == type(""):   # a string?

         self.filename = material                # assume it's an external MIDI filename

         # load and create the MIDI sample
         self.score = Score()                    # create an empty score
         Read.midi(self.score, self.filename)    # load the external MIDI file

      else:  # determine what type of material we have

         # and do necessary datatype wrapping (MidiSynth() expects a Score)
         if type(material) == Note:
            material = Phrase(material)
         if type(material) == Phrase:   # no elif - we need to successively wrap from Note to Score
            material = Part(material)
         if type(material) == jPhrase:  # (also wrap jMusic default Phrases, in addition to our own)
            material = Part(material)
         if type(material) == Part:     # no elif - we need to successively wrap from Note to Score
            material = Score(material)

         if type(material) == Score:

            self.score = material     # and remember it

         else:   # error check
            raise TypeError("Midi() - Unrecognized type", type(material), "- expected filename (string), Note, Phrase, Part, or Score.")

      # now, self.score contains a Score object

      # create Midi sequencer to playback this sample
      self.midiSynth = self.__initMidiSynth__()

      # get access to the MidiSynth's internal components (neededd for some of our operations)
      self.sequencer = self.midiSynth.getSequencer()
      self.synthesizer = self.midiSynth.getSynthesizer()

      # set tempo factor
      self.tempoFactor = 1.0   # scales whatever tempo is set for the sequence (1.0 means no change)

      self.defaultTempo = self.score.getTempo()   # remember default tempo
      self.playbackTempo = self.defaultTempo      # set playback tempo to default tempo

      # set volume
      self.volume = volume           # holds volume (0-127)
      #self.setVolume( self.volume )  # set desired volume

      # set MIDI score's default pitch
      self.pitch = pitch                         # remember provided pitch

      # remember that this MidiSequence has been created and is active (so that it can be stopped by JEM, if desired)
      __ActiveMidiSequences__.append(self)


   def __initMidiSynth__(self):
      """Creates and initializes a MidiSynth object."""

      # NOTE: Since we need access to the "guts" of the MidiSynth object, it is important to initialize it.
      #       This happens automatically the first time we play something through it, so let's play an empty score.
      midiSynth = MidiSynth()   # create it
      midiSynth.play( Score() ) # and initialize it
      return midiSynth


   def play(self):
      """Play the MIDI score."""

      # make sure only one play is active at a time
      if self.midiSynth.isPlaying():     # is another play is on?
         self.stop()                        # yes, so stop it

      #self.sequencer.setLoopCount(0)     # set to no repetition (needed, in case we are called after loop())
      self.midiSynth.setCycle(False)     # turn off looping (just in case)
      self.midiSynth.play( self.score )  # play it!

   def loop(self):
      """Repeat the score indefinitely."""

      # make sure only one play is active at a time
      if self.midiSynth.isPlaying():     # is another play is on?
         self.stop()                        # yes, so stop it

      # Due to an apparent Java Sequencer bug in setting tempo, we can only loop indefinitely (not a specified
      # number of times).  Looping a specified number of times causes the second iteration to playback at 120 BPM.
      #self.sequencer.setLoopCount(times)  # set the number of times to repeat the sequence
      self.midiSynth.setCycle(True)
      self.midiSynth.play( self.score )   # play it!

   def isPlaying(self):
      """
      Returns True if the sequence is still playing.
      """
      return self.midiSynth.isPlaying()

   def stop(self):
      """Stop the MIDI score play."""

      self.midiSynth.stop()

   def pause(self):
      """Pause the MIDI sequence play."""
      self.__setTempoFactor__(0.00000000000000000000000000000000000000000001) # slow play down to (almost) a standstill

   def resume(self):
      """
      Resume playing the sample (from the paused position).
      """
      self.__setTempoFactor__(1.0) # reset playback to original tempo (i.e., resume)

   # low-level helper function
   def __setTempoFactor__(self, factor = 1.0):
      """
      Set MIDI sequence's tempo factor (1.0 means default, i.e., no change).
      """
      self.sequencer.setTempoFactor( factor )


   def setPitch(self, pitch):
      """Set the MidiSequence's playback pitch (by transposing the MIDI material)."""

      semitones = pitch - self.pitch          # get the pitch change in semitones
      Mod.transpose( self.score, semitones )  # update score pitch appropriately

      # do some low-level work inside MidiSynth
      updatedSequence = self.midiSynth.scoreToSeq( self.score )  # get new Midi sequence from updated score
      self.positionInMicroseconds = self.sequencer.getMicrosecondPosition()  # remember where to resume
      self.sequencer.setSequence(updatedSequence)                # update the sequence - this restarts playing...
      self.sequencer.setMicrosecondPosition( self.positionInMicroseconds )   # ...so reset playing to where we left off
      self.sequencer.setTempoInBPM( self.playbackTempo )         # set tempo (needed for the first (partial) iteration)

      # finally, remember new pitch
      self.pitch = pitch

   def getPitch(self):
      """Returns the MIDI score's pitch."""

      return self.pitch

   def getDefaultPitch(self):
      """Return the MidiSequence's default pitch."""

      return self.defaultPitch


   def setTempo(self, beatsPerMinute):
      """
      Set MIDI sequence's playback tempo.
      """
      # Due to an apparent Java Sequencer bug in setting tempo, when looping a specified number of times causes
      # all but the first iteration to playback at 120 BPM, regardless of what the current tempo may be.
      # Unable to solve the problem in the general case, below is an attempt to fix it for some cases (e.g.,
      # for looping continuously, but not for looping a specified number of times).
      self.playbackTempo = beatsPerMinute               # keep track of new playback tempo
      self.sequencer.setTempoInBPM( beatsPerMinute )    # and set it
      self.midiSynth.setTempo( beatsPerMinute )         # and set it again (this seems redundant, but see above)
      self.score.setTempo( beatsPerMinute )             # and set it again (this seems redundant, but see above)

   def getTempo(self):
      """
      Return MIDI sequence's playback tempo.
      """
      return self.playbackTempo

   def getDefaultTempo(self):
      """
      Return MIDI sequence's default tempo (in beats per minute).
      """
      return self.defaultTempo


   def setVolume(self, volume):
      """Sets the volume for the MidiSequence (volume ranges from 0 - 127)."""

      self.volume = volume    # remember new volume

      # NOTE:  Setting volume through a MidiSynth is problematic.
      #        Here we use a solution by Howard Amos (posted 8/16/2012) in
      #        http://www.coderanch.com/t/272584/java/java/MIDI-volume-control-difficulties
      volumeMessage = ShortMessage()    # create a MIDI message
      #receiver = self.sequencer.getTransmitters().iterator().next().getReceiver()  # get the MidiSynth receiver
      receiver = self.sequencer.getTransmitters()[0].getReceiver()  # get the MidiSynth receiver

      for channel in range(16):   # change volume of all the MIDI channels
         volumeMessage.setMessage(0xB0 + channel, 7, volume)   # set coarse volume control for this channel
         receiver.send (volumeMessage, -1)                     # and communicate it to the receiver

   def getVolume(self):
      """Returns the volume for the MidiSequence (volume ranges from 0 - 127)."""

      return self.volume


######################################################################################
# If running inside JEM, register function that stops everything, when the Stop button
# is pressed inside JEM.
######################################################################################

# function to stop and clean-up all active MidiSequences
def __stopActiveMidiSequences__():

   global __ActiveMidiSequences__

   # first, stop them
   for m in __ActiveMidiSequences__:
      m.stop()    # no need to check if they are playing - just do it (it's fine)

   # then, delete them
   for m in __ActiveMidiSequences__:
      del m

   # also empty list, so things can be garbage collected
   __ActiveMidiSequences__ = []   # remove access to deleted items

# now, register function with JEM (if possible)
try:

    # if we are inside JEM, registerStopFunction() will be available
    registerStopFunction(__stopActiveMidiSequences__)   # tell JEM which function to call when the Stop button is pressed

except:  # otherwise (if we get an error), we are NOT inside JEM

    pass    # so, do nothing.



# used to keep track which Metronome objects are active, so we can stop them when
# JEM's Stop button is pressed
__ActiveMetronomes__ = []     # holds active MidiSequence objects

##### Metronome class ######################################

from timer import Timer
#from gui import Display     # for Metronome tick visualization

class Metronome():
   """Creates a metronome object used in scheduling and synchronizing function call (intended for starting blocks of musical
      material together, but could be really used for anything (e.g., GUI animzation).  This is based on the Timer class,
      but is higher-level, based on tempo (e.g., 60 BPM), and time signatures (e.g., 4/4).
   """

   #def __init__(self, tempo=60, timeSignature=[4, 4], displaySize=50, displayTickColor=Color.RED):
   def __init__(self, tempo=60, timeSignature=[4, 4]):

      # remember title, tempo and time signature
      self.tempo = tempo
      self.timeSignature = timeSignature  # a list (first item is numerator, second is denominator)

      # list of functions (we are asked to synchronize) and their information (parallel lists)
      self.functions        = []    # functions to call
      self.parameters       = []    # their corresponding parameters
      self.desiredBeats     = []    # on which beat to call them (0 means now)
      self.repeatFlags      = []    # if they are meant to be called repeatedly
      self.beatCountdowns   = []    # holds beat countdown until call

      # create timer, upon which to base our operation
      delay = int((60.0 / self.tempo) * 1000)   # in milliseconds
      self.timer = Timer2(delay, self.__callFunctions__, [], True)

      # set up metronome visualization
#      self.display = Display("Metronome", displaySize, displaySize+20, 0, 0)
#      self.display.hide()      # initially hidden
#
#      # set up display ticking
#      self.displayTickColor = displayTickColor               # color used for ticking
#      self.displayOriginalColor = self.display.getColor()    # color to reset ticking
#      self.flickerTimer = Timer2(100, self.display.setColor, [self.displayOriginalColor])   # create timer to reset display color (it ends fliker)
#      self.add( self.__updateDisplay__, [], 0, True, 1)      # schedule display flickering on every beat (starts flicker)

      # set up metronome visualization / sonification
      self.currentBeat   = 1       # holds current beat relative to provided time signature (1 means first beat)
      self.visualize     = False   # True means print out current beat on console; False do not print
      self.sonify        = False   # True means sound each tick; False do not
      self.sonifyPitch   = HI_MID_TOM   # which pitch to play whe ticking
      self.sonifyChannel = 9       # which channel to use (9 is for percussion)
      self.sonifyVolume  = 127     # how loud is strong beat (secondary beats will at 70%)

      # remember that this MidiSequence has been created and is active (so that it can be stopped by JEM, if desired)
      __ActiveMetronomes__.append(self)


   def add(self, function, parameters=[], desiredBeat=0, repeatFlag=False):
      """It schedules the provided function to be called by the metronome (passing the provided parameters to it) on the
         desired beat (0 means right away, 1 means first (strong) beat, 2 means second beat, etc.), and whether to keep
         calling in it every time the desired beat comes around.
      """
      self.functions.append( function )
      self.parameters.append( parameters )
      self.desiredBeats.append( desiredBeat )
      self.repeatFlags.append( repeatFlag )

      # calculate beat countdown
      beatCountdown = self.__calculateBeatCountdown__( desiredBeat )

      # store beat countdown for this function
      self.beatCountdowns.append( beatCountdown )

   def remove(self, function):
      """It removes the provided function from the list of functions scheduled (via add) to be called by the metronome.
         If several instances of this function have been scheduled, it removes the earliest one (i.e., several calls of this
         will be needed to remove all scheduled instances - a design choice).  If the function is not scheduled, it throws
         an error.
      """
      index = self.functions.index( function )   # find index of leftmost occurrence
      self.functions.pop( index )                # and remove it and all info
      self.parameters.pop( index )
      self.desiredBeats.pop( index )
      self.repeatFlags.pop( index )
      self.beatCountdowns.pop( index )

   def removeAll(self):
      """It removes all provided functions to be called by the metronome."""

      # reinitialize all function related information
      self.functions        = []
      self.parameters       = []
      self.desiredBeats     = []
      self.repeatFlags      = []
      self.beatCountdowns   = []

   def setTempo(self, tempo):
      """It sets the metronome's tempo."""

      self.tempo = tempo        # remember new tempo

      # and set it
      delay = int((60.0 / self.tempo) * 1000)   # in milliseconds
      self.timer.setDelay(delay)

   def getTempo(self):
      """It returns the metronome's tempo."""
      return self.tempo

   def setTimeSignature(self, timeSignature):
      """It sets the metronome's time signature."""
      self.timeSignature = timeSignature        # remember new time signature
      self.currentBeat = 0                      # reinitialize current beat relative to provided time signature (1 means first beat)

   def getTimeSignature(self):
      """It returns the metronome's time signature."""
      return self.timeSignature

   def start(self):
      """It starts the metronome."""
      self.timer.start()
      print "Metronome started..."

   def stop(self):
      """It starts the metronome."""
      self.timer.stop()
      print "Metronome stopped."

#   def __updateDisplay__(self):
#      """It temporarily flickers the metronome's visualization display to indicate a 'tick'."""
#
#      # change color to indicate a tick
#      self.display.setColor( self.displayTickColor )
#
#      # reset display back to original color after a small delay
#      #flikcerTimer = Timer2(250, self.display.setColor, [self.displayOriginalColor])
#      #flikcerTimer.start()    # after completion, this timer will eventually be garbage collected (no need to reuse)
#      self.flickerTimer.start()

#   def __advanceCurrentBeat__(self):
#      """It advances the current metronome beat."""
#
#      if self.visualize:   # do we need to print out current beat?
#         print self.currentBeat
#
#      if self.sonify:   # do we need to sound out current beat?
#         if self.currentBeat == 1:    # strong (first) beat?
#            Play.note(self.sonifyPitch, 0, 200, self.sonifyVolume, self.sonifyChannel)   # louder
#         else:
#            Play.note(self.sonifyPitch, 0, 200, int(self.sonifyVolume * 0.7), self.sonifyChannel)   # softer
#
#      self.currentBeat = (self.currentBeat % self.timeSignature[0]) + 1  # wrap around as needed


   def __callFunctions__(self):
      """Calls all functions we are asked to synchronize."""

      # do visualization / sonification tasks (if any)
      if self.visualize:   # do we need to print out current beat?
         print self.currentBeat

      if self.sonify:   # do we need to sound out current beat?
         if self.currentBeat == 1:    # strong (first) beat?
            Play.note(self.sonifyPitch, 0, 200, self.sonifyVolume, self.sonifyChannel)   # louder
         else:
            Play.note(self.sonifyPitch, 0, 200, int(self.sonifyVolume * 0.7), self.sonifyChannel)   # softer

      #***
      #print "self.desiredBeats, self.beatCountdowns = ",
      #print self.desiredBeats, self.beatCountdowns

      # NOTE:  The following uses several for loops so that all functions are given quick service.
      #        Once they've been called, we can loop again to do necessary book-keeping...

      # first, iterate to call all functions with their (provided) parameters
      nonRepeatedFunctions = []   # holds indices of functions to be called only once (so we can remove them later)
      for i in range( len(self.functions) ):

        # see if current function needs to be called right away
        if self.beatCountdowns[i] == 0:

           # yes, so call this function!!!
           self.functions[i]( *(self.parameters[i]) )   # strange syntax, but does the trick...

           # check if function was meant to be called only once, and if so remove from future consideration
           if not self.repeatFlags[i]:  # call only once?

              nonRepeatedFunctions.append( i )   # mark it for deletion (so it is not called again)

      # now, all functions who needed to be called have been called

      # next, iterate to remove any functions that were meant to be called once
      # NOTE: We remove functions right-to-left - see use of reversed().  This way, as lists shrink,
      #       earlier indices are still valid for other items to be removed (if any)!!!
      for i in reversed(nonRepeatedFunctions):
         self.functions.pop( i )
         self.parameters.pop( i )
         self.desiredBeats.pop( i )
         self.repeatFlags.pop( i )
         self.beatCountdowns.pop( i )


      ###########################################################################################
      # NOTE:  This belongs exactly here (before updating countdown timers below)

      # advance to next beat (in anticipation...)
      self.currentBeat = (self.currentBeat % self.timeSignature[0]) + 1  # wrap around as needed

      ###########################################################################################

      # finally, iterate to update countdown timers for all remaining functions
      for i in range( len(self.functions) ):

        # if this function was just called
        if self.beatCountdowns[i] == 0:

           # reinitialize its beat countdown counter, i.e., reschedule it for its next call

           # calculate beat countdown
           self.beatCountdowns[i] = self.__calculateBeatCountdown__( self.desiredBeats[i] )

        else:   # it's not time to call this function, so update its information

           # reduce ticks remaining to call it
           self.beatCountdowns[i] = self.beatCountdowns[i] - 1     # we are now one tick closer to calling it

      # now, all functions who needed to be called have been called, and all beat countdowns
      # have been updated.


   def __calculateBeatCountdown__(self, desiredBeat):
      """Calculates the beat countdown given the desired beat."""

#      if desiredBeat == 0:  # do they want now (regardess of current beat)?
#         beatCountdown = 0     # give them now
#      elif desiredBeat >= self.currentBeat:  # otherwise, is desired beat now or in the future?
#         beatCountdown = desiredBeat - self.currentBeat  # calculate remaining beats until then
#      else:  # desired beat has passed in the time signature, so we need to pick it up in the next measure
#         beatCountdown = (desiredBeat + self.timeSignature[0]) - self.currentBeat

      if desiredBeat == 0:  # do they want now (regardess of current beat)?
         beatCountdown = 0     # give them now
      elif self.currentBeat <= desiredBeat <= self.timeSignature[0]:  # otherwise, is desired beat the remaining measure?
         beatCountdown = desiredBeat - self.currentBeat                            # calculate remaining beats until then
      elif 1 <= desiredBeat < self.currentBeat:                       # otherwise, is desired beat passed in this measure?
         beatCountdown = (desiredBeat + self.timeSignature[0]) - self.currentBeat  # pick it up in the next measure
      elif self.timeSignature[0] < desiredBeat:                       # otherwise, is desired beat beyond this measure?
         beatCountdown = desiredBeat - self.currentBeat + self.timeSignature[0]    # calculate remaining beats until then
      else:  # we cannot handle negative beats
         raise ValueError("Cannot handle negative beats, " + str(desiredBeat) + ".")

      # ***
      #print "beatCountdown =", beatCountdown
      return beatCountdown


   def show(self):
      """It shows the metronome visualization display."""
      #self.display.show()
      self.visualize = True

   def hide(self):
      """It shows the metronome visualization display."""
      #self.display.hide()
      self.visualize = False

   def soundOn(self, pitch=ACOUSTIC_BASS_DRUM, volume=127, channel=9):
      """It turns the metronome sound on."""
      self.sonify = True
      self.sonifyPitch   = pitch   # which pitch to play whe ticking
      self.sonifyChannel = channel # which channel to use (9 is for percussion)
      self.sonifyVolume  = volume  # how loud is strong beat (secondary beats will at 70%)

   def soundOff(self):
      """It turns the metronome sound off."""
      self.sonify = False




#
#####################################################################################
# If running inside JEM, register function that stops everything, when the Stop button
# is pressed inside JEM.
######################################################################################

# function to stop and clean-up all active MidiSequences
def __stopActiveMetronomes__():

   global __ActiveMetronomes__

   # first, stop them
   for m in __ActiveMetronomes__:
      m.stop()    # no need to check if they are playing - just do it (it's fine)

   # then, delete them
   for m in __ActiveMetronomes__:
      del m

   # also empty list, so things can be garbage collected
   __ActiveMetronomes__ = []   # remove access to deleted items

# now, register function with JEM (if possible)
try:

    # if we are inside JEM, registerStopFunction() will be available
    registerStopFunction(__stopActiveMetronomes__)   # tell JEM which function to call when the Stop button is pressed

except:  # otherwise (if we get an error), we are NOT inside JEM

    pass    # so, do nothing.



######################################################################################
# synthesized jMusic instruments (also see http://jmusic.ci.qut.edu.au/Instruments.html)

#import AMInst
#import AMNoiseInst
#import AddInst
#import AddMorphInst
#import AddSynthInst
#import BandPassFilterInst
#import BowedPluckInst
#import BreathyFluteInst
#import ChiffInst
#import ControlledHPFInst
#import DynamicFilterInst
#import FGTRInst
#import FMNoiseInst
#import FractalInst
#import GranularInst
#import GranularInstRT
#import HarmonicsInst
#import LFOFilteredSquareInst
#import LPFilterEnvInst
#import NoiseCombInst
#import NoiseInst
#import OddEvenInst
#import OvertoneInst
#import PluckInst
#import PluckSampleInst
#import PrintSineInst
#import PulseFifthsInst
#import PulsewaveInst
#import RTPluckInst
#import RTSimpleFMInst
#import ResSawInst
#import ReverseResampledInst
#import RingModulationInst
#import SabersawInst
#import SawCombInst
#import SawHPFInst
#import SawLPFInst
#import SawLPFInstB
#import SawLPFInstE
#import SawLPFInstF
#import SawLPFInstG
#import SawLPFInstRT
#import SawtoothInst
#import Sawtooth_LPF_Env_Inst
#import SimpleAMInst
#import SimpleAllPassInst
#import SimpleFMInst
#import SimpleFMInstRT
#import SimplePluckInst
#import SimpleReverbInst
#import SimpleSampleInst
#import SimpleSineInst
#import SimpleTremoloInst
#import SimplestInst
#import SineInst
#import SlowSineInst
#import SquareBackwardsInst
#import SquareCombInst
#import SquareInst
#import SquareLPFInst
#import SubtractiveSampleInst
#import SubtractiveSynthInst
#import SuperSawInst
#import TextInst
#import TimpaniInst
#import TremoloInst
#import TriangleInst
#import TriangleRepeatInst
#import VaryDecaySineInst
#import VibesInst
#import VibratoInst
#import VibratoInstRT

# preserve Jython bindings that get ovwerwritten by the following Java imports - a hack!
# (also see very top of this file)
enumerate = enumerate_preserve


print
print
