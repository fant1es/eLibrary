# Файл нужен для генерации данных в базу данных
# !!! ВЫЗВАТЬ ВСЕГО ОДИН РАЗ !!!
from datetime import datetime
from .database import SessionLocal, GenreTable, BookTable, init_db
from sqlalchemy import select, func


def seed_data():
    with SessionLocal() as session:
        # Проверяем количество записей в таблице книг
        result = session.execute(select(func.count()).select_from(BookTable))
        count = result.scalar()

        if count > 0:
            print(f"База уже содержит данные ({count} шт.). Пропускаю заполнение.")
            return

        genres = {
            "classic": GenreTable(name="Классика"),
            "scifi": GenreTable(name="Научная фантастика"),
            "fantasy": GenreTable(name="Фэнтези"),
            "prog": GenreTable(name="Программирование"),
            "dystopia": GenreTable(name="Антиутопия"),
            "drama": GenreTable(name="Драма"),
            "nonfiction": GenreTable(name="Научпоп"),
            "psychology": GenreTable(name="Психология"),
            "horror": GenreTable(name="Ужасы")
        }
        session.add_all(genres.values())

        books_to_add = [
            BookTable(
                name="Мастер и Маргарита",
                author="Михаил Булгаков",
                rating=5.0,
                summary="Сложный многослойный роман, объединяющий сатиру, мистику и философию. История о визите "
                        "дьявола в Москву 1930-х годов и трагической любви писателя и его музы.",
                public_date=datetime.strptime("15.01.1967", "%d.%m.%Y").date(),
                genres=[genres["classic"], genres["drama"]],
                cover_path="master_margarita.jpg"
            ),
            BookTable(
                name="1984",
                author="Джордж Оруэлл",
                rating=4.8,
                summary="Культовое произведение о тоталитарном обществе, где мысли контролируются, а история "
                        "переписывается. История Уинстона Смита, пытающегося сохранить искру человечности в мире "
                        "Большого Брата.",
                public_date=datetime.strptime("08.06.1949", "%d.%m.%Y").date(),
                genres=[genres["dystopia"], genres["scifi"]],
                cover_path="1984.jpg"
            ),
            BookTable(
                name="Солярис",
                author="Станислав Лем",
                rating=4.7,
                summary="Глубокое философское исследование столкновения человечества с абсолютно чуждым разумом — "
                        "живым Океаном планеты Солярис, который материализует самые потаенные страхи и вину "
                        "исследователей.",
                public_date=datetime.strptime("01.01.1961", "%d.%m.%Y").date(),
                genres=[genres["scifi"], genres["drama"]],
                cover_path="solaris.jpg"
            ),
            BookTable(
                name="Дюна",
                author="Фрэнк Герберт",
                rating=4.9,
                summary="Грандиозная сага о пустынной планете Арракис, единственном источнике 'пряности'. История"
                        "Пола Атрейдеса, объединяющая политические интриги, религию, экологию и судьбу человечества.",
                public_date=datetime.strptime("01.08.1965", "%d.%m.%Y").date(),
                genres=[genres["scifi"], genres["fantasy"]],
                cover_path="dune.jpg"
            ),
            BookTable(
                name="Сияние",
                author="Стивен Кинг",
                rating=4.5,
                summary="История Джека Торранса, который устраивается зимним смотрителем в изолированный отель "
                        "'Оверлук'. Психологическое разрушение личности под влиянием призраков прошлого и алкогольной "
                        "зависимости.",
                public_date=datetime.strptime("28.01.1977", "%d.%m.%Y").date(),
                genres=[genres["horror"], genres["drama"]],
                cover_path="shining.jpg"
            ),
            BookTable(
                name="Sapiens: Краткая история человечества",
                author="Юваль Ной Харари",
                rating=4.8,
                summary="Провокационный взгляд на историю нашего вида: от когнитивной революции до наших дней. Как "
                        "биология и история определили нас и наше общество.",
                public_date=datetime.strptime("04.09.2011", "%d.%m.%Y").date(),
                genres=[genres["nonfiction"]],
                cover_path="sapiens.jpg"
            ),
            BookTable(
                name="Выразительный JavaScript",
                author="Марейн Хавербеке",
                rating=4.7,
                summary="Современное введение в программирование на JavaScript. Книга охватывает как основы "
                        "синтаксиса, так и продвинутые темы, включая асинхронность и функциональное программирование.",
                public_date=datetime.strptime("14.12.2014", "%d.%m.%Y").date(),
                genres=[genres["prog"]],
                cover_path="javascript.jpg"
            ),
            BookTable(
                name="О дивный новый мир",
                author="Олдос Хаксли",
                rating=4.6,
                summary="Антиутопия о генетически кастовом обществе потребления, где человечество обменяло свободу и "
                        "эмоции на стабильность и наркотическое счастье.",
                public_date=datetime.strptime("01.01.1932", "%d.%m.%Y").date(),
                genres=[genres["dystopia"]],
                cover_path="brave_new_world.jpg"
            ),
            BookTable(
                name="Тонкое искусство пофигизма",
                author="Марк Мэнсон",
                rating=4.3,
                summary="Контринтуитивный подход к личной эффективности и счастью. Автор объясняет, почему важно "
                        "выбирать, на что тратить свои нервы, и как смириться с неудачами.",
                public_date=datetime.strptime("13.09.2016", "%d.%m.%Y").date(),
                genres=[genres["psychology"], genres["nonfiction"]],
                cover_path="subtle_art.jpg"
            ),
            BookTable(
                name="Автостопом по Галактике",
                author="Дуглас Адамс",
                rating=4.9,
                summary="Невероятно смешная и абсурдная история Артура Дента, покинувшего Землю за мгновение до её "
                        "уничтожения. Помните: главное — не паниковать и иметь при себе полотенце.",
                public_date=datetime.strptime("12.10.1979", "%d.%m.%Y").date(),
                genres=[genres["scifi"]],
                cover_path="hitchhiker.jpg"
            )
        ]

        session.add_all(books_to_add)
        session.commit()
        print("База была пуста. Данные успешно добавлены!")


if __name__ == "__main__":
    init_db()
    seed_data()
