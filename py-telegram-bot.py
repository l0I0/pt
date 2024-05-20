import logging
import re
import paramiko
from dotenv import load_dotenv
import os
import psycopg2
from psycopg2 import Error, errors
from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler

# Загрузка переменных окружения
TOKEN = os.getenv('TOKEN')

# Параметры SSH
host = 'debian_ssh'
port = 22
username = 'admin'
password = 'admin'
print(username, password)


db_password = os.getenv('DB_PASSWORD')
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')
db_user = os.getenv('DB_USER')
db_name = os.getenv('DB_NAME')

# Настройка логирования
logging.basicConfig(
    filename='logfile.txt',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def run_command(command, host=host, port=22, user=username, passwd=password):
    logger.info(f"Running command: {command}")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, port=port, username=user, password=passwd)

    stdin, stdout, stderr = client.exec_command(command)
    stdin.close()

    data = stdout.read() + stderr.read()
    client.close()

    data = data.decode('utf-8')
    
    # Удаление предупреждения из данных
    if command.startswith('apt list --installed'):
        data = re.sub(r'WARNING: apt does not have a stable CLI interface. Use with caution in scripts.\n', '', data)
    
    return data

def query_database(query):
    try:
        connection = psycopg2.connect(user=db_user,
                                      password=db_password,
                                      host=db_host,
                                      port=db_port,
                                      database=db_name)
        cursor = connection.cursor()
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()
        connection.close()
        return result
    except (Exception, Error) as error:
        logger.error("Ошибка при работе с PostgreSQL: %s", error)
        return None
    
def insert_into_database(query, values):
    try:
        connection = psycopg2.connect(user=db_user,
                                      password=db_password,
                                      host=db_host,
                                      port=db_port,
                                      database=db_name)
        cursor = connection.cursor()
        cursor.execute(query, values)
        connection.commit()
        cursor.close()
        connection.close()
        return True
    except (Exception, Error) as error:
        logger.error("Ошибка при работе с PostgreSQL: %s", error)
        return False


def format_uptime(seconds):
    seconds = int(seconds)
    days = seconds // (24 * 3600)
    seconds %= (24 * 3600)
    hours = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    return f"{days} days, {hours} hours, {minutes} minutes, {seconds} seconds"

# Команда /start
def start(update: Update, context):
    user = update.effective_user
    logger.info(f"User {user.full_name} started the bot.")
    update.message.reply_text(f'Привет {user.full_name}!')

# Команда /help
def helpCommand(update: Update, context):
    help_text = (
        "Список команд:\n"
        "/find_email - Поиск email-адресов\n"
        "/find_phone_number - Поиск телефонных номеров\n"
        "/verify_password - Проверка сложности пароля\n"
        "/get_release - Информация о релизе системы\n"
        "/get_uname - Архитектура процессора, имя хоста и версия ядра\n"
        "/get_uptime - Время работы системы\n"
        "/get_df - Состояние файловой системы\n"
        "/get_free - Состояние оперативной памяти\n"
        "/get_mpstat - Производительность системы\n"
        "/get_w - Информация о работающих пользователях\n"
        "/get_auths - Последние 10 входов в систему\n"
        "/get_critical - Последние 5 критических событий\n"
        "/get_ps - Информация о запущенных процессах\n"
        "/get_ss - Информация об используемых портах\n"
        "/get_apt_list - Установленные пакеты\n"
        "/get_services - Запущенные сервисы\n"
        "/get_repl_logs - Вывод логов о репликации\n"
        "/get_phone_numbers - Вывод всех номеров телефонов\n"
        "/get_emails - Вывод всех почт\n"
    )
    logger.info("User requested help.")
    update.message.reply_text(help_text)

# Поиск номеров
def findPhoneNumbersCommand(update: Update, context):
    logger.info("User initiated phone number search.")
    update.message.reply_text('Введите текст для поиска телефонных номеров')
    return 'findPhoneNumbers'

# Обработчик поиска телефонных номеров
def findPhoneNumbers(update: Update, context):
    user_input = update.message.text
    logger.info(f"User is searching for phone numbers in text: {user_input}")

    numberRegex = re.compile(r'(\+7|8)\s?[-(]?\d{3}[-\s)]?\d{3}[-\s]?\d{2}[-\s]?\d{2}')
    matches = numberRegex.finditer(user_input)

    phoneNumberList = [match.group() for match in matches]

    if not phoneNumberList:
        logger.info("No phone numbers found.")
        update.message.reply_text('Телефонные номера не найдены')
        return ConversationHandler.END
    
    phoneNumbers = '\n'.join(phoneNumberList)
    logger.info(f"Found phone numbers: {phoneNumbers}")
    update.message.reply_text(f"Найденные номера телефонов:\n{phoneNumbers}\n")
    context.user_data['phone_numbers'] = phoneNumberList
    for phone_number in phoneNumberList:
        success = insert_into_database("INSERT INTO phone_numbers (phone_number) VALUES (%s)", (phone_number,))
        if success:
            update.message.reply_text(f"Номер телефона {phone_number} успешно сохранен.")
            logger.info(f"Номер телефона сохранен в БД: {phoneNumbers}")

        else:
            update.message.reply_text(f"Не удалось сохранить номер телефона {phone_number}.")
            logger.info(f"Не удалось сохранить номер телефона {phone_number}.")
    return ConversationHandler.END


