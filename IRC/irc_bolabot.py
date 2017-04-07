from twisted.words.protocols.irc import IRCClient
from twisted.internet.protocol import ClientFactory
from twisted.internet.base import DelayedCall
import random
import os
import datetime

irc_server = 'irc.rizon.net'
irc_port = 6667
irc_channel = '#qwertychat'
nick = 'BolaBOT'

def obv(msg):
    if random.randint(1,4) == 1:
        msg += ', obviamente'
    return msg + '.'

#Retorna nick sem caracteres de op, voice, half-op, etc
def raw_nick(nick):
    if nick[0] in '+@%':
        return nick[1:]
    else:
        return nick  
        
#Retorna uma string com stutter, Ex: orc suga pintos -> o-orc s-suga pint-tos
def stutter(frase):
    frase_stutter = ''
    valid_chars = 'bcdfghjklmnpqrstvxz'
    valid_chars = valid_chars + valid_chars.upper()
    i = 0
    while i < len(frase)-1:
        char = frase[i]
        if (char in valid_chars) and (frase[i+1] in 'aeiouwyAEIOUWY') and (random.randint(1,4) <= 3):
            frase_stutter += char + '-' + char
        else:
            frase_stutter += char
        i += 1
    frase_stutter += frase[-1]
    return frase_stutter
    
#Classe
class Roleta:

    roll_limit = 1

    def __init__(self, user1, user2):
        self.players = None, user1, user2
        self.players_rolls = [None, self.roll_limit, self.roll_limit]
        self.current_player = random.choice((1,-1))
        self.players_rolls[self.current_player] += 1         
        self.roll()


    def roll(self):
        if self.players_rolls[self.current_player]:
            self.cylinder = [0] * 6
            self.cylinder[random.randint(0,5)] = 1
            self.players_rolls[self.current_player] -= 1
            self.current_player *= -1
            return True
        else:
            return False
            
    def trigger(self):
        if self.cylinder[0]:
            return True
        else:
            self.cylinder = self.cylinder[1:]
            self.current_player *= -1
            return False
    
