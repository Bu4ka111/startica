from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

reply_keyboard = [
    [KeyboardButton("Топ фильмов")],
    [KeyboardButton("Хочу посмотреть"), KeyboardButton("Мои любимые фильмы")]
]
markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=False)

def build_movies_list(movies, list_type):
    if not movies:
        return "Список пуст.", None
    movies_text = "\n".join([f"{i+1}. {movie['Title']} ({movie['Year']})" for i, movie in enumerate(movies)])
    keyboard = [
        [InlineKeyboardButton(f"Удалить ❌", callback_data=f"remove_{list_type}|{movie['imdbID']}")]
        for movie in movies
    ]
    return movies_text, InlineKeyboardMarkup(keyboard)
