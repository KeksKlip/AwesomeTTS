# -*- coding: utf-8 -*-


#import awesometts.config as config

from PyQt4 import QtGui,QtCore

#Supported Languages       
# code , Language, windows charset encoding
slanguages = [['af', 'Afrikaans', 'cp1252'], #or iso-8859-1
['sq', 'Albanian',	'cp1250'], #or iso 8859-16
['ar', 'Arabic',	'cp1256'], #or iso-8859-6
['hy', 'Armenian',	'armscii-8'],
['ca', 'Catalan',	'cp1252'], #or iso-8859-1
['zh', 'Chinese',	'cp936'],
['hr', 'Croatian',	'cp1250'], #or iso-8859-2
['cs', 'Czech',		'cp1250'], #or iso-8859-2
['da', 'Danish',	'cp1252'], #or iso-8859-1
['nl', 'Dutch',		'cp1252'], #or iso-8859-1
['en', 'English',	'cp1252'], #or iso-8859-1
['fi', 'Finnish',	'cp1252'], #or iso-8859-1
['fr', 'French',	'cp1252'], #or iso-8859-1
['de', 'German',	'cp1252'], #or iso-8859-1
['el', 'Greek',		'cp1253'], #or iso-8859-7
['ht', 'Haitian Creole','cp1252'], #or iso-8859-1
['hi', 'Hindi',		'cp1252'], #or iso-8859-1
['hu', 'Hungarian',	'cp1250'], #or iso-8859-2
['is', 'Icelandic',	'cp1252'], #or iso-8859-1
['id', 'Indonesian'],
['it', 'Italian',	'cp1252'], #or iso-8859-1
['ja', 'Japanese',	'cp932'], #or shift_jis, iso-2022-jp, euc-jp
['ko', 'Korean',	'cp949'], #or euc-kr
['la', 'Latin'],
['lv', 'Latvian',	'cp1257'], #or iso-8859-13
['mk', 'Macedonian',	'cp1251'], #iso-8859-5
['no', 'Norwegian',	'cp1252'], #or iso-8859-1
['pl', 'Polish',	'cp1250'], #or iso-8859-2
['pt', 'Portuguese',	'cp1252'], #or iso-8859-1
['ro', 'Romanian',	'cp1250'], #or iso-8859-2
['ru', 'Russian',	'cp1251'], #or koi8-r, iso-8859-5
['sr', 'Serbian',	'cp1250'], # cp1250 for latin, cp1251 for cyrillic
['sk', 'Slovak',	'cp1250'], #or iso-8859-2
['es', 'Spanish',	'cp1252'], #or iso-8859-1
['sw', 'Swahili',	'cp1252'], #or iso-8859-1
['sv', 'Swedish',	'cp1252'], #or iso-8859-1
['tr', 'Turkish',	'cp1254'], #or iso-8859-9
['vi', 'Vietnamese',	'cp1258'],
['cy', 'Welsh',		'iso-8859-14']]

TTS_ADDRESS = 'http://translate.google.com/translate_tts'


import re, subprocess
from anki.utils import stripHTML
from urllib import quote_plus
import awesometts.config as config
import awesometts.util as util
from subprocess import Popen, PIPE, STDOUT


def playGoogleTTS(text, language):
	text = re.sub("\[sound:.*?\]", "", stripHTML(text.replace("\n", "")).encode('utf-8'))
	address = TTS_ADDRESS+'?tl='+language+'&q='+ quote_plus(text)

	if subprocess.mswindows:
		param = ['mplayer.exe', '-ao', 'win32', '-slave', '-user-agent', "'Mozilla/5.0'", address]
		if config.subprocessing:
			subprocess.Popen(param, startupinfo=util.si, stdin=PIPE, stdout=PIPE, stderr=STDOUT)
		else:
			subprocess.Popen(param, startupinfo=util.si, stdin=PIPE, stdout=PIPE, stderr=STDOUT).communicate()
	else:
		param = ['mplayer', '-slave', '-user-agent', "'Mozilla/5.0'", address]
		if config.subprocessing:
			subprocess.Popen(param, stdin=PIPE, stdout=PIPE, stderr=STDOUT)
		else:
			subprocess.Popen(param, stdin=PIPE, stdout=PIPE, stderr=STDOUT).communicate()

def playfromtagGoogleTTS(fromtag):
	for item in fromtag:
		match = re.match("(.*?):(.*)", item, re.M|re.I)
		playGoogleTTS(match.group(2), match.group(1))

def recordGoogleTTS(speaklist, param):
	print speaklist, param

def get_language_id(language_code):
	x = 0
	for d in slanguages:
		if d[0]==language_code:
			return x
		x = x + 1


def TTS_record_old(text, language):
	text = re.sub("\[sound:.*?\]", "", stripHTML(text.replace("\n", "")).encode('utf-8'))
	address = TTS_ADDRESS+'?tl='+language+'&q='+ quote_plus(text)
	
	file = util.generateFileName(text, 'g', slanguages[get_language_id(language)][2])
	if subprocess.mswindows:
		subprocess.Popen(['mplayer.exe', '-ao', 'win32', '-slave', '-user-agent', "'Mozilla/5.0'", address, '-dumpstream', '-dumpfile', file], startupinfo=util.si, stdin=PIPE, stdout=PIPE, stderr=STDOUT).wait()
		if not config.quote_mp3:
			return file.decode(slanguages[get_language_id(language)][2])
	else:
		subprocess.Popen(['mplayer', '-slave', '-user-agent', "'Mozilla/5.0'", address, '-dumpstream', '-dumpfile', file], stdin=PIPE, stdout=PIPE, stderr=STDOUT).wait()
	return file.decode('utf-8')

def filegenerator_layout(form):
	verticalLayout = QtGui.QVBoxLayout()
	textEditlabel = QtGui.QLabel()
	textEditlabel.setText("Language:")
	form.comboBoxGoogle = QtGui.QComboBox()
	form.comboBoxGoogle.addItems([d[1] for d in slanguages])

	verticalLayout.addWidget(textEditlabel)
	verticalLayout.addWidget(form.comboBoxGoogle)
	return verticalLayout

def filegenerator_run(form):
	return TTS_record_old(unicode(form.texttoTTS.toPlainText()), slanguages[form.comboBoxGoogle.currentIndex()][0])

def filegenerator_preview(form):
	return playGoogleTTS(unicode(form.texttoTTS.toPlainText()), slanguages[form.comboBoxGoogle.currentIndex()][0])


TTS_service = {'g' : {
'name': 'Google',
'play' : playGoogleTTS,
'playfromtag' : playfromtagGoogleTTS,
'record' : recordGoogleTTS,
'filegenerator_layout': filegenerator_layout,
'filegenerator_preview': filegenerator_preview,
'filegenerator_run': filegenerator_run}}



