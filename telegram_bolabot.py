# -*- coding: utf-8 -*-

import telebot
import random
import argparse
import subprocess
import sys
import os

parser = argparse.ArgumentParser()
parser.add_argument("--key", help="AUTH Key do telegram bot")
parser.add_argument("-v", "--verbose", action="store_true", help="Mostra mais informação na tela")
parser.add_argument("-p", "--private_only", action="store_true", help="Considera apenas mensagens enviadas em conversa privada")

args = parser.parse_args()

def print_verbose(string):
	if args.verbose:
		print string
		
def obv(msg):
    if random.randint(1,4) == 1:
        msg += ', obviamente'
    return msg + '.'
	

configs = {}
if not os.path.isfile("config.ini"):
	print "Criando config.ini inicial"
	f = open("config_template.txt")
	template_data = f.read()
	f.close()
	
	f = open("config.ini", 'w')
	f.write(template_data)
	f.close()

f = open("config.ini")
for line in f.readlines():
	line = line.strip()
	print "linha: %s" % line
	if line and (not line.startswith('#')):
		config_key = line.split('=')[0]
		config_value = line.split('=')[1].split(',')
		configs[config_key] = config_value
f.close()

print_verbose("Configs: %s" % (str(configs)))

if args.key:
	configs["key"] = [args.key]

if configs["key"] == ['']:
	print "AUTH key não encontrada, por favor insira no config.ini ou por via do comando --key"
	sys.exit(1)

bot = telebot.TeleBot(configs["key"][0])

updating = False #Flag pra quando for updatear
		
@bot.message_handler(content_types=['text'])
def handle_messages(message):
	global updating
	
	#Provavelmente redundante por causa do bot.stop_polling(), mas só pra ter certeza
	if updating:
		return 
	
	#Pra não ficar floodando o canal enquanto estivermos testando
	if (message.chat.type != "private") and args.private_only:
		return

	print_verbose("%s: %s" % (message.from_user.username, message.text))
	command = None
	texto = message.text
	for string in configs["command_strings"]:
		if message.text.startswith(string):
			command = message.text[len(string):].split()[0]
			texto = ' '.join(message.text.split()[1:])
			break
			
	print_verbose("CMD: %s: %s\n" % (command, texto))
	
	admin_rights = message.from_user.username in configs["admins"]
	
	if command == "alt":
		if ':' not in texto:
			msg = texto.strip('?')
		else:
			msg = texto.split(':')[-1].strip().strip('?')
		alternativas = msg.split(' ou ')
		if len(alternativas) > 1:
			bot.send_message(message.chat.id, obv(random.choice(alternativas).capitalize()))
	
	if texto.startswith('@' + bot.get_me().username):
		command = texto.split()
		command = command[1].strip()
		if command == "update" and admin_rights:
			bot.send_message(message.chat.id, "Fazendo update!")
			subprocess.call("git pull origin master", shell = True)
			updating = True
			bot.stop_polling()
		else:
			bot.send_message(message.chat.id, obv(random.choice(("Sim", "Não"))))
		
	if command == "bola":
		bot.send_message(message.chat.id, obv(random.choice(("Sim", "Não"))))
	
	if command == "user" and message.chat.type != "private" and configs["users"] != ['']:
		bot.send_message(message.chat.id, obv(random.choice(configs["users"])))


bot.skip_pending = True
print_verbose("Iniciando: %s" % sys.argv)
bot.polling()

if updating:
	print "Atualizando..."
	subprocess.Popen(["python"] + sys.argv)
