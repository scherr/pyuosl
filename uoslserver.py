# -*- coding: utf-8 -*-

# Maximilian Scherr
# 2002

import threading
import time
import socket
import select
import string
import binascii

class threadh:
    def listthreads(self):
        tlist = []
        for thread in threading.enumerate():
            try:
                if thread.id:
                    tlist.append(thread)

            except:
                pass

        return tlist
    
    def getthread(self, id):
        for thread in self.listthreads():
            if thread.id == id:
                return thread

        return 0

class oputh(threading.Thread):
    def __init__(self):
        self.id = 'oputh'
        self.status = 1
        self.log = open('uoslserver.log', 'w')
        threading.Thread.__init__(self, target=self.stayalife)

    def stayalife(self):
        while self.status:
            time.sleep(1)

        self.log.close()

    def puto(self, string):
        print string
        self.log.write(string +'\n')

class iputh(threading.Thread):
    def __init__(self):
        self.id = 'iputh'
        self.status = 1
        self.threadh = threadh()
        self.functions = functions()
        threading.Thread.__init__(self, target=self.handleiput)

    def handleiput(self):
        oputh = self.threadh.getthread('oputh')
        while self.status:
            iput = raw_input()
            oputh.puto('Input: '+ iput)
            if iput == '?':
                oputh.puto('Valid commands:')
                oputh.puto('? - shows this list')
                oputh.puto('x - shuts down server')
                oputh.puto('o - shows online players')

            elif iput == 'x':
                server = self.threadh.getthread('server')
                server.shutdown()

            elif iput == 'o':
                olplayerlist = self.functions.enumolplayers()
                if olplayerlist == []:
                    oputh.puto('No player is online.')

                else:
                    oputh.puto('Online players:')
                    infoh = self.threadh.getthread('infoh')
                    for olplayer in self.functions.enumolplayers():
                        info = infoh.getinfo(olplayer.id)
                        oputh.puto(info[2])

            else:
                oputh.puto('Invalid command.')

class server(threading.Thread):
    def __init__(self, addr):
        self.id = 'server'
        self.status = 1
        self.addr = addr
        self.threadh = threadh()
        self.oputh = self.threadh.getthread('oputh')
        self.oputh.puto('Starting up server...')
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(addr)
        threading.Thread.__init__(self, target=self.listen)

    def listen(self):
        self.oputh.puto('...finished.')
        while self.status:
            self.sock.listen(1)
            csock, caddr = self.sock.accept()
            tmpthreadobj = clienth(csock, caddr)
            tmpthreadobj.start()

        self.sock.close()

    def shutdown(self):
        self.oputh.puto('Shutting down server...')
        tmpclassobj = functions()
        for olplayer in tmpclassobj.enumolplayers():
            tmpclassobj.disconnclient(olplayer)
            time.sleep(1)
            
        for thread in self.threadh.listthreads():
            if thread.id != 'oputh':
                thread.status = 0
            
        tmpsockobj = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tmpsockobj.connect(self.addr)
        tmpsockobj.close()
        self.oputh.puto('...finished.')
        self.oputh.status = 0

class clienth(threading.Thread):
    def __init__(self, csock, caddr):
        self.id = 'clienth'
        self.status = 1
        self.csock = csock
        self.caddr = caddr
        self.threadh = threadh()
        self.datah = datah(self)
        self.convdata = 0
        self.datalength = 4
        threading.Thread.__init__(self, target=self.recv)

    def recv(self):
        server = self.threadh.getthread('server')
        if not server or not server.status:
            self.csock.close()
            return
        
        oputh = self.threadh.getthread('oputh')
        oputh.puto('Client connected: '+ str(self.caddr))
        while self.status:
            try:
                select.select([self.csock], [], [], 2)
                data = self.csock.recv(self.datalength)
                if data:
                    if self.convdata:
                        self.datah.handledata(self.convdata, data)
                        self.convdata = 0
                        self.datalength = 4

                    else:
                        retval = self.datah.checkdata(data)
                        self.convdata = retval[0]
                        self.datalength = retval[1]

                else:
                    break

            except:
                break
            
        self.status = 0
        self.csock.close()
        infoh = self.threadh.getthread('infoh')
        if self.id[:7] == 'clienth' and len(self.id) > 7:
            tmpclassobj = functions()
            for olplayer in tmpclassobj.enumolplayers():
                if olplayer.id != self.id:
                    tmpclassobj.initnonplayer(self, olplayer)

            oldseq = tmpclassobj.eraseoprop(self, 'oldseq')
            info = infoh.getinfo(self.id)
            info[1] = 0
            infoh.changeinfo(info)
            oputh.puto('Player logged off: '+ info[2])
            
        oputh.puto('Client disconnected: '+ str(self.caddr))

