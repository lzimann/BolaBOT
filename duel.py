# -*- coding: utf-8 -*-
import random
from telebot import types

class Duelo:
	
	state = "WAITING_ACCEPT"
	last_callback = -1
	
	def send_buttons(self, buttons_strings, text):
		self.last_callback += 1
	
		markup = types.InlineKeyboardMarkup()
		buttons = []
		for bstring in buttons_strings:
			button = types.InlineKeyboardButton(text = bstring, callback_data = "DUEL:%s:%s" % (bstring, self.last_callback))
			buttons.append(button)
		markup.row(*buttons)
		
		self.bot.send_message(self.chat_id, text, reply_markup=markup)
	
	def __init__(self, bot, message, player2_request = None):
		self.players = [None, message.from_user.username, None]
		self.player2_request = player2_request
		self.bot = bot
		self.chat_id = message.chat.id
		
		if player2_request:
			self.player2_request = player2_request.strip('@')
			self.send_buttons(("Aceitar!",), "@%s chamou @%s pra TR3T@!" % (self.players[1], player2_request))
		else:	
			self.send_buttons(("Aceitar!",), "@%s chamou qualquer um pra TR3T@!" % (self.players[1]))
			
	def handle_message(self, message = None, callback_answer = None):
	
		if message:
			texto = ' '.join(message.text.strip().split()[1:]) #texto da mensagem sem o comando .duel/.d
			
			if texto == "cancel" and self.state == "WAITING_ACCEPT" and message.from_user.username == self.players[1]:
				self.bot.send_message(self.chat_id, "TR3T@ cancelada.")
				return "ENDGAME"
				
		if callback_answer:
			if int(callback_answer.data.split(':')[-1]) >= self.last_callback:
				data = callback_answer.data.split(':')[1]
				
				if self.state == "WAITING_ACCEPT" and data == "Aceitar!" and (callback_answer.from_user.username != self.players[1]):
					self.player_accepted(callback_answer.from_user.username)
					
				if self.state == "ATAQUE" and (data in ("Esquerda", "Meio", "Direita")) and (callback_answer.from_user.username == self.players[self.current_player]):
					self.direcao_ataque = data
					self.state = "DEFESA"
					self.play()
					
				elif self.state == "DEFESA" and (data in ("Esquerda", "Meio", "Direita")) and (callback_answer.from_user.username == self.players[self.current_player * -1]):
					if data == self.direcao_ataque:
						if data == "Meio":
							ao_a = "ao"
						else:
							ao_a = "a"
						self.bot.send_message(self.chat_id, "BANG!!! @%s atirou %s %s, @%s foi baleado e morto." % (self.players[self.current_player], ao_a, data.lower(), self.players[self.current_player * -1]))
						return "ENDGAME"
					else:
						if "Meio" not in (self.direcao_ataque, data):							
							self.bot.send_message(self.chat_id, "BANG!!! @%s desviou facilmente!" % (self.players[self.current_player * -1]))
						else:
							self.bot.send_message(self.chat_id, "BANG!!! @%s desviou por pouco!" % (self.players[self.current_player * -1]))
						
						self.state = "ATAQUE"
						self.current_player *= -1
						self.play()
				
					
	def player_accepted(self, player):
		if (not self.player2_request) or (self.player2_request == player):
			self.players[2] = player
			self.state = "ATAQUE"
			self.current_player = random.choice([1, -1])
			self.bot.send_message(self.chat_id, "T\nR\n3\nT\n@")
			self.play()
			
	def play(self):
		
		if self.state == "ATAQUE":
			self.send_buttons(("Esquerda", "Meio", "Direita"), "Vez de @%s atacar, escolha uma direção:" % self.players[self.current_player])
			
		if self.state == "DEFESA":
			self.send_buttons(("Esquerda", "Meio", "Direita"), "@%s tente desviar, escolha uma direção:" % self.players[self.current_player * -1])
			