import telebot
import time
import os.path
import sqlite3

from telebot import types
#from telebot import apihelper
#apihelper.proxy = {'https': 'socks5://442518772:HBbqlZ7z@orbtl.s5.opennetwork.cc:999'}

#Подключение к боту
token = "841699118:AAH-Ka0Ab2AUaF8xQAx8I8EzDGsblutEXfE"
bot = telebot.TeleBot(token)

def send(id, msg):
    if len(msg) < 4096:
        bot.send_message(id, msg)
    else:
        symbols = len(msg)
        i = 0
        while symbols > 4096:
            last = msg.rfind(" ", i, i+4096)
            bot.send_message(id, msg[i:last])
            symbols = symbols - (last - i + 1)
            i = last + 1
        bot.send_message(id, msg[i:i + symbols])

#def createAnswer(fed, st):

def updateDB(fz):
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()

    path = "laws\\"+str(fz)
    num = str(fz)[:str(fz).rfind(".txt")]+"-фз"
    #print('num-',num)
    sql = "SELECT * FROM laws WHERE num=?"
    cursor.execute(sql, [(str(num))])
    if not cursor.fetchall():
        cursor.execute("INSERT INTO laws VALUES(\'" + num + "\', '')")
        conn.commit()
        f = open(path, 'r')
        i = 1
        text = f.read()
        while text.find("Статья " + str(i)) != -1:
            a1 = "Статья " + str(i)
            a2 = "Статья " + str(i + 1)
            pos1 = text.find(a1)
            pos2 = text.find(a2)
            posG = text.find("Глава", pos1)

            if posG < pos2 and posG > 0:
                info = text[pos1:posG]
            else:
                if pos2 > -1:
                    info = text[pos1:pos2]
                else:
                    info = text[pos1:]
            article = [(str(num[:len(num)-3]), str(i), info[:info.find("\n")], info)]
            print('added - ', i, 'fz - ', num)
            cursor.executemany("INSERT INTO articles VALUES (?,?,?,?)", article)
            conn.commit()
            i = i + 1
        f.close()
    conn.close()


#updateDB(150)

@bot.message_handler(commands=["start"])
def start(m):
    msg = bot.send_message(m.chat.id, "Пример запроса из клавиатуры: \"152-фз Статья 1\"")
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)

    keyboard.add(*[types.KeyboardButton(name) for name in ['Перейти к базе']])
    keyboard.add(*[types.KeyboardButton(name) for name in ['Управление базой (для администраторов)']])

    bot.send_message(m.chat.id, 'Вы в главном меню',
                     reply_markup=keyboard)
    #bot.register_next_step_handler(msg, chooseLaw)

def set(m):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)

    keyboard.add(*[types.KeyboardButton(name) for name in ['Главное меню']])
    keyboard.add(*[types.KeyboardButton(name) for name in ['Добавить фз']])
    keyboard.add(*[types.KeyboardButton(name) for name in ['Удалить фз']])

    bot.send_message(m.chat.id, 'Здесь вы можете добавить или удалить фз',
                     reply_markup=keyboard)

def chooseLaw(m):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)

    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    sql = "SELECT num FROM laws"
    cursor.execute(sql)
    listOfLaws = cursor.fetchall()
    i = len(listOfLaws)
    keyboard.add(*[types.KeyboardButton(article) for article in ['Главное меню']])
    while i > 0:
        keyboard.add(*[types.KeyboardButton(name) for name in [listOfLaws[len(listOfLaws)-i][0]]])
        i = i - 1
    conn.close()

    bot.send_message(m.chat.id, 'Выберите фз',
        reply_markup=keyboard)
    #bot.register_next_step_handler(msg, chooseArticle)


def chooseArticle(m):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(*[types.KeyboardButton(article) for article in ['Главное меню']])

    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    sql = "SELECT name FROM articles WHERE law=?"
    law = m.text[:m.text.find("-")]
    cursor.execute(sql, [law])
    listOfArts = cursor.fetchall()
    i = len(listOfArts)
    #keyboard.add(*[types.KeyboardButton(article) for article in ['Главное меню']])

    while i > 0:
        keyboard.add(*[types.KeyboardButton(article) for article in [law+"-фз "+listOfArts[len(listOfArts) - i][0]]])
        i = i - 1
    conn.close()

    bot.send_message(m.chat.id, 'Выберите интересующую статью',
        reply_markup=keyboard)

def isAdmin(m):
    id = m.from_user.id
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    sql = "SELECT * FROM admins WHERE id=?"
    cursor.execute(sql, [id])
    if cursor.fetchone():
        return True
    else:
        return False

def addLaw(m):
    bot.send_message(m.chat.id, 'Отправьте мне фз в формате .txt')
    bot.register_next_step_handler(m, getTxt)