class infoh(threading.Thread):
    def __init__(self):
        self.id = 'infoh'
        self.status = 1
        sav = open('uoslserver.sav', 'r')
        self.infolist = eval(sav.readline()[:-1])
        self.highestser = eval(sav.readline()[:-1])
        self.gprops = eval(sav.readline())
        sav.close()
        threading.Thread.__init__(self, target=self.stayalife)

    def stayalife(self):
        while self.status:
            time.sleep(1)

        sav = open('uoslserver.sav', 'w')
        sav.write(str(self.infolist) +'\n')
        sav.write(str(self.highestser) +'\n')
        sav.write(str(self.gprops))
        sav.close()

    def getinfo(self, id):
        for info in self.infolist:
            if info[0] == id:
                return info

        return 0

    def addinfo(self, addinfo):
        self.infolist.append(addinfo)

    def removeinfo(self, removeinfo):
        self.infolist.remove(removeinfo)

    def changeinfo(self, changeinfo):
        for info in self.infolist:
            if info[0] == changeinfo[0]:
                self.removeinfo(info)
                self.addinfo(changeinfo)

    def generateser(self):
        self.highestser = self.highestser + 1
        return self.highestser

    def checkpassword(self, id, password):
        for info in self.infolist:
            if info[0] == id:
                if not info[1]:
                    if info[3] == password:
                        return 1

                    else:
                        return 0

                else:
                    return 0
                
