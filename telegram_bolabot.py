# -*- coding: utf-8 -*-
import telebot
import random

DEBUG = True
IGNORE_CHANNEL = False

APIKey = #Coloque APIKey aqui

bot = telebot.TeleBot(APIKey)

#Mensagens que começam com alguma dessas strings serão consideradas comandos
command_strings = '!', '/', '.'

def print_debug(string):
	if DEBUG:
		print string
		
def obv(msg):
    if random.randint(1,4) == 1:
        msg += ', obviamente'
    return msg + '.'
		
@bot.message_handler(content_types=['text'])
def echo_all(message):
	print_debug("%s: %s" % (message.from_user.username, message.text))
	
	#Pra não ficar floodando o canal enquanto estivermos testando
	if (message.chat.type != "private") and IGNORE_CHANNEL:
		return

	command = None
	texto = message.text
	for string in command_strings:
		if message.text.startswith(string):
			command = message.text[len(string):].split()[0]
			texto = ' '.join(message.text.split()[1:])
			break
			
	print_debug("CMD: %s: %s\n" % (command, texto))

	if command == "alt":
		if ':' not in texto:
			msg = texto.strip('?')
		else:
			msg = texto.split(':')[-1].strip().strip('?')
		alternativas = msg.split(' ou ')
		if len(alternativas) > 1:
			bot.send_message(message.chat.id, obv(random.choice(alternativas).capitalize()))
	
	if command == "bola" or texto.startswith('@' + bot.get_me().username):
		bot.send_message(message.chat.id, obv(random.choice(("Sim", "Não"))))
	
		

bot.skip_pending = True
bot.polling()