#@bot.message_handler(content_types=['document'])
def getTxt(m):
    if m.text:
        #print('text')
        handle_text(m)

    if m.document:
        if isAdmin(m):
            file_info = bot.get_file(m.document.file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            src = "laws\\" + m.document.file_name
            f = open(src, 'w')
            f.write(downloaded_file)
            updateDB(m.document.file_name)
            send(m.from_user.id, "ФЗ добавлен")
        else:
            passRequest(m)

def deleteLaw(m):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)

    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    sql = "SELECT num FROM laws"
    cursor.execute(sql)
    listOfLaws = cursor.fetchall()
    i = len(listOfLaws)
    keyboard.add(*[types.KeyboardButton(article) for article in ['Главное меню']])
    while i > 0:
        keyboard.add(*[types.KeyboardButton(name) for name in ["Удалить " + listOfLaws[len(listOfLaws) - i][0]]])
        i = i - 1
    conn.close()

    bot.send_message(m.chat.id, 'Какой фз удалить?',
                     reply_markup=keyboard)
    #bot.register_next_step_handler(m, removeLawFromDB)


def removeLawFromDB(m):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(*[types.KeyboardButton(article) for article in ['Главное меню']])

    if isAdmin(m):
        law = m.text[m.text.find(" ")+1:]
        num = law[:law.find("-")]
        #print('num-', num, "law-", law)

        conn = sqlite3.connect("data.db")
        cursor = conn.cursor()

        sql = "DELETE FROM laws WHERE num=?"
        cursor.execute(sql, [law])
        conn.commit()

        sql = "DELETE FROM articles WHERE law=?"
        cursor.execute(sql, [num])
        conn.commit()

        conn.close()

        send(m.from_user.id, m.text+" и все его статьи успешно удалены")
        deleteLaw(m)
    else:
        passRequest(m)

def passRequest(m):
    send(m.from_user.id, "Введите ключ авторизации администратора")
    enterPass(m)

def enterPass(m):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(*[types.KeyboardButton(article) for article in ['Главное меню']])

    if m.text == "pass123":
        conn = sqlite3.connect("data.db")
        cursor = conn.cursor()
        user = [(m.from_user.first_name, m.from_user.last_name, m.from_user.id)]
        cursor.executemany("INSERT INTO admins VALUES (?,?,?)", user)
        conn.commit()
        conn.close()

        keyboard.add(*[types.KeyboardButton(article) for article in ['Добавить фз']])
        keyboard.add(*[types.KeyboardButton(article) for article in ['Удалить фз']])
        bot.send_message(m.chat.id, 'Вы добавлены в базу администраторов - теперь вы можете издавать и отменять законы нашего бота',
                         reply_markup=keyboard)

@bot.message_handler(commands=["help"])
def help(message):
    answer = "В чате запрос выглядит так: \"152-фз Статья 1\""
    send(message.from_user.id, answer)

@bot.message_handler(content_types=['text'])
def handle_text(message):
    print('От:', message.from_user.first_name, message.from_user.last_name, '-', message.text)
    if message.text == 'Главное меню':
        start(message)
    elif message.text == 'Управление базой (для администраторов)':
        set(message)
    elif message.text == 'Перейти к базе':
        chooseLaw(message)
    elif message.text == 'Добавить фз':
        if isAdmin(message):
            addLaw(message)
        else:
            passRequest(message)
    elif message.text == 'Удалить фз':
        if isAdmin(message):
            deleteLaw(message)
        else:
            passRequest(message)
    elif message.text.find("Удалить") == 0:
        removeLawFromDB(message)
    elif message.text == 'pass123':
        enterPass(message)
    else:
        #print('От:', message.from_user.first_name, message.from_user.last_name,'-', message.text)
        req = message.text
        law = req[:req.find("-")]

        newMess = req
        indP = req.rfind(".")
        if indP > -1:
            newMess = req[:req.find(".")]
        num = (newMess[newMess.find(" ")+1:])[newMess.find(" ")+1:]

        conn = sqlite3.connect("data.db")
        cursor = conn.cursor()

        sql = "SELECT * FROM laws WHERE num=?"
        cursor.execute(sql, [(str(law))])
        sql = "SELECT text,law FROM articles WHERE law=? AND num=?"
        cursor.execute(sql, [(str(law)), (str(num))])
        text = cursor.fetchone()
        if text:
            answer = text[1]+"-фз "+text[0]
            send(message.from_user.id, answer)
        else:
            sql = "SELECT * FROM laws WHERE num=?"
            cursor.execute(sql, [message.text])
            #print(message.text)
            if cursor.fetchone():
                chooseArticle(message)
            else:
                send(message.from_user.id, "Не найдено, воспользуйтесь меню")
        conn.close()


while True:
    try:
        bot.polling(none_stop=True, interval=0, timeout=3)
    except Exception as e:
        print(e)
        time.sleep(15)
        bot.polling(none_stop=True, interval=0, timeout=3)

