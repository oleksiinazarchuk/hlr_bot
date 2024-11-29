import requests
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import asyncio

# Настройки
API_TOKEN = "tg.api" 
PHP_SERVER_URL = "url"  

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Поля для отображения и их переименование
FIELDS_MAPPING_HLR = {
    "msisdn": "Номер",
    "connectivity_status": "Статус",
    "original_network_name": "Оператор",
    "original_country_name": "Страна",
    "original_country_code": "Код страны",
    "processing_status": "Статус обработки"
}

FIELDS_MAPPING_NT = {
    "number": "Номер",
    "number_type": "Тип номера",
    "query_status": "Статус запроса",
    "is_valid": "Действительный",
    "invalid_reason": "Причина недействительности",
    "is_possibly_ported": "Возможно перенесен",
    "is_vanity_number": "Прямой номер",
    "original_network_name": "Оператор",
    "original_country_name": "Страна",
    "original_country_code": "Код страны",
    "regions": "Регион",
    "timezones": "Часовая зона",
    "info_text": "Информация"
}


# Функция для взаимодействия с PHP-скриптом
def make_request(phone_number, action):
    try:
        # Формируем запрос к PHP-скрипту
        url = f"{PHP_SERVER_URL}?action={action}"
        headers = {"Content-Type": "application/json"}
        data = {"msisdn" if action == "hlr-lookup" else "number": phone_number}

        # Отправляем запрос
        response = requests.post(url, json=data, headers=headers)

        # Если запрос успешен, возвращаем результат
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"HTTP {response.status_code}: {response.text}"}
    except requests.RequestException as e:
        return {"error": f"Ошибка запроса: {str(e)}"}


# Обработчик команды /start
@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.reply(
        "Отправь номер телефона в международном формате (например, +491731972326), чтобы получить информацию."
    )


# Обработчик сообщений с номерами
@dp.message()
async def handle_message(message: types.Message):
    phone_number = message.text.strip()

    # Добавляем "+" в начале номера, если его нет
    if not phone_number.startswith("+"):
        if phone_number.isdigit():
            phone_number = f"+{phone_number}"
        else:
            await message.reply("❌ Введи корректный номер телефона.")
            return

    await message.reply("🔍 Проверяю номер...")

    # Выполняем запрос HLR
    hlr_result = make_request(phone_number, "hlr-lookup")

    # Выполняем запрос NT
    nt_result = make_request(phone_number, "nt-lookup")

    # Обрабатываем результаты HLR
    if "error" in hlr_result:
        hlr_response_text = f"❌ Ошибка HLR: {hlr_result['error']}"
    else:
        hlr_filtered = {FIELDS_MAPPING_HLR[key]: value for key, value in hlr_result.items() if key in FIELDS_MAPPING_HLR}
        hlr_response_text = "📞 Результаты HLR:\n" + "\n".join([f"{key}: {value}" for key, value in hlr_filtered.items()])

    # Обрабатываем результаты NT
    if "error" in nt_result:
        nt_response_text = f"❌ Ошибка NT: {nt_result['error']}"
    else:
        nt_filtered = {}
        for key, value in nt_result.items():
            if key in FIELDS_MAPPING_NT and key != "info_text":
                if isinstance(value, bool):
                    value = "Да" if value else "Нет"
                if isinstance(value, list):
                    value = ", ".join(value)
                value = value if value not in (None, "", "null") else "Информация недоступна"
                nt_filtered[FIELDS_MAPPING_NT[key]] = value

        nt_response_text = "📞 Результаты NT:\n" + "\n".join([f"{key}: {value}" for key, value in nt_filtered.items()])

    # Анализ данных и формирование финального вывода
    analysis_text = "📊 Анализ:\n"
    try:
        hlr_status = hlr_result.get("connectivity_status", "UNDETERMINED")
        number_type = nt_result.get("number_type", "UNKNOWN")

        if hlr_status == "INVALID_MSISDN":
            analysis_text += "❌ Номер недоступен на момент проверки (invalid).\n"
        elif hlr_status == "UNDETERMINED":
            analysis_text += "⚠️ Номер неопределён.\n"
        elif hlr_status == "CONNECTED":
            if number_type == "MOBILE":
                analysis_text += "✅ Номер действительный, мобильный, доступен.\n"
            elif number_type == "PAGER":
                analysis_text += "⚠️ Номер возможно стационарный (pager).\n"
            else:
                analysis_text += f"⚠️ Номер с неизвестным типом: {number_type}.\n"
    except Exception as e:
        analysis_text += f"❌ Ошибка анализа: {str(e)}.\n"

    # Отправляем пользователю оба результата и анализ
    await message.reply(f"{hlr_response_text}\n\n{nt_response_text}\n\n{analysis_text}")




# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