# Команда для поиска email-адресов
def findEmailCommand(update: Update, context):
    logger.info("User initiated email search.")
    update.message.reply_text('Введите текст для поиска email-адресов')
    return 'findEmail'

# Обработчик поиска email-адресов
def findEmail(update: Update, context):
    user_input = update.message.text
    logger.info(f"User is searching for emails in text: {user_input}")

    emailRegex = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
    emailList = emailRegex.findall(user_input)

    if not emailList:
        logger.info("No emails found.")
        update.message.reply_text('Email-адреса не найдены')
        return ConversationHandler.END
    
    emails = '\n'.join(emailList)
    logger.info(f"Found emails: {emails}")
    update.message.reply_text(f"Найденные email-адреса:\n{emails}\n")
    context.user_data['emails'] = emailList
    for email in emailList:
        success = insert_into_database("INSERT INTO emails (email) VALUES (%s)", (email,))
        if success:
            update.message.reply_text(f"Email {email} успешно сохранен.")
            logger.info(f"Email {email} успешно сохранен.")
        else:
            update.message.reply_text(f"Не удалось сохранить email {email}.")
            logger.info(f"Не удалось сохранить почту {phone_number}.")
    return ConversationHandler.END

def verifyPasswordCommand(update: Update, context):
    logger.info("User initiated password verification.")
    update.message.reply_text('Введите пароль для проверки')
    return 'verifyPassword'

