try:
    from tkinter import *
except ImportError:
    from Tkinter import *
try:
    import pyttsx3
except ImportError:
    import pyttsx as pyttsx3
from random import randint
import time
import pymysql
from PIL import Image, ImageTk
import webbrowser
import os
import sys
import platform
import const
import dblogin
from lang import locales
import locale
import requests
import re
import threading


def resource_path(relative_path):
    #Get absolute path to resource, works for dev and for PyInstaller
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath('.')

    return os.path.join(base_path, relative_path)

class Game:
    def __init__(self):
        self.speechEngine = pyttsx3.init()
        self.locale = locales[locale.getdefaultlocale()[0].lower()] if locale.getdefaultlocale()[0].lower() in locales else 'en_us'
        originalFlagImage = Image.open(resource_path('res/flag.png'))
        resizedFlagImage = originalFlagImage.resize((const.BLOCK_SIZE, const.BLOCK_SIZE), Image.ANTIALIAS)
        self.OPWIN = Tk()
        self.flagImage = ImageTk.PhotoImage(resizedFlagImage)
        self.OPWIN.iconbitmap(resource_path('res/icon.ico'))
        self.OPWIN.title('MinesweePy')
        self.OPWIN.geometry('250x150')
        self.OPWIN.resizable(0, 0)
        self.OPWIN.restartButton = Button(self.OPWIN, text=self.locale['newgame'] , command=lambda : self.startNewGame())
        self.OPWIN.flagLabel = Label(self.OPWIN, text=self.locale['flagsleft'], font=('Helvetica', 20))
        self.OPWIN.difficulty = StringVar()
        self.OPWIN.difficulty.trace('w', lambda *_: self.setDifficulty(self.OPWIN.difficulty.get()))
        self.OPWIN.difficulty.set('Easy')
        self.OPWIN.difficultyMenu = OptionMenu(self.OPWIN, self.OPWIN.difficulty, *const.GRIDS)
        self.OPWIN.leaderboardButton = Button(self.OPWIN, text=self.locale['leaderboard'], command=self.displayLeaderboard)
        self.OPWIN.pauseButton = Button(self.OPWIN, text=self.locale['pause'], command=lambda : self.pauseGame())
        self.OPWIN.difficultyMenu.pack()
        self.OPWIN.restartButton.pack()
        self.OPWIN.leaderboardButton.pack()
        self.outdated = self.checkVersion()

    def checkVersion(self):
        try:
            url = 'https://raw.githubusercontent.com/thaag7734/minesweepy/master/VERSION'
            r = requests.get(url)
            version = r.text
            if const.VERSION == version:
                return False
            else:
                self.outdatedWindow = Toplevel()
                self.outdatedWindow.iconbitmap(resource_path('res/error.ico'))
                head = self.locale['OUTDATED']['head']
                body = self.locale['OUTDATED']['body']
                self.outdatedWindow.versionWarningHead = Label(self.outdatedWindow, text=head, fg='red')
                self.outdatedWindow.versionWarningBody = Label(self.outdatedWindow, text=body, wraplength=200)
                self.outdatedWindow.updateButton = Button(self.outdatedWindow, text=self.locale['updatebutton'], command=self.openUpdate)
                self.outdatedWindow.versionWarningHead.pack()
                self.outdatedWindow.versionWarningBody.pack()
                self.outdatedWindow.updateButton.pack()
                return True
        except requests.RequestException:
            self.outdatedWindow = Toplevel()
            self.outdatedWindow.iconbitmap(resource_path('res/error.ico'))
            self.outdatedWindow.noConnHead = Label(self.outdatedWindow, text=self.locale['NO_CONN']['head'], fg='red')
            self.outdatedWindow.noConnBody = Label(self.outdatedWindow, text=self.locale['NO_CONN']['body'], wraplength=200)
            self.outdatedWindow.noConnHead.pack()
            self.outdatedWindow.noConnBody.pack()
            return 'nc'

    def openUpdate(self):
        system = platform.system()
        if system == 'Windows': os.system('start "" http://degenerat.es/minesweepy')
        elif system == 'Darwin': os.system('open "" http://degenerat.es/minesweepy')
        elif system == 'Linux': os.system('xdg-open "" http://degenerat.es/minesweepy')
        else: webbrowser.open('http://degenerat.es/minesweepy')

    def setDifficulty(self, difficulty):
        self.difficulty = difficulty

    def startNewGame(self):
        self.gameOver = False
        self.exposed = 0
        try:
            self.WINDOW.destroy()
            self.WINDOW = Toplevel()
        except AttributeError:
            self.WINDOW = Toplevel()
        try:
            self.victoryWindow.destroy()
        except AttributeError:
            pass
        try:
            self.leaderboardWindow.destroy()
        except AttributeError:
            pass
        self.WINDOW.iconbitmap(resource_path('res/icon.ico'))
        self.WINDOW.title('MinesweePy')
        self.WINDOW.resizable(0,0)
        self.WINDOW.pauseText = Label(self.WINDOW, text=self.locale['paused'], font=('Helvetica', 32), anchor=CENTER)
        self.winx = self.OPWIN.winfo_x() + self.OPWIN.winfo_width() + 50
        self.winy = self.OPWIN.winfo_y()
        self.WINDOW.geometry('+%d+%d' % (self.winx, self.winy))
        self.field = Field(self.difficulty, self.WINDOW)
        self.flagsLeft = IntVar()
        self.flagsLeft.trace('w', lambda *_: self.OPWIN.flagLabel.config(text=self.locale['flagsleft'] + str(self.flagsLeft.get())))
        self.flagsLeft.set(self.field.MINE_COUNT)
        self.WINDOW.bind('<ButtonRelease-1>', lambda _: self.frameClicked())
        self.WINDOW.bind('<ButtonRelease-3>', lambda _: self.flag())
        self.WINDOW.bind('<Escape>', lambda _: self.pauseGame())
        self.OPWIN.flagLabel.pack()
        self.OPWIN.pauseButton.pack()
        self.paused = False
        self.pausedTimes = []
        self.timerStart = time.time() #THIS IS BAD AND I SHOULDNT BE USING IT REE

    def pauseGame(self):
        if not self.paused:
            self.paused = True
            self.pausedTimes += [time.time() - self.timerStart]
            for y in range(0, self.field.GRID_SIZE):
                for x in range(0, self.field.GRID_SIZE):
                    self.field.dispField[y][x].grid_forget()
            self.WINDOW.pauseText.place(relx=0.5, rely=0.5, anchor=CENTER)
        else:
            self.paused = False
            self.WINDOW.pauseText.place_forget()
            for y in range(0, self.field.GRID_SIZE):
                for x in range(0, self.field.GRID_SIZE):
                    self.field.dispField[y][x].grid(row=y, column=x)
            self.timerStart = time.time()
            

    def frameClicked(self):
        if not self.gameOver and not self.paused:
            self.visitedLastClick = []
            y = (self.WINDOW.winfo_pointery() - self.WINDOW.winfo_rooty()) // self.field.BLOCK_SIZE
            x = (self.WINDOW.winfo_pointerx() - self.WINDOW.winfo_rootx()) // self.field.BLOCK_SIZE

            if not self.field.dispField[y][x].flagLabel.cget('image'):
                self.expose([y,x])

            if self.exposed == (self.field.GRID_SIZE ** 2) - self.field.MINE_COUNT:
                return self.win()

    def expose(self, coords):
        self.chainEnd = False
        y = coords[0]
        x = coords[1]
        if self.field.valField[y][x]:
            return self.explode()

        if self.field.dispField[y][x].cget('relief') == RAISED and not self.field.dispField[y][x].flagLabel.cget('image'):
            self.field.dispField[y][x].config(relief=SUNKEN)
            self.exposed += 1

        if self.field.dispField[y][x].flagLabel.cget('image'):
            self.chainEnd = True

        if self.field.dispField[y][x].exposeLabel.cget('text') != '0' and not self.field.dispField[y][x].flagLabel.cget('image'):
            self.field.dispField[y][x].exposeLabel.pack()
            self.chainEnd = True

        if [y,x] not in self.visitedLastClick:
            self.visitedLastClick.append([y,x])
            if not self.chainEnd:
                if y >= 1:
                    if not self.field.valField[y-1][x]: self.expose([y-1, x])
                if x >= 1:
                    if not self.field.valField[y][x-1]: self.expose([y, x-1])
                if x < self.field.GRID_SIZE - 1:
                    if not self.field.valField[y][x+1]: self.expose([y, x+1])
                if y < self.field.GRID_SIZE - 1:
                    if not self.field.valField[y+1][x]: self.expose([y+1, x])

    def flag(self):
        if not self.gameOver:
            y = (self.WINDOW.winfo_pointery() - self.WINDOW.winfo_rooty()) // self.field.BLOCK_SIZE
            x = (self.WINDOW.winfo_pointerx() - self.WINDOW.winfo_rootx()) // self.field.BLOCK_SIZE
            if self.field.dispField[y][x].cget('relief') != SUNKEN:
                if self.field.dispField[y][x].flagLabel.cget('image'):
                    self.field.dispField[y][x].flagLabel.config(image='')
                    self.field.dispField[y][x].flagLabel.pack_forget()
                    self.flagsLeft.set(self.flagsLeft.get() + 1)
                else:
                    if self.flagsLeft.get() > 0:
                        self.field.dispField[y][x].flagLabel.config(image=self.flagImage)
                        self.field.dispField[y][x].flagLabel.pack()
                        self.flagsLeft.set(self.flagsLeft.get() - 1)

    def explode(self):
        for y in range(0, self.field.GRID_SIZE):
            for x in range(0, self.field.GRID_SIZE):
                if self.field.valField[y][x]:
                    self.field.dispField[y][x].config(relief=SUNKEN)
                    self.field.dispField[y][x].flagLabel.pack_forget()
                    self.field.dispField[y][x].exposeLabel.pack()
        self.gameOver = True
        self.speechEngine.say(self.locale['explodespeech'])
        self.speechThread = threading.Thread(target=self.speechEngine.runAndWait)
        self.speechThread.start()

    def win(self):
        self.gameOver = True
        self.timerEnd = time.time()
        self.speechEngine.say(self.locale['winspeech'])
        self.speechThread = threading.Thread(target=self.speechEngine.runAndWait)
        self.speechThread.start()
        self.elapsedTime = 0
        timeSum = 0
        for currTime in self.pausedTimes:
            timeSum += currTime
        self.elapsedTime += timeSum
        self.elapsedTime += self.timerEnd - self.timerStart
        self.victoryWindow = Toplevel()
        self.victoryWindow.iconbitmap(resource_path('res/icon.ico'))
        self.victoryWindow.timeLabel = Label(self.victoryWindow, text=self.locale['savetime'] % (self.difficulty, self.elapsedTime),
                                              font=('Helvetica', 18), wraplength=300)
        self.validateCmd = (self.victoryWindow.register(self.validateName), '%P', '%d', '%S')
        self.victoryWindow.nameEntry = Entry(self.victoryWindow, validate='key', vcmd=self.validateCmd)
        self.victoryWindow.submitButton = Button(self.victoryWindow, text=self.locale['submitbutton'],
                                                 command=lambda : self.submitTime(self.victoryWindow.nameEntry.get(), self.elapsedTime))
        self.victoryWindow.invalidInputLabel = Label(self.victoryWindow, wraplength=300, fg='red', text=self.locale['validation'])
        if self.outdated == 'nc':
            self.victoryWindow.timeLabel.config(text=self.locale['NO_CONN']['body'], wraplength=500)
            self.victoryWindow.nameEntry.config(state=DISABLED)
            self.victoryWindow.submitButton.config(text=self.locale['continuebutton'])
        elif self.outdated:
            self.victoryWindow.timeLabel.config(wraplength=500, text=self.locale['outdatedsave'])
            self.victoryWindow.nameEntry.config(state=DISABLED)
            self.victoryWindow.submitButton.config(text=self.locale['continuebutton'])
        self.victoryWindow.timeLabel.pack()
        self.victoryWindow.nameEntry.pack()
        self.victoryWindow.submitButton.pack()

    def validateName(self, name, act, char):
        if len(name) > 255: return False
        if not (re.match('^[a-zA-Z0-9_ .]+$', name) or name == ''):
            self.victoryWindow.invalidInputLabel.pack()
            self.victoryWindow.submitButton.config(state=DISABLED)
        else:
            self.victoryWindow.invalidInputLabel.pack_forget()
            self.victoryWindow.submitButton.config(state=NORMAL)
        return True

    def submitTime(self, name, time):
        try:
            if not self.outdated:
                conn = pymysql.connect(host=dblogin.DB_LOGIN['host'], user=dblogin.DB_LOGIN['user'], passwd=dblogin.DB_LOGIN['passwd'],
                                       database=dblogin.DB_LOGIN['database'], port=dblogin.DB_LOGIN['port'])
                cursor = conn.cursor()
                numRows = cursor.execute('SELECT * FROM `%s` WHERE `name` = "%s"' % (self.difficulty, name))
                if numRows >= 10:
                    limit = numRows - 9
                    cursor.execute('DELETE FROM `%s` WHERE `name` = "%s" ORDER BY `time` DESC LIMIT %d' % (self.difficulty, name, limit))
                cursor.execute('INSERT INTO `%s` (`name`,`time`) VALUES ("%s", %d)' % (self.difficulty, name, time))
                cursor.close()
                conn.close()
            self.victoryWindow.destroy()
            self.displayLeaderboard()
        except pymysql.err.OperationalError:
            errWindow = Toplevel()
            errWindow.iconbitmap(resource_path('res/error.ico'))
            errWindow.errHead = Label(errWindow, text=self.locale['NO_CONN']['head'], fg='red')
            errWindow.errBody = Label(errWindow, text=self.locale['NO_CONN']['body'], wraplength=200)
            errWindow.errHead.pack()
            errWindow.errBody.pack()

    def displayLeaderboard(self):
        self.leaderboardWindow = Toplevel()
        self.leaderboardWindow.iconbitmap(resource_path('res/icon.ico'))
        self.leaderboardWindow.title('MinesweePy')
        self.leaderboardWindow.titleText = Label(self.leaderboardWindow, text=self.locale['toptimes'] % self.difficulty, font=('Helvetica', 20))
        self.leaderboardWindow.lbFrame = Frame(self.leaderboardWindow, relief=RAISED, bd=1, highlightthickness=0, bg='#0d0d0d')
        self.leaderboardWindow.topFive = [
            Label(self.leaderboardWindow.lbFrame, fg='#ffd700', bg=self.leaderboardWindow.lbFrame.cget('bg'), font=('Helvetica', 20)),
            Label(self.leaderboardWindow.lbFrame, fg='#c0c0c0', bg=self.leaderboardWindow.lbFrame.cget('bg'), font=('Helvetica', 18)),
            Label(self.leaderboardWindow.lbFrame, fg='#cc6633', bg=self.leaderboardWindow.lbFrame.cget('bg'), font=('Helvetica', 16)),
            Label(self.leaderboardWindow.lbFrame, fg='#eeeeee', bg=self.leaderboardWindow.lbFrame.cget('bg'), font=('Helvetica', 16)),
            Label(self.leaderboardWindow.lbFrame, fg='#eeeeee', bg=self.leaderboardWindow.lbFrame.cget('bg'), font=('Helvetica', 16))
            ]
        try:
            conn = pymysql.connect(host=dblogin.DB_LOGIN['host'], user=dblogin.DB_LOGIN['user'], passwd=dblogin.DB_LOGIN['passwd'],
                                   database=dblogin.DB_LOGIN['database'], port=dblogin.DB_LOGIN['port'])
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM `%s` ORDER BY `time` LIMIT 5' % self.difficulty)
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            self.leaderboardWindow.titleText.pack()
            self.leaderboardWindow.lbFrame.pack(pady=(0, 10))
            for timeNum in range(0, len(results)):
                self.leaderboardWindow.topFive[timeNum].config(text='%s: %d' % (results[timeNum][0], results[timeNum][1]))
                self.leaderboardWindow.topFive[timeNum].pack()
        except pymysql.err.OperationalError:
            self.leaderboardWindow.titleText.pack()
            self.leaderboardWindow.connectionErrorText = Label(self.leaderboardWindow, text=self.locale['noconn'], fg='red')
            self.leaderboardWindow.connectionErrorText.pack()

