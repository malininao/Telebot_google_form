import telebot
from telebot import types
import os
import google_module
from google_module import GoogleSheets


#не забуд прописать в терминал команду pip install pytelegrambotapi (если у тебя мак то pip3, а не pip)

logger = telebot.logger


HEROKU = os.environ.get('HEROKU')
if HEROKU == "True":
    TOKEN = os.environ.get('TOKEN')
    LINK = os.environ.get('LINK')
else:
    import CONFIG
    TOKEN = CONFIG.TOKEN
    LINK = CONFIG.LINK
bot = telebot.TeleBot(TOKEN)


#это глвное меню бота (вызывается из базы данных, формируется на основе ее значений)
#функция заполняет клавиатуру которая генерируется из базы данных (только главное меню)
#telebot.logger.setLevel(logging.DEBUG)

@bot.message_handler(commands=['start', 'reload'])
def start(message):
    answers = []
    sheet_data = GoogleSheets(LINK)
    sheet_values = sheet_data.get_sheets_values()
    structure = sheet_values[1]
    questions = sheet_values[2]
    text_1 = structure[0][0] % (message.chat.username)
    markup = types.ReplyKeyboardRemove()
    bot.send_message(message.chat.id, text_1, disable_notification=True, reply_markup=markup)
    iterator = 1
    structure_moving(message, structure, questions, iterator, answers, sheet_data)

def structure_moving(message, structure, questions, iterator, answers, sheet_data):
    answers.append(message.text)
    if iterator == len(structure[0])-1:
        text = structure[0][iterator]
        del answers[0]
        if str(text).count('%s') != 0:
            text = text % (answers[0], len(questions[0])-1)
        bot.send_message(message.chat.id, text, disable_notification=True)
        iterator_question = 0
        answers_question = []
        print(answers)
        question_moving(message, questions, iterator_question, answers, answers_question, sheet_data)
    else:
        msg = bot.send_message(message.chat.id, structure[0][iterator], disable_notification=True)
        bot.register_next_step_handler(msg,structure_moving, structure, questions, iterator+1, answers, sheet_data)


def question_moving(message, questions, iterator_question, answers, answers_question, sheet_data):
    answers_question.append(message.text)
    if iterator_question == len(questions[0])-1:
        bot.send_message(message.chat.id, questions[0][iterator_question], disable_notification=True)
        del answers_question[0]
        print(answers_question)
        question = questions[0]
        del question[len(question) - 1]
        #print(question)

        choose_end_step(message, answers, answers_question, question, sheet_data)
    else:
        counter_text = f'Вопрос {iterator_question+1} из {len(questions[0])-1}'
        bot.send_message(message.chat.id, counter_text, disable_notification=True)
        msg = bot.send_message(message.chat.id, questions[0][iterator_question], disable_notification=True)
        bot.register_next_step_handler(msg, question_moving, questions, iterator_question+1, answers, answers_question,
                                       sheet_data)


def get_result_message(list_one, list_two):
    united_string = ''
    for i, v in enumerate(list_two):
        united_string = united_string + f'{i+1}. {list_one[i]}: {list_two[i]}\n'
    print(united_string)
    return united_string


def choose_end_step(message, answers, answers_question, question, sheet_data):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True, row_width=2)
    itembtn_one = types.KeyboardButton("Отправить")
    itembtn_two = types.KeyboardButton("Редактировать")
    markup.add(itembtn_one, itembtn_two)
    result = get_result_message(question, answers_question)
    msg = bot.send_message(message.chat.id, f'Ваш ответ:\n{result}', reply_markup=markup, disable_notification=True)
    bot.register_next_step_handler(msg, process_select_step, answers, answers_question, question, sheet_data)


def process_select_step(message, answers, answers_question, question, sheet_data):
    if message.text == "Отправить":
        markup = types.ReplyKeyboardRemove()
        bot.send_message(message.chat.id, "Записываю результаты...", disable_notification=True, reply_markup=markup)
        get_total_list(message, answers, answers_question, question, sheet_data)
    if message.text == "Редактировать":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=5)
        indexs = enumerate(answers_question)
        item_btns = []
        for i in indexs:
            item_btn = types.KeyboardButton(i[0]+1)
            #item_btns.append(item_btn)
            markup.add(item_btn)

        bot.send_message(message.chat.id, "Какой ответ нужно отредактировать?", disable_notification=True,
                         reply_markup=markup)
        msg = bot.send_message(message.chat.id, 'Как только будет доступна функция отредактируется',
                               disable_notification=True)
        bot.register_next_step_handler(msg, start)


def get_total_list(message, answers, answers_question, question, sheet_data):
    answer_list = []
    for i, v in enumerate(answers_question):
        answer_list.append(question[i])
        answer_list.append(answers_question[i])
    print(answer_list)
    date = google_module.DateTime.date()
    time = google_module.DateTime.time()
    time_date = f'{time} {date}'
    time_date = [time_date]
    total_list = answers + time_date + answer_list
    print(total_list)

    #sheet_data.add_answer(message.chat.username, total_list)

    bot.send_message(message.chat.id, "Данные записаны. Спасибо что прошли опрос. В будущем для прохождения нового"
                                      " опроса, или перепрохождения текущего нажмите /start в меню выбора команд",
                     disable_notification=True)


if __name__ == "__main__":
    try:
        bot.polling()
    except Exception as e:
        print(e)


#Команды Git

#git add .
#git commit -m "*"
#git push
#git push heroku main