class functions:
    def __init__(self):
        self.threadh = threadh()
        self.oputh = self.threadh.getthread('oputh')
        self.infoh = self.threadh.getthread('infoh')
        
    def convstrtohex(self, string, length = 0):
        string = str(string)
        convertedstring = ''
        letterindex = 0
        while len(convertedstring) < len(string) * 2:
            hexletter = hex(ord(string[letterindex]))
            convertedstring = convertedstring + hexletter[2:]
            letterindex = letterindex + 1

        if length:
            while len(convertedstring) < length * 2:
                convertedstring = convertedstring +'00'
                
        return convertedstring

    def convinttohex(self, integer, length):
        integer = int(integer)
        convertedinteger = hex(integer)
        convertedinteger = convertedinteger[2:]
        while len(convertedinteger) < length * 2:
            convertedinteger = '0'+ convertedinteger

        return convertedinteger

    def convhextostr(self, hexstring):
        hexstring = str(hexstring)
        convertedhexstring = ''
        hexletterindex = 0
        while len(hexstring) != hexletterindex:
            nexthexletterindex = hexletterindex + 2
            hexletter = hexstring[hexletterindex:nexthexletterindex]
            if hexletter != '00':
                hexletter = int(hexletter, 16)
                letter = chr(hexletter)
                convertedhexstring = convertedhexstring + letter
                hexletterindex = hexletterindex + 2

            else:
                hexletterindex = hexletterindex + 2
                
        return convertedhexstring

    def convhextoint(self, hexinteger):
        hexinteger = str(hexinteger)
        convertedhexinteger = int(hexinteger, 16)
        return convertedhexinteger

    def disconnclient(self, client):
        convdata = 'fe44000101'
        data = binascii.a2b_hex(convdata)
        client.csock.send(data)

    def initplayer(self, player):
        info = self.infoh.getinfo(player.id)
        id = string.split(player.id)
        convdata = 'fe360001'+ self.convinttohex(id[1], 4)
        data = binascii.a2b_hex(convdata)
        player.csock.send(data)
        info[1] = 1
        self.infoh.changeinfo(info)
        self.oputh.puto('Player logged on: '+ info[2])
        convdata = 'fe4c0001'+ self.convinttohex(id[1], 4)
        convdata = convdata +'000000000000000000000005'
        data = binascii.a2b_hex(convdata)
        player.csock.send(data)
        convdata = 'fea600010000000000000000'+ self.convstrtohex(info[2])
        convdata = convdata +'00'
        data = binascii.a2b_hex(convdata)
        for olplayer in self.enumolplayers():
            olplayer.csock.send(data)

    def initnonplayer(self, nonplayer, forplayer):
        info = self.infoh.getinfo(nonplayer.id)
        id = string.split(nonplayer.id)
        convdata = 'fe3a0001'+ self.convinttohex(id[1], 4)
        data = binascii.a2b_hex(convdata)
        forplayer.csock.send(data)

    def updateplayer(self, player):
        info = self.infoh.getinfo(player.id)
        id = string.split(player.id)
        convdata = 'fe3e0001'+ self.convinttohex(id[1], 4)
        convdata = convdata + self.convinttohex(info[4], 2)
        convdata = convdata +'00'
        coords = info[6]
        convdata = convdata + self.convinttohex(coords[0], 2)
        convdata = convdata + self.convinttohex(coords[1], 2)
        convdata = convdata +'0000'
        convdata = convdata + self.convinttohex(info[5], 1)
        convdata = convdata + self.convinttohex(coords[2], 1)
        data = binascii.a2b_hex(convdata)
        player.csock.send(data)

    def updatenonplayer(self, nonplayer, forplayer):
        info = self.infoh.getinfo(nonplayer.id)
        id = string.split(nonplayer.id)
        convdata = 'fe350001'+ self.convinttohex(id[1], 4)
        convdata = convdata + self.convinttohex(info[4], 2)
        convdata = convdata +'000000'
        coords = info[6]
        convdata = convdata + self.convinttohex(coords[0], 2)
        convdata = convdata + self.convinttohex(coords[1], 2)
        convdata = convdata + self.convinttohex(info[5], 1)
        convdata = convdata + self.convinttohex(coords[2], 1)
        data = binascii.a2b_hex(convdata)
        forplayer.csock.send(data)        

    def enumolplayers(self):
        olplayerlist = []
        for thread in self.threadh.listthreads():
            if thread.id[:7] == 'clienth' and len(thread.id) > 7:
                olplayerlist.append(thread)

        return olplayerlist

    def listolplayersnearloc(self, coords, range):
        olplayernearloclist = []
        for olplayer in self.enumolplayers():
            info = self.infoh.getinfo(olplayer.id)
            if self.checkdist(coords, info[6]) <= range:
                olplayernearloclist.append(olplayer)
                
        return olplayernearloclist
    
    def showpd(self, player, forplayer):
        id = string.split(player.id)
        convdata = 'fe420001'+ self.convinttohex(id[1], 4)
        convdata = convdata +'000a'
        data = binascii.a2b_hex(convdata)
        forplayer.csock.send(data)

    def showstatus(self, player, forplayer):
        info = self.infoh.getinfo(player.id)
        id = string.split(player.id)
        convdata = 'fe330001'+ self.convinttohex(id[1], 4)
        convdata = convdata + self.convstrtohex(info[2], 30)
        vitals = info[8]
        convdata = convdata + self.convinttohex(vitals[0], 2)
        stats = info[7]
        convdata = convdata + self.convinttohex(stats[0], 2)
        if player.id == forplayer.id:
            convdata = convdata +'01'

        else:
            convdata = convdata +'00'

        convdata = convdata + self.convinttohex(info[4], 1)
        convdata = convdata + self.convinttohex(stats[0], 2)
        convdata = convdata + self.convinttohex(stats[1], 2)
        convdata = convdata + self.convinttohex(stats[2], 2)
        convdata = convdata + self.convinttohex(vitals[2], 2)
        convdata = convdata + self.convinttohex(stats[2], 2)
        convdata = convdata + self.convinttohex(vitals[1], 2)
        convdata = convdata + self.convinttohex(stats[1], 2)
        exp = info[10]
        convdata = convdata + self.convinttohex(exp[0], 4)
        convdata = convdata + self.convinttohex(exp[2], 4)
        convdata = convdata + self.convinttohex(exp[1] - 1, 2)
        data = binascii.a2b_hex(convdata)
        forplayer.csock.send(data)

    def printtxtabv(self, player, forplayer, text, color = [200, 200, 200]):
        info = self.infoh.getinfo(player.id)
        id = string.split(player.id)
        convdata = 'fe370001'+ self.convinttohex(id[1], 4)
        convdata = convdata +'00000000'
        convdata = convdata + self.convinttohex(color[2], 1)
        convdata = convdata + self.convinttohex(color[1], 1)
        convdata = convdata + self.convinttohex(color[0], 1)
        convdata = convdata + self.convstrtohex(info[2], 30)
        convdata = convdata + self.convstrtohex(text)
        convdata = convdata +'00'
        data = binascii.a2b_hex(convdata)
        forplayer.csock.send(data)

    def moveplayertoloc(self, player, coords):
        convdata = 'fe3f000100'+ self.convinttohex(coords[0], 2)
        convdata = convdata + self.convinttohex(coords[1], 2)
        info = self.infoh.getinfo(player.id)
        convdata = convdata + self.convinttohex(info[5], 1)
        convdata = convdata + self.convinttohex(coords[2], 1)
        data = binascii.a2b_hex(convdata)
        oldcoords = info[6]
        info[6] = coords
        self.infoh.changeinfo(info)
        player.csock.send(data)
        for olplayernearloc in self.listolplayersnearloc(oldcoords, 20):
            if olplayernearloc.id != player.id:
                self.updatenonplayer(player, olplayernearloc)
                self.updatenonplayer(olplayernearloc, player)

        for olplayernearloc in self.listolplayersnearloc(coords, 20):
            if olplayernearloc.id != player.id:
                self.initnonplayer(player, olplayernearloc)
                self.initnonplayer(olplayernearloc, player)
                self.updatenonplayer(player, olplayernearloc)
                self.updatenonplayer(olplayernearloc, player)

    def getgprop(self, gpropname):
        for gprop in self.infoh.gprops:
            if gprop[0] == gpropname:
                return gprop[1]

        return 0

    def setgprop(self, gpropname, gpropval):
        if self.getgprop(gpropname):
            self.erasegprop(gpropname)

        self.infoh.gprops.append([gpropname, gpropval])

    def erasegprop(self, gpropname):
        for gprop in self.infoh.gprops:
            if gprop[0] == gpropname:
                self.infoh.gprops.remove(gprop)

    def getobjbyid(self, id):
        id = str(id)
        for info in self.infoh.infolist:
            infoid = string.split(info[0])
            if infoid[1] == id:
                obj = self.threadh.getthread(info[0])
                return obj

        return 0            

    def showskills(self, player, forplayer):
        info = self.infoh.getinfo(player.id)
        skills = info[9]
        convdata = 'fe6f0001'+ self.convinttohex(skills[0] * 100, 2)
        convdata = convdata + self.convinttohex(skills[1] * 100, 2)
        convdata = convdata + self.convinttohex(skills[2] * 100, 2)
        convdata = convdata + self.convinttohex(skills[3] * 100, 2)
        convdata = convdata + self.convinttohex(skills[4] * 100, 2)
        convdata = convdata + self.convinttohex(skills[5] * 100, 2)
        convdata = convdata + self.convinttohex(skills[6] * 100, 2)
        convdata = convdata + self.convinttohex(skills[7] * 100, 2)
        convdata = convdata + self.convinttohex(skills[8] * 100, 2)
        convdata = convdata + self.convinttohex(skills[9] * 100, 2)
        data = binascii.a2b_hex(convdata)
        forplayer.csock.send(data)

    def checkdist(self, coords1, coords2):
        xdiff = coords1[0] - coords2[0]
        if xdiff < 0:
            xdiff = xdiff * -1

        ydiff = coords1[1] - coords2[1]
        if ydiff < 0:
            ydiff = ydiff * -1
            
        if xdiff > ydiff:
            return xdiff

        else:
            return ydiff
        
    def moveplayer(self, player, dir, seq):
        info = self.infoh.getinfo(player.id)
        if dir > 7:
            dir = dir - 128
            
        coords = info[6]
        if dir == info[5]:
            if dir == 0:
                coords[1] = coords[1] - 1

            elif dir == 1:
                coords[0] = coords[0] + 1
                coords[1] = coords[1] - 1

            elif dir == 2:
                coords[0] = coords[0] + 1

            elif dir == 3:
                coords[0] = coords[0] + 1
                coords[1] = coords[1] + 1

            elif dir == 4:
                coords[1] = coords[1] + 1

            elif dir == 5:
                coords[0] = coords[0] - 1
                coords[1] = coords[1] + 1

            elif dir == 6:
                coords[0] = coords[0] - 1

            elif dir == 7:
                coords[0] = coords[0] - 1
                coords[1] = coords[1] - 1
                
            info[6] = coords

        info[5] = dir
        convdata = 'fe400005'+ self.convinttohex(seq, 1)
        data = binascii.a2b_hex(convdata)
        player.csock.send(data)
        self.infoh.changeinfo(info)
        oldseq = self.getoprop(player, 'oldseq')
        if not oldseq:
            oldseq = 0

        seqdiff = oldseq - seq
        if seqdiff < 0:
            seqdiff = seqdiff * -1
            
        if seqdiff >= 10:
            for olplayernearloc in self.listolplayersnearloc(coords, 20):
                if olplayernearloc.id != player.id:
                    self.updatenonplayer(player, olplayernearloc)
                    self.updatenonplayer(olplayernearloc, player)

            self.setoprop(player, 'oldseq', seq)                    

        else:
            for olplayernearloc in self.listolplayersnearloc(coords, 20):
                if olplayernearloc.id != player.id:
                    self.updatenonplayer(player, olplayernearloc)
        
    def getoprop(self, obj, opropname):
        id = string.split(obj.id)
        info = self.infoh.getinfo(obj.id)
        index = 0
        if id[0] == 'clienth':
            index = 12
            
        for oprop in info[index]:
            if oprop[0] == opropname:
                return oprop[1]

        return 0
    
    def setoprop(self, obj, opropname, opropval):
        self.eraseoprop(obj, opropname)
        id = string.split(obj.id)
        info = self.infoh.getinfo(obj.id)
        index = 0
        if id[0] == 'clienth':
            index = 12
            
        oprops = info[index]
        oprops.append([opropname, opropval])
        info[index] = oprops
        self.infoh.changeinfo(info)

    def eraseoprop(self, obj, opropname):
        id = string.split(obj.id)
        info = self.infoh.getinfo(obj.id)
        index = 0
        if id[0] == 'clienth':
            index = 12
            
        oprops = info[index]
        for oprop in info[index]:
            if oprop[0] == opropname:
                oprops.remove(oprop)

        info[index] = oprops
        self.infoh.changeinfo(info)

    def gethits(self, mob):
        info = self.infoh.getinfo(mob.id)
        vitals = info[8]
        return vitals[0]

    def sethits(self, mob, hits):
        info = self.infoh.getinfo(mob.id)
        vitals = info[8]
        vitals[0] = hits
        self.infoh.changeinfo(info)
        for olplayernearloc in self.listolplayersnearloc(info[6], 20):
            self.showstatus(mob, olplayernearloc)

    def getfati(self, mob):
        info = self.infoh.getinfo(mob.id)
        vitals = info[8]
        return vitals[2]

    def setfati(self, mob, fati):
        info = self.infoh.getinfo(mob.id)
        vitals = info[8]
        vitals[2] = fati
        self.infoh.changeinfo(info)
        for olplayernearloc in self.listolplayersnearloc(info[6], 20):
            self.showstatus(mob, olplayernearloc)

    def getmana(self, mob):
        info = self.infoh.getinfo(mob.id)
        vitals = info[8]
        return vitals[1]

    def setmana(self, mob, mana):
        info = self.infoh.getinfo(mob.id)
        vitals = info[8]
        vitals[1] = mana
        self.infoh.changeinfo(info)
        for olplayernearloc in self.listolplayersnearloc(info[6], 20):
            self.showstatus(mob, olplayernearloc)