class Field:
    def __init__(self, difficulty, window):
        originalBombImage = Image.open(resource_path('res/bomb.png'))
        resizedBombImage = originalBombImage.resize((const.BLOCK_SIZE, const.BLOCK_SIZE), Image.ANTIALIAS)
        self.bombImage = ImageTk.PhotoImage(resizedBombImage)
        self.BLOCK_SIZE = const.BLOCK_SIZE
        self.GRID_SIZE  = const.GRIDS[difficulty]['GRID_SIZE']
        self.MINE_COUNT = const.GRIDS[difficulty]['MINE_COUNT']
        self.WINDOW = window

        self.createField()

    def createField(self):
        self.valField = [[0 for i in range(0,self.GRID_SIZE)] for i in range(0,self.GRID_SIZE)]
        
        self.mineList = []
        while len(self.mineList) < self.MINE_COUNT:
            y = randint(0,self.GRID_SIZE - 1)
            x = randint(0,self.GRID_SIZE - 1)
            coords = [y,x]
            if coords not in self.mineList:
                self.mineList.append(coords)
                self.valField[y][x] = 1

        self.dispField = [[Frame(self.WINDOW, height=self.BLOCK_SIZE, width=self.BLOCK_SIZE, bd=1, highlightthickness=0, relief=RAISED) for i in range(0,self.GRID_SIZE)] for i in range(0,self.GRID_SIZE)]

        for y in range(0, self.GRID_SIZE):
            for x in range(0, self.GRID_SIZE):
                self.dispField[y][x].exposeLabel = Label(self.dispField[y][x], font=('Helvetica', self.BLOCK_SIZE - 4))
                self.dispField[y][x].flagLabel = Label(self.dispField[y][x], image='', font=('Helvetica', self.BLOCK_SIZE - 4))
                self.dispField[y][x].pack_propagate(False)

                if self.valField[y][x] == 1:
                    self.dispField[y][x].exposeLabel.config(image=self.bombImage)
                else:
                    around = 0
                    if y >= 1:
                        if x >= 1:
                            if self.valField[y-1][x-1]: around += 1
                        if self.valField[y-1][x]: around += 1
                        if x < self.GRID_SIZE - 1:
                            if self.valField[y-1][x+1]: around += 1

                    if x >= 1:
                        if self.valField[y][x-1]: around += 1

                    if x < self.GRID_SIZE - 1:
                        if self.valField[y][x+1]: around += 1

                    if y < self.GRID_SIZE - 1:
                        if x >= 1:
                            if self.valField[y+1][x-1]: around += 1
                        if self.valField[y+1][x]: around += 1
                        if x < self.GRID_SIZE - 1:
                            if self.valField[y+1][x+1]: around += 1


                    self.dispField[y][x].exposeLabel.config(text=str(around), fg=const.COLOURS[around])
                self.dispField[y][x].grid(row=y, column=x)

game = Game()
game.OPWIN.mainloop()
