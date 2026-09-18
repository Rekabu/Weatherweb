from flask import Flask, render_template, request, session, redirect 
import requests


app = Flask(__name__)
app.secret_key = "a3f8b2c9d1e4f7a6b5c8d2e9f1a4b7c3d6e9f2a5b8c1d4e7f3a6b9c2d5e8f1a4"


# --- Словарь переводов погоды ---
TRANSLATIONS = {
    "Sunny": "Солнечно",
    "Clear": "Ясно",
    "Partly cloudy": "Переменная облачность",
    "Cloudy": "Облачно",
    "Overcast": "Пасмурно",
    "Mist": "Туман",
    "Fog": "Туман",
    "Patchy rain nearby": "Местами дождь",
    "Light rain": "Небольшой дождь",
    "Light rain shower": "Небольшой ливень",
    "Moderate rain": "Умеренный дождь",
    "Heavy rain": "Сильный дождь",
    "Light snow": "Небольшой снег",
    "Moderate snow": "Умеренный снег",
    "Heavy snow": "Сильный снег",
    "Blizzard": "Метель",
    "Thundery outbreaks possible": "Возможны грозы",
    "Patchy light rain with thunder": "Местами дождь с грозой",
    "Moderate or heavy rain with thunder": "Сильный дождь с грозой",
    "Light drizzle": "Морось",
    "Freezing drizzle": "Ледяная морось",
    "Patchy light drizzle": "Местами морось",
    "Light freezing rain": "Небольшой ледяной дождь",
    "Moderate or heavy snow showers": "Сильные снегопады",
    "Light snow showers": "Небольшой снегопад",
    "Moderate snow": "Умеренный снег",
    "Patchy moderate snow": "Местами умеренный снег",
    "Patchy heavy snow": "Местами сильный снег",
    "Moderate or heavy sleet": "Сильный мокрый снег",
    "Light sleet": "Небольшой мокрый снег",
    "Torrential rain shower": "Ливень",
    "Moderate or heavy rain shower": "Сильный ливень",
    "Patchy light rain": "Местами небольшой дождь",
    "Moderate rain at times": "Временами умеренный дождь",
    "Heavy rain at times": "Временами сильный дождь",
}


def translate(condition):
    """Переводит описание погоды на русский."""
    condition = condition.strip()
    return TRANSLATIONS.get(condition, condition)


def get_weather(city):
    """Запрашивает текущую погоду через wttr.in."""
    url = f"https://wttr.in/{city}?format=j1&lang=ru"

    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return None

        data = response.json()
        current = data["current_condition"][0]
        
        print("ОПИСАНИЕ ОТ wttr.in:", repr(current["weatherDesc"][0]["value"]))

        return {
            "city": city,
            "temp": current["temp_C"],
            "condition": translate(current["weatherDesc"][0]["value"]),
            "humidity": current["humidity"],
            "wind": current["windspeedKmph"],
            "icon": current["weatherIconUrl"][0]["value"],
        }
    except (requests.exceptions.RequestException, KeyError, IndexError):
        return None


def get_forecast(city):
    """Запрашивает прогноз на 3 дня через wttr.in."""
    url = f"https://wttr.in/{city}?format=j1&lang=ru"

    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return None

        data = response.json()
        forecast = []
        for day in data["weather"][:3]:
            forecast.append({
                "date": day["date"],
                "maxtemp": day["maxtempC"],
                "mintemp": day["mintempC"],
                "condition": translate(day["hourly"][4]["weatherDesc"][0]["value"]),
                "icon": day["hourly"][4]["weatherIconUrl"][0]["value"],
            })
        return forecast
    except (requests.exceptions.RequestException, KeyError, IndexError):
        return None


@app.route("/", methods=["GET", "POST"])
def index():
    weather = None
    forecast = None
    error = None

    # Очистка истории
    if request.args.get("clear"):
        session.pop("history", None)
        return redirect("/")

    # Удаление одного города
    if request.args.get("remove"):
        city_to_remove = request.args.get("remove")
        if "history" in session and city_to_remove in session["history"]:
            session["history"].remove(city_to_remove)
        return redirect("/")

    # POST: ввод города из формы
    if request.method == "POST":
        city = request.form.get("city", "").strip()
        if not city:
            error = "Введите название города."
        else:
            weather = get_weather(city)
            forecast = get_forecast(city)
            if not weather:
                error = f"Не удалось найти погоду для «{city}»"
            else:
                if "history" not in session:
                    session["history"] = []
                if city not in session["history"]:
                    session["history"].insert(0, city)
                    session["history"] = session["history"][:5]

    # GET: клик по городу из истории
    elif request.method == "GET" and request.args.get("city"):
        city = request.args.get("city", "").strip()
        if city:
            weather = get_weather(city)
            forecast = get_forecast(city)
            if not weather:
                error = f"Не удалось найти погоду для «{city}»"

    return render_template(
        "index.html",
        weather=weather,
        forecast=forecast,
        error=error,
    )


if __name__ == "__main__":
    app.run(debug=True)