class combath(threading.Thread):
    def __init__(self, attacker, defender):
        self.id = 'combath '+ str(attacker.id)
        self.status = 1
        self.attacker = attacker
        self.defender = defender
        self.threadh = threadh()
        self.infoh = self.threadh.getthread('infoh')
        self.functions = functions()
        threading.Thread.__init__(self, target=self.handlec)

    def handlec(self):
        attinfo = self.infoh.getinfo(self.attacker.id)
        definfo = self.infoh.getinfo(self.defender.id)
        if self.functions.checkdist(attinfo[6], definfo[6]) <= 1 and self.functions.getfati(self.attacker) and self.functions.gethits(self.attacker) and self.functions.gethits(self.defender):
            self.functions.printtxtabv(self.attacker, self.attacker, '*You attack '+ definfo[2] +'*', [255, 0, 0])
            self.functions.printtxtabv(self.attacker, self.defender, '*'+ attinfo[2] +' attacks you*', [255, 0, 0])
            self.functions.setfati(self.attacker, self.functions.getfati(self.attacker) - 1)
            self.functions.sethits(self.defender, self.functions.gethits(self.defender) - 1)
            if not self.functions.gethits(self.defender):
                convdata = 'fe4b000101'
                data = binascii.a2b_hex(convdata)
                self.defender.csock.send(data)

        else:
            if self.functions.checkdist(attinfo[6], definfo[6]) > 1:
                self.functions.printtxtabv(self.attacker, self.attacker, '*You are too far away*')

            elif not self.functions.getfati(self.attacker):
                self.functions.printtxtabv(self.attacker, self.attacker, '*You are too fatigue*')

            elif not self.functions.getfati(self.attacker):
                self.functions.printtxtabv(self.attacker, self.attacker, '*You are dead*')
        
