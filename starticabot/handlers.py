import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from config import API_KEY_OMDB, PAGE_SIZE  # PAGE_SIZE = 10 для топ фильмов
from keyboards import markup, build_movies_list

WATCHLIST_PAGE_SIZE = 5
FAVORITES_PAGE_SIZE = 5

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "👋 Привет! Я бот, который поможет тебе найти интересные фильмы.\n\n"
        "🎬 Нажми кнопку «Топ фильмов» ниже, чтобы получить список популярных фильмов.\n"
        "📝 Также ты можешь использовать «Хочу посмотреть» и «Мои любимые фильмы»!"
    )
    await update.message.reply_text(welcome_text, reply_markup=markup)

async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    movies = []
    for page in range(1, 11):
        url = f'http://www.omdbapi.com/?apikey={API_KEY_OMDB}&s=movie&type=movie&page={page}'
        try:
            response = requests.get(url, timeout=5).json()
        except Exception:
            break
        if response.get('Response') == 'True':
            movies.extend(response.get('Search', []))
        else:
            break

    if not movies:
        await update.message.reply_text('Не удалось получить данные о фильмах.')
        return

    context.user_data['movies'] = movies
    context.user_data['page'] = 0
    await send_movies_page(update, context)

async def send_movies_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
    page = context.user_data.get('page', 0)
    movies = context.user_data.get('movies', [])

    start_idx = page * PAGE_SIZE
    end_idx = start_idx + PAGE_SIZE
    movies_page = movies[start_idx:end_idx]

    keyboard = [
        [InlineKeyboardButton(f"{i + 1}. {movie['Title']} ({movie['Year']})", callback_data=movie['imdbID'])]
        for i, movie in enumerate(movies_page, start=start_idx)
    ]

    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton('⬅ Назад', callback_data='prev'))
    if end_idx < len(movies):
        nav_buttons.append(InlineKeyboardButton('Вперед ➡', callback_data='next'))
    if nav_buttons:
        keyboard.append(nav_buttons)

    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.edit_message_text("Выбери фильм из списка:", reply_markup=reply_markup)
        await update.callback_query.answer()
    else:
        await update.message.reply_text("Выбери фильм из списка:", reply_markup=reply_markup)

async def send_movie_details(update: Update, context: ContextTypes.DEFAULT_TYPE, imdb_id: str):
    url = f"http://www.omdbapi.com/?apikey={API_KEY_OMDB}&i={imdb_id}&plot=full"
    try:
        response = requests.get(url, timeout=5).json()
    except Exception:
        await update.callback_query.message.reply_text("Не удалось получить информацию о фильме.")
        return

    if response.get("Response") != "True":
        await update.callback_query.message.reply_text("Не удалось получить информацию о фильме.")
        return

    title = response.get("Title", "N/A")
    year = response.get("Year", "N/A")
    rating = response.get("imdbRating", "N/A")
    genre = response.get("Genre", "N/A")
    plot = response.get("Plot", "N/A")
    poster = response.get("Poster")

    message = (
        f"*{title}* ({year})\n\n"
        f"*Жанр:* {genre}\n"
        f"*Рейтинг IMDb:* {rating}\n\n"
        f"*Описание:*\n_{plot}_"
    )

    context.user_data['last_movie'] = {
        'imdbID': imdb_id,
        'Title': title,
        'Year': year
    }

    keyboard = InlineKeyboardMarkup([[  
        InlineKeyboardButton("❤️ В любимые", callback_data='add_favorites'),
        InlineKeyboardButton("👁 Хочу посмотреть", callback_data='add_watchlist')
    ]])

    if poster and poster != "N/A":
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=poster,
            caption=message,
            parse_mode='Markdown',
            reply_markup=keyboard
        )
    else:
        await update.callback_query.message.reply_text(
            text=message,
            parse_mode='Markdown',
            reply_markup=keyboard
        )

# Универсальная функция показа страницы для watchlist/favorites с пагинацией