class BotProtocol(IRCClient):
    
    nickname = nick
    channel = irc_channel
    bots = 'Internets', 'ChanStat', 'Nserv', nickname
    ops = 'Ystah', 'LeeoZ'
    deds = []
    #Deixe como False se não for nick registrado
    registered = True
    #Deixe como None se não quiser usar whitelist
    whitelist = ['Ystah', 'LeoZ', 'Orcy', 'ralph__', 'Poncheis', 'Dislexia', 'orc', 'Nosomy']
    #whitelist = None
    roleta_timeout = None
    
    def record_file(self, mode):
        rfilename = 'record.txt'
        if not os.path.isfile(rfilename):
            open(rfilename, 'w').close()
        if mode == 'r':
            self.records = {}
            f = open(rfilename)
            record_data = f.read()
            f.close()
            if not record_data:
                return
            record_data = record_data.strip('\n').split('\n')
            for line in record_data:
                line = line.split(':')
                self.records[line[0]] = [int(line[1]), int(line[2]),int(line[3])]
        
        if mode == 'w':
            record_data = ''
            for record in self.records.keys():
                record_data += '%s:%s:%s:%s\n' % (record, self.records[record][0], self.records[record][1], self.records[record][2])
            f = open(rfilename, 'w')
            f.write(record_data)
            f.close()

    def last_file(self, mode):
        lfilename = 'last.txt'
        if not os.path.isfile(lfilename):
            open(lfilename, 'w').close()
        if mode == 'r':
            self.lasts = {}
            f = open(lfilename)
            last_data = f.read()
            f.close()
            if not last_data:
                return
            last_data = last_data.strip('\n').split('\n')
            for line in last_data:
                line = line.split(':')
                self.lasts[line[0]] = line[1]
        
        if mode == 'w':
            last_data = ''
            for last in self.lasts.keys():
                last_data += '%s:%s\n' % (last, self.lasts[last])
            f = open(lfilename, 'w')
            f.write(last_data)
            f.close()
            
    def update_last(self, user):
        self.lasts[user] = str(datetime.datetime.now())
        self.last_file('w')
            
            
    def check_challenge(self):
        if not self.roleta and self.roleta_challenger:
            self.roleta_clean()
            self.say(self.channel, 'TR3T@ cancelada.')
            
    def roleta_clean(self):
        self.roleta = None
        self.roleta_challenger = None
        self.roleta_challenged = None
        try:
            if self.challenge:
                if self.challenge.active():
                    self.challenge.cancel()
        except AttributeError: pass
        self.challenge = None
        
    def roleta_win(self, winner, ded):
        #winner = self.roleta.players[self.roleta.current_player*-1]
        #ded = self.roleta.players[self.roleta.current_player]
        self.deds.append(ded)
        if ded in self.records.keys():
            ban_min = 1 + self.records[ded][2]
            self.records[ded][2] = 0
            self.records[ded][1] += 1
        else:
            self.records[ded] = [0,1,0]
            ban_min = 1
        
        
        if winner in self.records.keys():
            self.records[winner][0] += 1
            self.records[winner][2] += 1
        else:
            self.records[winner] = [1,0,1]                                   
        
        self.record_file('w')
        sprees = None, None, 'DOUBLE KILL', 'TRIPLE KILL', 'ULTRA KILL!', 'RAMPAGE!!!'
        self.say(channel, 'BANG! %s ded. %s min(s).' % (ded, ban_min))
        if self.records[winner][2] >= 2:
            if self.records[winner][2] > 5:
                self.say(channel, '%s RAMPAGE!!! ALGUÉM MATA ESSA PORRA' % winner)
            else:
                self.say(channel, '%s %s' % (winner, sprees[self.records[winner][2]]))
        
        self.roleta_clean()
        self.mode(channel, False, 'o', user = ded)
        self.mode(channel, True, 'b', user = ded)
        reactor.callLater(ban_min * 60, self.unban, ded)        
        
    def unban(self, banned):
        self.mode(irc_channel, False, 'b', user = banned)
        self.deds.remove(banned)
        
    def irc_RPL_NAMREPLY(self, prefix, params):
        self.got_names(params[1], params[3].split())
    
    def got_names(self, channel, names):
        names = list(names)
        self.users = []
        for user in names:
            user = raw_nick(user)
            if user in self.bots:
                continue            
            self.update_last(user)
            self.users.append(user)
    
    def userJoined(self, user, channel):
        user = raw_nick(user)
        if user not in self.bots:
            self.users.append(user)
            print user, 'joined.'
            self.update_last(user)

        
    def userLeft(self, user, quit):
        user = raw_nick(user)
        self.users.remove(user)
        self.update_last(user)
        print user, 'left/quit'
        
        
    userQuit = userLeft
        
    def userKicked(self, kickee, channel, kicker, message):
        kickee = raw_nick(kickee)
        kicker = raw_nick(kicker)
        self.users.remove(kickee)
        print kickee, 'kicked by', kicker
    
    
    def userRenamed(self, oldname, newname):
        self.users.remove(oldname)
        self.users.append(newname)
        
    def signedOn(self):
        if self.registered:
            pass_file = open('bola_pass.txt')
            pwd = pass_file.read().strip('\n')
            pass_file.close()
            self.msg('NickServ', 'IDENTIFY %s' % pwd)
        self.join(self.channel)
        self.roleta_clean()
        self.record_file('r')
        self.last_file('r')
    
    def privmsg(self, user, channel, message):        
        user = user.split('!')[0]
        user = raw_nick(user)
        
        if self.whitelist and user not in self.whitelist:
            return
        
        if channel.startswith('#'):                
            if message.startswith(self.nickname):
                escolha = obv(random.choice(('Sim', 'Não')))
                self.say(channel, escolha)
            
            elif message.startswith('!'):
                cmd = message.split(' ')[0][1:].lower()
                message = ' '.join(message.split(' ')[1:]).strip(' ')
                
                
                # if user in self.ops:
                    # if cmd == 'kick':
                        # self.kick(channel, message)

                    # elif cmd == 'ban':
                        # self.mode(channel, True, 'b', user = message)  

                    # elif cmd == 'kban':
                        # self.mode(channel, True, 'b', user = message)
                        # self.kick(channel, message)
                        
                    # elif cmd == 'unban':
                        # self.mode(channel, False, 'b', user = message)                        
                
                
                if cmd == 'alt':
                    if ':' not in message:
                        msg = message.strip('?')
                    else:
                        msg = message.split(':')[-1].strip().strip('?')
                    alternativas = msg.split(' ou ')
                    if len(alternativas) > 1:
                        self.say(channel, obv(random.choice(alternativas).capitalize()))
                
                if cmd == 'last':
                    if message in self.lasts.keys():
                        self.say(channel, 'Ultima vez que vi %s: %s' % (message, self.lasts[message]))
                        
                    
                if cmd == 'user':
                    self.say(channel, obv(random.choice(self.users)))             
                    
                if cmd == 'nivel':
                    nivel = random.randint(0,10000)
                    msg = 'nivel %s: %s' % (message, nivel)
                    if nivel >= 8000:
                        msg += '!!!'
                    self.say(channel, msg)
                    
                if cmd == 'chance':
                    nivel = random.randint(0,100)
                    msg = 'chance ' + message + ': ' + str(nivel) + r'%'
                    self.say(channel, msg)                        
                    
                if cmd == 'roleta':
                    
                    if not self.roleta:
                        if not message and not self.roleta_challenger:
                            self.roleta_challenger = user
                            self.say(channel, '%s chamou qualquer um pra TR3T@!' % user)
                            self.challenge = reactor.callLater(60, self.check_challenge)
                        
                        elif message == 'accept':
                            if self.roleta_challenger and self.roleta_challenger != user:
                                if not self.roleta_challenged or self.roleta_challenged == user:
                                    self.roleta = Roleta(self.roleta_challenger, user)
                                    self.challenge.cancel()
                                    self.say(channel, 'T\nR\n3\nT\n@\n%s vs %s. %s começa.' % (self.roleta_challenger, user, self.roleta.players[self.roleta.current_player]))
                        
                        else:
                            if message in self.users and not self.roleta_challenger and message != user:
                                self.say(channel, '%s chamou %s pra TR3T@!' % (user, message))
                                self.challenge = reactor.callLater(60, self.check_challenge)                                
                                self.roleta_challenger = user
                                self.roleta_challenged = message
                
                    else:
                        if user == self.roleta.players[self.roleta.current_player]:
                            if message == 'trigger':
                                if self.roleta.trigger():
                                    winner = self.roleta.players[self.roleta.current_player*-1]
                                    ded = self.roleta.players[self.roleta.current_player]
                                    self.deds.append(ded)
                                    if ded in self.records.keys():
                                        ban_min = 1 + self.records[ded][2]
                                        self.records[ded][2] = 0
                                        self.records[ded][1] += 1
                                    else:
                                        self.records[ded] = [0,1,0]
                                        ban_min = 1
                                    
                                    
                                    if winner in self.records.keys():
                                        self.records[winner][0] += 1
                                        self.records[winner][2] += 1
                                    else:
                                        self.records[winner] = [1,0,1]                                   
                                    
                                    self.record_file('w')
                                    sprees = None, None, 'DOUBLE KILL', 'TRIPLE KILL', 'ULTRA KILL!', 'RAMPAGE!!!'
                                    self.say(channel, 'BANG! %s ded. %s min(s).' % (ded, ban_min))
                                    if self.records[winner][2] >= 2:
                                        if self.records[winner][2] > 5:
                                            self.say(channel, '%s RAMPAGE!!! ALGUÉM MATA ESSA PORRA' % winner)
                                        else:
                                            self.say(channel, '%s %s' % (winner, sprees[self.records[winner][2]]))
                                    
                                    self.roleta_clean()
                                    self.mode(channel, False, 'o', user = ded)
                                    self.mode(channel, True, 'b', user = ded)
                                    reactor.callLater(ban_min * 60, self.unban, ded)
                                    
                                else:
                                    #self.say(channel, 'Click. 1/%s, %d' % (len(self.roleta.cylinder), int(1./len(self.roleta.cylinder) * 100)) + r'%')
                                    self.say(channel, 'Click.')
                                    if self.roleta_timeout:
                                        self.roleta_timeout.cancel()
                                        self.roleta_timeout = None
                                    self.roleta_timeout = reactor.callLater(30, self.roleta_win, (self, self.roleta.players[self.roleta.current_player], self.roleta.players[self.roleta.current_player*-1]))
                            
                            elif message == 'roll':
                                if not self.roleta.roll():    
                                    self.say(channel, 'Out of rolls.')
                                else:
                                    self.say(channel, 'Rolling.')
                                    if self.roleta_timeout:
                                        self.roleta_timeout.cancel()
                                        self.roleta_timeout = None
                                    #self.say(channel, 'Rolling. 1/6, 17%')
                        
                    if message == 'cancel':
                        if self.roleta_challenger:
                            self.say(channel, 'TR3T@ cancelada.')
                        self.roleta_clean()
                        
                    if message == 'records':
                        for record in self.records.keys():
                            self.say(self.channel, '%s: %s kills, %s deaths, %s spree, score: %s' % (record, self.records[record][0], self.records[record][1], self.records[record][2], self.records[record][0] - self.records[record][1]))                            
                        
                    
                if cmd == 'cmds' or cmd == 'cmd':
                    if not message:
                        self.say(channel, 'Comandos atuais: !alt, !user, !nivel, !msg(pvt), !chance, !roleta\nUse !cmd <command> pra info detalhada.')
                    if message.startswith('!'):
                        message = message[1:]
                    if message == 'alt':
                        self.say(self.channel, 'Peça pro bot escolher alternativas, separe-as pergunta com " ou ", ex: !alt a ou b?, !alt a ou b\nColoque ":" antes das alternativas caso queira adicionar algum texto, ex !alt escolha: a ou b')
                    if message == 'user':
                        self.say(self.channel, 'Peça pro bot escolher um user do canal, ex: !user mais retardo')
                    if message == 'nivel':
                        self.say(self.channel, 'Peça pro bot falar o nivel de algo(0-10000), ex: !nivel de parrudisse do bot')
                    if message == 'chance':
                        self.say(self.channel, 'Peça pro bot escolher uma porcentagem 0-100%, ex: !chance do bot falar a verdade')
                    if message == 'msg(pvt)' or message == 'msg':
                        self.say(self.channel, 'Fale alguma mensagem em private pro bot falar anonimamente no canal, ex: em pvt com o bot: !msg fode sim')
                    if message == 'roleta':
                        self.say(self.channel, 'Iniciar jogo de roleta russa com alguem, "!roleta" pra chamar qualquer um, "!roleta <nick>" pra chamar alguem especifico, "!roleta trigger" pra puxar o gatilho na sua vez, "!roleta roll" pra rolar o gatilho na sua vez(max 1), "!roleta cancel" pra cancelar jogo atual, "!roleta records" pra ver hall da fama.')
                        
            
            else:
                if random.randint(0,200) == 1:
                    self.say(channel, '%s suga pintos.' % user)
        else:
            cmd = message.split(' ')[0][1:]
            message = ' '.join(message.split(' ')[1:])
            
            if cmd == 'msg':
                if user in self.deds:
                    self.say(self.channel, 'DED(%s): %s' % (user, stutter(message)))
                else:
                    self.say(self.channel, 'MSG: %s' % message)
                print '%s: %s' % (user, message)

class BotFactory(ClientFactory):
    protocol = BotProtocol

    def clientConnectionLost(self, connector, reason):
        connector.connect()

    clientConnectionFailed = clientConnectionLost                  
            
#Main
f = BotFactory()
from twisted.internet import reactor
reactor.connectTCP(irc_server, irc_port, f)
reactor.run()
        