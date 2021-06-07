import telebot
from telebot import types
import os
from data_functions import getData
from google_module import GoogleDocs, GoogleDocsRead, GoogleSheets
import img_download as img_d


#не забуд прописать в терминал команду pip install pytelegrambotapi (если у тебя мак то pip3, а не pip)

logger = telebot.logger
linkURLSheets = 'https://docs.google.com/spreadsheets/d/13mPMefBJ4gjLF2R6ONaOmJB6dsoM1ylWzg7cKQwh9tk/edit#gid=0'
sheet_data = GoogleSheets(linkURLSheets)

HEROKU = os.environ.get('HEROKU')
if HEROKU == "True":
    TOKEN = os.environ.get('TOKEN')
else:
    import config
    TOKEN = config.TOKEN

bot = telebot.TeleBot(TOKEN)


#это глвное меню бота (вызывается из базы данных, формируется на основе ее значений)
#функция заполняет клавиатуру которая генерируется из базы данных (только главное меню)
#telebot.logger.setLevel(logging.DEBUG)

@bot.message_handler(commands=['start'])
def start(message):
    sheet_data.add_user(user_name=message.chat.username)
    bot.send_message(message.chat.id, "Бот запущен", disable_notification=True)
    main_menu_select_step(message)

@bot.message_handler(content_types=['text'])
def main_menu_select_step(message):
    data = getData('t1')
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True, row_width=2)  # переменная вызывает клавиатуру
    messageList = []
    for item in data:
        if item[1] != "" and item[2] is not None and item[2] != "":
            itembtn = types.KeyboardButton(item[1])
            markup.add(itembtn)
        messageList.append(str(item[4]))

    msg = bot.send_message(message.chat.id,
                           messageList[0],
                           reply_markup=markup, disable_notification=True)  # вызвать клаву
    bot.register_next_step_handler(msg, process_select_step, data)


#выбор дальнейших шагов в по таблицам БД
def process_select_step(message, data):
    # пустые массивы в начале функций нужны для того что при каждом вызове функции из значения заполнялись заново
    nextStep = []
    texts = []
    lastStep = []
    try:
        for item in data: #пробег по массиву из кортежей, получаем следующую т
            # аблицу, текст кнопок, и предыдущую таблицу
            texts.append(item[1])
            nextStep.append(str(item[2]))
            lastStep.append(str(item[3]))
            print(item[1], "->", item[2])
        index = texts.index(message.text)
        table = nextStep[index]
        lastTable = lastStep[index]
        print("Переход к финальной инструкции IT", str("t01" in nextStep))
        print("Переход к финальной инструкции BIM", str("t02" in nextStep))
        if "t01" in nextStep or "t02" in nextStep or "t1" in nextStep: #если следующая таблица пустая то вызывается
            # функция в которой выводится текст инструкции
            instructionList=[]
            imgList = []
            for item in data:
                instructionList.append(item[5])
                imgList.append(str(item[6]) + "\\"+str(item[1]))
            index = texts.index(message.text)
            instruction = instructionList[index]
            path = imgList[index]
            table = nextStep[index]
            if nextStep[index] == '<-':
                data = getData(lastTable)
                menu_select_step(message, data)
            else:
                if nextStep[index] == 't1':
                    case = 1
                elif nextStep[index] == 't01' or nextStep[index] == 't02':
                    case = 2
                else:
                    case = 3

                data = getData(table)
                print_instruction_step(message, instruction, data, case, path)

        else:#в любом другом случае получаем данные о дальнейшем и предыдущем шаге
            # для вызова шаблонной функции генерации кнопок
            print(table)
            if table == "<-":
                data = getData(lastTable)
                menu_select_step(message, data)
            else:
                data = getData(table)
                menu_select_step(message, data)
    except Exception as e:
        #telebot.logger.setLevel(logging.DEBUG)
        if message.text == "В НАЧАЛО":
            main_menu_select_step(message)
        elif message.text == "/start":
            start(message)
        else:
            print(str(e))
            bot.reply_to(message, "Раздел")
            bot.send_message(message.chat.id, 'В данный момент не доступен', reply_markup=types.ReplyKeyboardRemove(),
                             disable_notification=True)
            main_menu_select_step(message)



#Обычная функция генерации кнопок, ничего примечательного
def menu_select_step(message, data):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True, row_width=2)  # переменная вызывает клавиатуру
    messageList = []
    for item in data:
        if item[1] != "" and item[2] is not None and item[2] != "":
            itembtn = types.KeyboardButton(item[1])
            markup.add(itembtn)
        messageList.append(str(item[4]))
    itemBtnBack = types.KeyboardButton('В НАЧАЛО')
    markup.add(itemBtnBack)
    msg = bot.send_message(message.chat.id,
                           messageList[0],
                           reply_markup=markup, disable_notification=True)  # вызвать клаву
    bot.register_next_step_handler(msg, process_select_step, data)