async def send_custom_list_page(update: Update, context: ContextTypes.DEFAULT_TYPE, list_name: str, page_size: int):
    page_key = f"{list_name}_page"
    page = context.user_data.get(page_key, 0)
    user_list = context.user_data.get(list_name, [])

    if not user_list:
        if update.callback_query:
            await update.callback_query.edit_message_text(f"Список {list_name} пуст.")
        else:
            await update.message.reply_text(f"Список {list_name} пуст.")
        return

    start_idx = page * page_size
    end_idx = start_idx + page_size
    page_items = user_list[start_idx:end_idx]

    keyboard = []
    for i, movie in enumerate(page_items, start=start_idx):
        # Кнопка с названием фильма - вызывает детали
        movie_button = InlineKeyboardButton(
            f"{i + 1}. {movie['Title']} ({movie['Year']})",
            callback_data=movie['imdbID']
        )
        # Кнопка удаления - отдельная кнопка с крестиком
        remove_button = InlineKeyboardButton(
            "❌",
            callback_data=f"remove_{list_name}|{movie['imdbID']}"
        )
        # Добавляем кнопки в одну строку
        keyboard.append([movie_button, remove_button])

    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton('⬅ Назад', callback_data=f'{list_name}_prev'))
    if end_idx < len(user_list):
        nav_buttons.append(InlineKeyboardButton('Вперед ➡', callback_data=f'{list_name}_next'))
    if nav_buttons:
        keyboard.append(nav_buttons)

    reply_markup = InlineKeyboardMarkup(keyboard)
    message_text = f"Мои {list_name}:"

    if update.callback_query:
        await update.callback_query.edit_message_text(message_text, reply_markup=reply_markup)
        await update.callback_query.answer()
    else:
        await update.message.reply_text(message_text, reply_markup=reply_markup)


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "Топ фильмов":
        await top(update, context)
        return

    if text == "Хочу посмотреть":
        context.user_data['watchlist_page'] = 0  # сброс страницы при открытии
        await send_custom_list_page(update, context, 'watchlist', WATCHLIST_PAGE_SIZE)
        return

    if text == "Мои любимые фильмы":
        context.user_data['favorites_page'] = 0  # сброс страницы при открытии
        await send_custom_list_page(update, context, 'favorites', FAVORITES_PAGE_SIZE)
        return

    await update.message.reply_text("Пожалуйста, выбери одну из доступных кнопок ниже.")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    if data == 'next':
        context.user_data['page'] = context.user_data.get('page', 0) + 1
        await send_movies_page(update, context)

    elif data == 'prev':
        context.user_data['page'] = max(context.user_data.get('page', 0) - 1, 0)
        await send_movies_page(update, context)

    elif data == 'add_favorites':
        movie = context.user_data.get('last_movie')
        if movie:
            favorites = context.user_data.setdefault('favorites', [])
            if movie not in favorites:
                favorites.append(movie)
                await query.answer("Добавлено в избранное ❤️")
            else:
                await query.answer("Фильм уже в избранном")
        else:
            await query.answer("Нет информации о фильме для добавления")

    elif data == 'add_watchlist':
        movie = context.user_data.get('last_movie')
        if movie:
            watchlist = context.user_data.setdefault('watchlist', [])
            if movie not in watchlist:
                watchlist.append(movie)
                await query.answer("Добавлено в список 'Хочу посмотреть' 👁")
            else:
                await query.answer("Фильм уже в списке 'Хочу посмотреть'")
        else:
            await query.answer("Нет информации о фильме для добавления")

    elif data.startswith('remove_favorites|'):
        imdb_id = data.split('|')[1]
        favorites = context.user_data.get('favorites', [])
        context.user_data['favorites'] = [m for m in favorites if m['imdbID'] != imdb_id]
        await query.answer("Фильм удалён из избранного")
        await send_custom_list_page(update, context, 'favorites', FAVORITES_PAGE_SIZE)

    elif data.startswith('remove_watchlist|'):
        imdb_id = data.split('|')[1]
        watchlist = context.user_data.get('watchlist', [])
        context.user_data['watchlist'] = [m for m in watchlist if m['imdbID'] != imdb_id]
        await query.answer("Фильм удалён из списка 'Хочу посмотреть'")
        await send_custom_list_page(update, context, 'watchlist', WATCHLIST_PAGE_SIZE)

    # Навигация для watchlist
    elif data == 'watchlist_next':
        context.user_data['watchlist_page'] = context.user_data.get('watchlist_page', 0) + 1
        await send_custom_list_page(update, context, 'watchlist', WATCHLIST_PAGE_SIZE)

    elif data == 'watchlist_prev':
        context.user_data['watchlist_page'] = max(context.user_data.get('watchlist_page', 0) - 1, 0)
        await send_custom_list_page(update, context, 'watchlist', WATCHLIST_PAGE_SIZE)

    # Навигация для favorites
    elif data == 'favorites_next':
        context.user_data['favorites_page'] = context.user_data.get('favorites_page', 0) + 1
        await send_custom_list_page(update, context, 'favorites', FAVORITES_PAGE_SIZE)

    elif data == 'favorites_prev':
        context.user_data['favorites_page'] = max(context.user_data.get('favorites_page', 0) - 1, 0)
        await send_custom_list_page(update, context, 'favorites', FAVORITES_PAGE_SIZE)

    else:
        # Если data - imdbID, показать детали фильма
        await send_movie_details(update, context, data)
