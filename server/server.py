import base64
from datetime import datetime
import json
import os
import socket
from threading import Thread
from dataclasses import dataclass

from dotenv import load_dotenv

from database.crud import get_genres, get_genre, add_genre, delete_genres
from database.crud import get_books, add_book, delete_book, update_book
from database.crud import authenticate_user, register_user
from database.database import SessionLocal, init_db
from database.database import BookTable
from server.logger import get_logger, ClientLoggerAdapter

load_dotenv()
SERVER_HOST = os.getenv("SERVER_HOST", "127.0.0.1")
SERVER_PORT = int(os.getenv("SERVER_PORT", 8080))

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COVERS_DIR = os.path.join(BASE_DIR, os.getenv("COVERS_DIR", "content/covers"))
BOOKS_DIR = os.path.join(BASE_DIR, os.getenv("BOOKS_DIR", "content/books"))

ADMIN_ONLY_COMMANDS: frozenset[str] = frozenset({
    "add_genre",
    "delete_genres",
    "add_book",
    "delete_book",
    "edit_book",
})

logger = get_logger()


def fetch_file_json(file_path: str) -> str:
    """Формирование JSON для передачи одной полноценной книги"""
    full_path = os.path.join(BOOKS_DIR, file_path)

    if not os.path.exists(full_path):
        return json.dumps({
            "status": "error",
            "message": f"Файл '{file_path}' не найден на сервере"
        }, ensure_ascii=False)

    with open(full_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()

    return json.dumps({
        "status": "success",
        "action": "download",
        "filename": os.path.basename(file_path),
        "file_data": encoded
    }, ensure_ascii=False)


def fetch_books_json() -> str:
    """Формирование JSON для передачи информации о всех книгах для карточек"""
    try:
        with SessionLocal() as session:
            books = get_books(session)
            result = []
            for b in books:
                try:
                    p_date = b.public_date.strftime("%d.%m.%Y") if b.public_date else "Дата неизвестна"

                    result.append({
                        "id": b.id,
                        "name": b.name,
                        "author": b.author,
                        "public_date": p_date,
                        "rating": b.rating,
                        "genres": [g.name for g in b.genres],
                        "summary": b.summary or "",
                        "cover_pic": encode_cover(b.cover_path),
                        "file_path": b.file_path
                    })
                except Exception as e:
                    logger.error(f"Ошибка при обработке книги id={getattr(b, 'id', 'unknown')}: {e}", exc_info=True)
                    continue

        return json.dumps({
            "status": "success",
            "action": "books",
            "data": result
        }, ensure_ascii=False)

    except Exception as e:
        logger.error(f"Критическая ошибка при получении списка книг: {e}", exc_info=True)
        return json.dumps({
            "status": "error",
            "message": "Ошибка на стороне сервера при получении списка книг"
        }, ensure_ascii=False)


def fetch_genres_json() -> str:
    """Формирование JSON для передачи информации о всех жанрах для фильтров"""
    try:
        with SessionLocal() as session:
            genres = get_genres(session)
            result = [{"id": genre.id, "name": genre.name} for genre in genres]

        return json.dumps({
            "status": "success",
            "action": "genres",
            "data": result
        }, ensure_ascii=False)

    except Exception as e:
        logger.error(f"Критическая ошибка при получении списка жанров: {e}", exc_info=True)
        return json.dumps({
            "status": "error",
            "message": "Ошибка на стороне сервера при получении списка жанров"
        }, ensure_ascii=False)


def encode_cover(path: str | None) -> str | None:
    """Перевод изображения в строку для обложки в карточку"""
    if not path:
        return None

    full_path = os.path.join(COVERS_DIR, path)
    if not os.path.exists(full_path):
        return None

    with open(full_path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def recv_exact(sock: socket.socket, msg_len: int) -> bytes | None:
    """Получает точное число байт из сокета"""
    buffer = bytearray()
    while len(buffer) < msg_len:
        chunk = sock.recv(msg_len - len(buffer))
        if not chunk:
            return None
        buffer += chunk
    return bytes(buffer)


@dataclass
class ClientSession:
    """Состояние одного клиентского подключения"""
    role: str = "guest"
    username: str | None = None


# --- Обработчики команд -------------------------------------------------------

def _handle_get_books(data: dict, ctx: ClientSession, log: ClientLoggerAdapter) -> str:
    log.debug("Запрос списка книг")
    return fetch_books_json()


def _handle_get_genres(data: dict, ctx: ClientSession, log: ClientLoggerAdapter) -> str:
    log.debug("Запрос списка жанров")
    return fetch_genres_json()


def _handle_download(data: dict, ctx: ClientSession, log: ClientLoggerAdapter) -> str:
    file_path = data.get("file_path", "")
    log.info(f"Скачивание файла: '{file_path}'")
    return fetch_file_json(file_path)


def _handle_login(data: dict, ctx: ClientSession, log: ClientLoggerAdapter) -> str:
    username = data.get("username", "")
    password = data.get("password", "")
    with SessionLocal() as session:
        user = authenticate_user(session, username, password)
        if user:
            ctx.role = user.role.value if hasattr(user.role, "value") else str(user.role)
            ctx.username = user.username
            log.info(f"Успешный вход: username='{username}', role='{ctx.role}'")
            return json.dumps({
                "status": "success",
                "action": "login",
                "user_data": {"username": user.username, "role": ctx.role}
            }, ensure_ascii=False)
        else:
            log.warning(f"Неудачная попытка входа: username='{username}'")
            return json.dumps({
                "status": "error",
                "action": "login",
                "message": "Неверное имя пользователя или пароль"
            }, ensure_ascii=False)


def _handle_register(data: dict, ctx: ClientSession, log: ClientLoggerAdapter) -> str:
    username = data.get("username", "")
    password = data.get("password", "")
    with SessionLocal() as session:
        success, result = register_user(session, username, password)
        if success:
            ctx.role = result.role.value if hasattr(result.role, "value") else str(result.role)
            ctx.username = result.username
            log.info(f"Новый пользователь зарегистрирован: username='{username}'")
            return json.dumps({
                "status": "success",
                "action": "login",
                "user_data": {"username": result.username, "role": ctx.role}
            }, ensure_ascii=False)
        else:
            log.warning(f"Неудачная регистрация: username='{username}', причина='{result}'")
            return json.dumps({
                "status": "error",
                "action": "login",
                "message": result
            }, ensure_ascii=False)


def _handle_add_genre(data: dict, ctx: ClientSession, log: ClientLoggerAdapter) -> str:
    name = data.get("name", "")
    log.info(f"Добавление жанра: '{name}'")
    with SessionLocal() as session:
        add_genre(session, name)
    return fetch_genres_json()


def _handle_delete_genres(data: dict, ctx: ClientSession, log: ClientLoggerAdapter) -> str:
    ids = [int(i) for i in data.get("ids", [])]
    log.info(f"Удаление жанров: ids={ids}")
    with SessionLocal() as session:
        delete_genres(session, ids)
    return fetch_genres_json()


def _handle_add_book(data: dict, ctx: ClientSession, log: ClientLoggerAdapter) -> str:
    try:
        book_filename = data["book_filename"]
        log.info(f"Добавление книги: '{data.get('name', '')}', файл='{book_filename}'")

        with open(os.path.join(BOOKS_DIR, book_filename), "wb") as f:
            f.write(base64.b64decode(data["book_data"]))

        cover_filename = None
        if data.get("cover_data") and data.get("cover_filename"):
            cover_filename = data["cover_filename"]
            with open(os.path.join(COVERS_DIR, cover_filename), "wb") as f:
                f.write(base64.b64decode(data["cover_data"]))

        with SessionLocal() as session:
            genres = [get_genre(session, gid) for gid in data.get("genre_ids", [])]
            book = BookTable(
                name=data["name"],
                author=data["author"],
                summary=data["summary"],
                rating=data["rating"],
                public_date=datetime.strptime(data["public_date"], "%d.%m.%Y").date(),
                genres=[g for g in genres if g],
                file_path=book_filename,
                cover_path=cover_filename,
            )
            add_book(session, book)

        return fetch_books_json()
    except Exception as e:
        log.error(f"Ошибка добавления книги: {e}", exc_info=True)
        return json.dumps({"status": "error", "message": f"Ошибка при добавлении книги: {e}"}, ensure_ascii=False)


def _handle_delete_book(data: dict, ctx: ClientSession, log: ClientLoggerAdapter) -> str:
    book_id = int(data.get("id", 0))
    log.info(f"Удаление книги: id={book_id}")
    with SessionLocal() as session:
        success = delete_book(session, book_id)
    if not success:
        log.warning(f"Книга не найдена при удалении: id={book_id}")
    return fetch_books_json() if success else json.dumps(
        {"status": "error", "message": "Книга не найдена"}, ensure_ascii=False)


def _handle_edit_book(data: dict, ctx: ClientSession, log: ClientLoggerAdapter) -> str:
    try:
        book_id = data.get("id", "?")
        log.info(f"Редактирование книги: id={book_id}")

        book_filename = None
        if data.get("book_data") and data.get("book_filename"):
            book_filename = data["book_filename"]
            with open(os.path.join(BOOKS_DIR, book_filename), "wb") as f:
                f.write(base64.b64decode(data["book_data"]))

        cover_filename = None
        if data.get("cover_data") and data.get("cover_filename"):
            cover_filename = data["cover_filename"]
            with open(os.path.join(COVERS_DIR, cover_filename), "wb") as f:
                f.write(base64.b64decode(data["cover_data"]))

        with SessionLocal() as session:
            success = update_book(session, data, book_filename, cover_filename)

        if not success:
            log.warning(f"Книга не найдена при редактировании: id={book_id}")

        return fetch_books_json() if success else json.dumps(
            {"status": "error", "message": "Книга не найдена"}, ensure_ascii=False)
    except Exception as e:
        log.error(f"Ошибка редактирования книги: {e}", exc_info=True)
        return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)


# Словарь: action -> handler
HANDLERS: dict[str, callable] = {
    "get_books":     _handle_get_books,
    "get_genres":    _handle_get_genres,
    "download":      _handle_download,
    "login":         _handle_login,
    "register":      _handle_register,
    "add_genre":     _handle_add_genre,
    "delete_genres": _handle_delete_genres,
    "add_book":      _handle_add_book,
    "delete_book":   _handle_delete_book,
    "edit_book":     _handle_edit_book,
}


# --- Основной цикл клиента -------------------------------------------------

def handle_client(client: socket.socket, address):
    """Цикл работы с клиентом"""
    ctx = ClientSession()
    log = ClientLoggerAdapter(logger, address, ctx)

    log.info("Новое подключение")

    with client:
        while True:
            try:
                raw_len = recv_exact(client, 4)
                if not raw_len:
                    break

                message_len = int.from_bytes(raw_len, "big")
                raw_data = recv_exact(client, message_len)
                if not raw_data:
                    break

                try:
                    data = json.loads(raw_data.decode())
                except (UnicodeDecodeError, json.JSONDecodeError) as e:
                    log.warning(f"Неверный формат запроса: {e}")
                    err = json.dumps({"status": "error", "message": "Неверный формат запроса"})
                    client.sendall(len(err.encode()).to_bytes(4, "big") + err.encode())
                    continue

                action = data.get("action", "")
                log.info(f"action={action!r}")

                if action in ADMIN_ONLY_COMMANDS and ctx.role != "admin":
                    log.warning(f"Отказано в доступе: action={action!r}, role='{ctx.role}'")
                    response = json.dumps({
                        "status": "error",
                        "message": "Отказано в доступе: требуются права администратора"
                    }, ensure_ascii=False)
                elif action in HANDLERS:
                    response = HANDLERS[action](data, ctx, log)
                else:
                    log.warning(f"Неизвестная команда: {action!r}")
                    response = json.dumps({
                        "status": "error",
                        "message": f"Неизвестная команда: {action!r}"
                    }, ensure_ascii=False)

                encoded = response.encode()
                client.sendall(len(encoded).to_bytes(4, "big") + encoded)

            except OSError as e:
                log.warning(f"Разрыв соединения: {e}")
                break

    log.info("Клиент отключился")


def start_server():
    init_db()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((SERVER_HOST, SERVER_PORT))
        server.listen()
        logger.info(f"Сервер запущен на {SERVER_HOST}:{SERVER_PORT}")

        while True:
            client, addr = server.accept()
            client_thread = Thread(target=handle_client, args=(client, addr), daemon=True)
            client_thread.start()


if __name__ == "__main__":
    start_server()