#функция отвечает за вывод текста(далее изображений) инструкции

def print_instruction_step(message, instruction, data, case, path):
    data = data
    if "src" in path:
        count_of_img = img_d.countImg(path)
        print(f"В папке {path}\n{count_of_img} файла")
        instruction_list = str(instruction).split("(рис)")
        try:
            if len(instruction_list) != count_of_img:
                j = 0
                for i in range(count_of_img):
                    img = open(path + f"\\{i + 1}.png", 'rb')
                    try:
                        if len(instruction_list) != 1:
                            bot.send_message(message.chat.id, instruction_list[j], disable_notification=True,
                                         parse_mode="HTML")
                            bot.send_photo(message.chat.id, img, disable_notification=True)
                    except Exception as e:
                        #bot.reply_to(message, "Ошибка инструкции")
                        print(e)
                        break
                    j = j + 1
                try:
                    bot.send_message(message.chat.id, instruction_list[j], disable_notification=True, parse_mode="HTML")
                except Exception as e:
                    print(e)
            else:
                for i in range(count_of_img):
                    img_path = path + f"\\{i + 1}.png"
                    print(img_path)
                    img = open(path + f"\\{i + 1}.png", 'rb')
                    try:
                        bot.send_message(message.chat.id, instruction_list[i], disable_notification=True, parse_mode="HTML")
                        bot.send_photo(message.chat.id, img, disable_notification=True)
                    except Exception as e:
                        #bot.reply_to(message, "Ошибка инструкции")
                        print(e)
                        break
        except Exception as e:
            print(str(e))
            bot.reply_to(message, "Инструкция или изображение отсутствует")
            #bot.send_message(message.chat.id, instruction, parse_mode="HTML", disable_notification=True)
            main_menu_select_step(message)
    elif 'https://' in instruction:
        doc = GoogleDocs(instruction)
        total_list = GoogleDocsRead(doc_body=doc.get_document_body(), inline_objects=doc.get_inline_object()
                                    ).join_total_list()
        for item in total_list:
            if item.count('googleusercontent') == 0:
                bot.send_message(message.chat.id, item, disable_notification=True, parse_mode="HTML")
            else:
                bot.send_photo(message.chat.id, item, disable_notification=True)

    else:
        if instruction != "":
            bot.send_message(message.chat.id, instruction, parse_mode="HTML", disable_notification=True)
    if case == 1:
        if message.text == "Спасибо, инструкция помогла":
            effective = True
        else:
            effective = False
        sheet_data.add_interaction_point(user_name=message.chat.username, effective=effective)
        main_menu_select_step(message)
    elif case == 2:
        final_menu_select_step(message, data)
    elif case == 3:
        menu_select_step(message, data)


#Последний шаг, генерируются кнопки для завершения работы (вопрос: помогло или нет?)
def final_menu_select_step(message, data):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True, row_width=2)  # переменная вызывает клавиатуру
    messageList = []
    for item in data:
        itembtn = types.KeyboardButton(item[1])
        messageList.append(str(item[2]))
        markup.add(itembtn)
    msg = bot.send_message(message.chat.id,
                           messageList[0],
                           reply_markup=markup, disable_notification=True)  # вызвать клаву
    bot.register_next_step_handler(msg, final_process_select_step, data)

#выводится тескт с дальнейшими указаниями если инструкция не помогла. (в дальнейшем здесь будет вызываться запись в БД)
def final_process_select_step(message, data):
    texts = []
    answers = []
    try:
        for item in data:
            texts.append(item[1])
            answers.append(item[3])
        index = texts.index(message.text)
        if message.text == "Да":
            effective = True
        else:
            effective = False
        sheet_data.add_interaction_point(user_name=message.chat.username, effective=effective)
        bot.send_message(message.chat.id, answers[index], disable_notification=True)
        main_menu_select_step(message)
    except Exception as e:
        #telebot.logger.setLevel(logging.DEBUG)
        if message.text == "В НАЧАЛО":
            main_menu_select_step(message)
        else:
            print(str(e))
            bot.reply_to(message, 'Такого раздела пока нет')
            main_menu_select_step(message)


if __name__ == "__main__":
    try:
        bot.polling()
    except:
        pass


#Команды Git

#git add .
#git commit -m "*"
#git push
#git push heroku main