# Обработчик проверки пароля
def verifyPassword(update: Update, context):
    user_input = update.message.text
    logger.info(f"User is verifying password: {user_input}")

    passwordRegex = re.compile(r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[!@#$%^&*()])[A-Za-z\d!@#$%^&*()]{8,}$')

    if passwordRegex.match(user_input):
        logger.info("Password is strong.")
        update.message.reply_text('Пароль сложный')
    else:
        logger.info("Password is weak.")
        update.message.reply_text('Пароль простой')
    
    return ConversationHandler.END

def get_release(update: Update, context):
    release_info = run_command('cat /etc/os-release')
    logger.info(f"Retrieved release info: {release_info}")
    update.message.reply_text(release_info)

def get_uname(update: Update, context):
    architecture = run_command('uname -m').strip()
    hostname = run_command('hostname').strip()
    kernel = run_command('uname -r').strip()
    response = f"Processor Architecture: {architecture}\nHostname: {hostname}\nKernel Version: {kernel}"
    logger.info(f"Retrieved uname info: {response}")
    update.message.reply_text(response)

def get_uptime(update: Update, context):
    raw_uptime = float(run_command('cat /proc/uptime').split()[0])
    uptime = format_uptime(raw_uptime)
    logger.info(f"Retrieved uptime: {uptime}")
    update.message.reply_text(uptime)

def get_df(update: Update, context):
    df_info = run_command('df -h')
    logger.info(f"Retrieved disk usage info: {df_info}")
    update.message.reply_text(df_info)

def get_free(update: Update, context):
    mem_info = run_command('free -h')
    logger.info(f"Retrieved memory usage info: {mem_info}")
    update.message.reply_text(mem_info)

def get_mpstat(update: Update, context):
    cpu_use = run_command('mpstat')
    logger.info(f"Retrieved CPU usage info: {cpu_use}")
    update.message.reply_text(cpu_use)

def get_w(update: Update, context):
    users_info = run_command('w')
    logger.info(f"Retrieved user info: {users_info}")
    update.message.reply_text(users_info)

def get_auths(update: Update, context):
    auths_info = run_command('last -n 10')
    logger.info(f"Retrieved authentication logs: {auths_info}")
    update.message.reply_text(auths_info)

def get_critical(update: Update, context):
    crit_logs = run_command('journalctl -p crit -n 5')
    logger.info(f"Retrieved critical logs: {crit_logs}")
    update.message.reply_text(crit_logs)

def get_ps(update: Update, context):
    ps_info = run_command('ps aux')
    logger.info(f"Retrieved process info: {ps_info}")
    update.message.reply_text(ps_info)

def get_ss(update: Update, context):
    ss_info = run_command('ss -tuln')
    logger.info(f"Retrieved socket info: {ss_info}")
    update.message.reply_text(ss_info)

def get_apt_list(update: Update, context):
    logger.info("User initiated apt list retrieval.")
    update.message.reply_text('Введите название пакета для поиска или напишите "all" для получения списка всех установленных пакетов.')
    return 'get_apt_list'

def process_apt_list(update: Update, context):
    user_input = update.message.text.strip().lower()
    logger.info(f"User requested apt list with input: {user_input}")

    if user_input == 'all':
        apt_list = run_command('apt list --installed')
    else:
        apt_list = run_command(f'apt list --installed | grep {user_input}')
    
    apt_list = re.sub(r'WARNING: apt does not have a stable CLI interface. Use with caution in scripts.\n', '', apt_list)

    if not apt_list.strip():
        logger.info("No packages found.")
        update.message.reply_text('Пакеты не найдены.')
    else:
        max_length = 4096
        for i in range(0, len(apt_list), max_length):
            logger.info(f"Sending apt list chunk: {apt_list[i:i+max_length]}")
            update.message.reply_text(apt_list[i:i+max_length])
    
    return ConversationHandler.END

def get_services(update: Update, context):
    services_info = run_command('systemctl list-units --type=service --state=running')
    logger.info(f"Retrieved services info: {services_info}")
    update.message.reply_text(services_info)

def get_repl_logs(update: Update, context):
    logger.info("Логи репликации")
    repl_logs = run_command(command='grep -Ei "replication|streaming|WAL streaming|ready to accept connections" /var/log/postgresql/postgresql-15-main.log',
                            user='admin',
                            passwd='admin',
                            host='db')
    if not repl_logs.strip():
        update.message.reply_text('Логи репликации не найдены.')
    else:
        max_length = 4096
        for i in range(0, len(repl_logs), max_length):
            update.message.reply_text(repl_logs[i:i+max_length])

def get_emails(update: Update, context):
    logger.info("Запрошеныы почты.")
    query = "SELECT email FROM emails;"
    result = query_database(query)
    if result:
        emails = '\n'.join([row[0] for row in result])
        update.message.reply_text(emails)
    else:
        update.message.reply_text('Не удалось получить данные из базы данных.')

def get_phone_numbers(update: Update, context):
    logger.info("Запрошены номера телефона.")
    query = "SELECT phone_number FROM phone_numbers;"
    result = query_database(query)
    if result:
        phone_numbers = '\n'.join([row[0] for row in result])
        update.message.reply_text(phone_numbers)
    else:
        update.message.reply_text('Не удалось получить данные из базы данных.')

def main():
    updater = Updater(TOKEN, use_context=True)

    dp = updater.dispatcher

    convHandlerFindPhoneNumbers = ConversationHandler(
        entry_points=[CommandHandler('find_phone_number', findPhoneNumbersCommand)],
        states={
            'findPhoneNumbers': [MessageHandler(Filters.text & ~Filters.command, findPhoneNumbers)],
        },
        fallbacks=[]
    )

    convHandlerFindEmail = ConversationHandler(
        entry_points=[CommandHandler('find_email', findEmailCommand)],
        states={
            'findEmail': [MessageHandler(Filters.text & ~Filters.command, findEmail)],
        },
        fallbacks=[]
    )

    convHandlerVerifyPassword = ConversationHandler(
        entry_points=[CommandHandler('verify_password', verifyPasswordCommand)],
        states={
            'verifyPassword': [MessageHandler(Filters.text & ~Filters.command, verifyPassword)],
        },
        fallbacks=[]
    )

    convHandlerGetAptList = ConversationHandler(
        entry_points=[CommandHandler('get_apt_list', get_apt_list)],
        states={
            'get_apt_list': [MessageHandler(Filters.text & ~Filters.command, process_apt_list)],
        },
        fallbacks=[]
    )

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", helpCommand))
    dp.add_handler(convHandlerFindPhoneNumbers)
    dp.add_handler(convHandlerFindEmail)
    dp.add_handler(convHandlerVerifyPassword)
    dp.add_handler(convHandlerGetAptList)

    dp.add_handler(CommandHandler("get_release", get_release))
    dp.add_handler(CommandHandler("get_uname", get_uname))
    dp.add_handler(CommandHandler("get_uptime", get_uptime))
    dp.add_handler(CommandHandler("get_df", get_df))
    dp.add_handler(CommandHandler("get_free", get_free))
    dp.add_handler(CommandHandler("get_mpstat", get_mpstat))
    dp.add_handler(CommandHandler("get_w", get_w))
    dp.add_handler(CommandHandler("get_auths", get_auths))
    dp.add_handler(CommandHandler("get_critical", get_critical))
    dp.add_handler(CommandHandler("get_ps", get_ps))
    dp.add_handler(CommandHandler("get_ss", get_ss))
    dp.add_handler(CommandHandler("get_services", get_services))

    dp.add_handler(CommandHandler("get_repl_logs", get_repl_logs))
    dp.add_handler(CommandHandler("get_emails", get_emails))
    dp.add_handler(CommandHandler("get_phone_numbers", get_phone_numbers))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()