class datah:
    def __init__(self, clienth):
        self.clienth = clienth
        self.threadh = threadh()
        self.infoh = self.threadh.getthread('infoh')
        self.oputh = self.threadh.getthread('oputh')
        self.functions = functions()

    def checkdata(self, data):
        convdata = binascii.b2a_hex(data)
        datalength = self.functions.convhextoint(convdata[4:]) - 4
        retval = (convdata, datalength)
        return retval

    def handledata(self, convdata, data):
        convdata = convdata + binascii.b2a_hex(data)
        if convdata[2:4] == '01':
            id = 'clienth '+ str(self.functions.convhextoint(convdata[8:16]))
            password = self.functions.convhextostr(convdata[1116:1176])
            info = self.infoh.getinfo(id)
            if info and id != 'clienth 0':
                if self.infoh.checkpassword(id, password):
                    self.clienth.id = id
                            
                else:
                    convdata = 'feb7000100'
                    data = binascii.a2b_hex(convdata)
                    self.clienth.csock.send(data)
                    self.oputh.puto('Client tried to log on with wrong password or has already logged on: '+ str(self.clienth.caddr))
                    
            elif not info and id == 'clienth 0':
                id = 'clienth '+ str(self.infoh.generateser())
                name = self.functions.convhextostr(convdata[24:84])
                graphic = self.functions.convhextoint(convdata[1176:1178])
                realname = self.functions.convhextostr(convdata[604:860])
                homepage = self.functions.convhextostr(convdata[84:340])
                emailaddr = self.functions.convhextostr(convdata[348:604])
                pcinfo = self.functions.convhextostr(convdata[860:1116])
                self.infoh.addinfo([id, 0, name, password, graphic, 0, [554, 576, 0], [33, 33, 33], [33, 33, 33], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 1, 100], [realname, homepage, emailaddr, pcinfo], []])
                self.clienth.id = id
                self.oputh.puto('Player created: '+ name)

            elif not info and id != 'clienth 0':
                convdata = 'feb7000101'
                data = binascii.a2b_hex(convdata)
                self.clienth.csock.send(data)
                self.oputh.puto('Client tried to log on with non existing player: '+ str(self.clienth.caddr))
                
        elif convdata[2:4] == '0c':
            id = self.functions.convhextoint(convdata[8:])
            obj = self.functions.getobjbyid(id)
            if obj:
                id = string.split(obj.id)
                info = self.infoh.getinfo(obj.id)
                if id[0] == 'clienth':
                    self.functions.showpd(obj, self.clienth)
            
        elif convdata[2:4] == '64':
            if convdata[8:] == '000000001f':
                self.functions.initplayer(self.clienth)
                self.functions.updateplayer(self.clienth)
                for olplayer in self.functions.enumolplayers():
                    if olplayer.id != self.clienth.id:
                        self.functions.initnonplayer(self.clienth, olplayer)
                        self.functions.initnonplayer(olplayer, self.clienth)
                        self.functions.updatenonplayer(self.clienth, olplayer)
                        self.functions.updatenonplayer(olplayer, self.clienth)
                        
            elif convdata[8:10] != '03' and convdata[8:10] != '00':
                id = self.functions.convhextoint(convdata[10:])
                if convdata[8:10] == '04':
                    self.functions.showstatus(self.functions.getobjbyid(id), self.clienth)

                if convdata[8:10] == 'fe':
                    self.functions.showskills(self.functions.getobjbyid(id), self.clienth)

        elif convdata[2:4] == '06':
            info = self.infoh.getinfo(self.clienth.id)
            color = [self.functions.convhextoint(convdata[16:18]), self.functions.convhextoint(convdata[14:16]), self.functions.convhextoint(convdata[12:14])]
            text = self.functions.convhextostr(convdata[18:])
            if text[0] == '#':
                if self.functions.getoprop(self.clienth, 'cmdlvl'):
                    text = string.split(text[1:])
                    if text[0] == 'goxyz':
                        self.functions.moveplayertoloc(self.clienth, [int(text[1]), int(text[2]), int(text[3])])
                        
                    elif text[0] == 'where':
                        self.functions.printtxtabv(self.clienth, self.clienth, str(info[6]))

                    elif text[0] == 'sethits':
                        for olplayernearloc in self.functions.listolplayersnearloc(info[6], 1):
                            if olplayernearloc.id != self.clienth.id:
                                self.functions.sethits(olplayernearloc, int(text[1]))

                    elif text[0] == 'setfati':
                        for olplayernearloc in self.functions.listolplayersnearloc(info[6], 1):
                            if olplayernearloc.id != self.clienth.id:
                                self.functions.setfati(olplayernearloc, int(text[1]))

                    elif text[0] == 'setmana':
                        for olplayernearloc in self.functions.listolplayersnearloc(info[6], 1):
                            if olplayernearloc.id != self.clienth.id:
                                self.functions.setmana(olplayernearloc, int(text[1]))

                    else:
                        self.functions.printtxtabv(self.clienth, self.clienth, 'Invalid command.')

                else:
                    self.functions.printtxtabv(self.clienth, self.clienth, 'You can\'t use commands as a normal player.')
                    
            else:
                if self.functions.gethits(self.clienth):
                    for olplayernearloc in self.functions.listolplayersnearloc(info[6], 20):
                        self.functions.printtxtabv(self.clienth, olplayernearloc, text, color)

        elif convdata[2:4] == '11':
            id = self.functions.convhextoint(convdata[8:])
            obj = self.functions.getobjbyid(id)
            if obj:
                id = string.split(obj.id)
                info = self.infoh.getinfo(obj.id)
                if id[0] == 'clienth':
                    self.functions.printtxtabv(obj, self.clienth, info[2], [0, 0, 255])
                    if not self.functions.gethits(obj):
                        self.functions.printtxtabv(obj, self.clienth, '[dead]', [0, 0, 255])
            
        elif convdata[2:4] == '04':
            dir = self.functions.convhextoint(convdata[8:10])
            seq = self.functions.convhextoint(convdata[10:])
            self.functions.moveplayer(self.clienth, dir, seq)

        elif convdata[2:4] == '0b':
            id = self.functions.convhextoint(convdata[8:])
            if self.threadh.getthread('combath '+ str(id)):
                self.functions.printtxtabv(self.clienth, self.clienth, '*You are already fighting*')

            else:
                tmpthreadobj = combath(self.clienth, self.functions.getobjbyid(id))
                tmpthreadobj.start()
                
class main:
    def __init__(self):
        cfg = open('uoslserver.cfg', 'r')
        addr = eval(cfg.readline())
        cfg.close()
        tmpthreadobj = oputh()
        tmpthreadobj.start()
        tmpthreadobj.puto('Ultima Online: Shattered Legacy Server')
        tmpthreadobj.puto('© 2002 Maximilian Scherr')
        tmpthreadobj.puto('')
        tmpthreadobj = infoh()
        tmpthreadobj.start()
        tmpthreadobj = server(addr)
        tmpthreadobj.start()
        tmpthreadobj = iputh()
        tmpthreadobj.start()

main()
