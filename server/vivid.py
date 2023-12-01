# TODO Vivid:
# TODO Джамал: начал работу
#  Динамическое написание книги, с сохранением результата, (в .md) - Джамал
#  Сохранение результата предполагает сохранение в рамках генерации одной книги.
#  Чтобы если падал сайт, то генерация продолжалась после поднятия.
#  Должна быть возможность ручного ввода любых данных, включая названия глав книги и их содержания.

# TODO Вячеслав: пока рано
#  Бэк-енд.
#  Сохранение книги в PDF(из .md) - Вячеслав. Идея: использовать FPDF для Python
#  Динамическая отправка процесса генерации на фронт.
#  Придумать как реализовать аккаунты, дабы данные пользовательского ввода сохранялись и если пользователь
#  уже генерировал книгу ранее, мог ее скачать заново.

# TODO Ибро: пока рано
#  Фронт-енд. Для начала хотя бы главную страницу. С НОРМАЛЬНЫМ ДИЗАЙНОМ.
#  Идея:
#  Сайт должен быть написан от и до на react.
#  С поддержкой websockets (для отслеживания процесса генерации)

# Все части программы могут поддаваться критике и обсуждаться членам группы (Vivid).
# Если есть какие-либо предложения, писать в чат.

import asyncio
import os
import re

import g4f
import uuid

import logging

# Create a custom logger
logger = logging.getLogger(__name__)

# Set level of logger
logger.setLevel(logging.DEBUG)

# Create handlers
c_handler = logging.StreamHandler()
c_handler.setLevel(logging.DEBUG)

# Create formatters and add it to handlers
c_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
c_handler.setFormatter(c_format)

# Add handlers to the logger
logger.addHandler(c_handler)


class Vivid:
    """
    Vivid(яркий) - просто слово, состоящее из 3 различных букв
    V - Вячеслав
    I - Ибро
    D - Джамал
    """

    REQUEST_CHAPTERS_PATTERN = r'(\d+)\.\s(.*)'
    REQUEST_CHAPTER_PATTERN = "Текст главы"

    def __init__(
            self,
            sections_count=7,
            chapters_count=12,
            chapters_length=4000,
            v: int | float | str = "3.5",
            genre="",
            book=""
    ):
        if sections_count < 3:
            chapters_count = 3
            print('Кол-во разделов не может быть меньше 3, поэтому установлено как 3')
        if chapters_count < 4:
            chapters_count = 4
            print('Кол-во глав в разделе не может быть меньше 4, поэтому установлено как 4')
        if chapters_length < 300:
            chapters_length = 300
            print('Кол-во символов в главе не может быть меньше 300, поэтому установлено как 300')
        self.CHAPTERS_COUNT = chapters_count
        self.CHAPTERS_LENGTH = chapters_length
        self.REQUEST_CHAPTERS = """
        Действуй в роли писателя в жанре "{0}"! Пиши на русском языке!
        Сгенерируй названия """ + str(self.CHAPTERS_COUNT) + """ штук различных глав для раздела "{2}" книги "{1}".
        Не указывай сайты-источники!
        Отвечай строго по шаблону ниже и больше никак!

        Номер. Название главы
        """

        self.SECTIONS_COUNT = sections_count
        self.REQUEST_SECTIONS = """
        Действуй в роли писателя в жанре "{0}"! Пиши на русском языке!
        Сгенерируй названия """ + str(self.SECTIONS_COUNT) + """ штук различных разделов для книги "{1}".
        Не указывай сайты-источники!
        Отвечай строго по шаблону ниже и больше никак!

        Номер. Название раздела
        """  # TODO

        self.REQUEST_PREGENERATION = """
        Действуй в роли писателя в жанре "{0}"! Пиши на русском языке!
        Сгенерируй названия основных сюжетных мест и имён героев для книги "{1}".
        Названия разделов этой книги:
        {2}

        Не указывай сайты-источники!
        Ответь строго по шаблону ниже:
        Основные сюжетные места/темы/имена/названия мест/имена героев(если уместно в данной книге):
        ...

        {1} - книга о ...
        """

        self.REQUEST_CHAPTER = """
        Действуй в роли писателя в жанре "{0}"! Пиши на русском языке!
        Сгенерируй текст размером """ + str(self.CHAPTERS_LENGTH) + """ символов главы "{2}" для книги "{1}".
        Названия прошлых глав(используй для правильной последовательности повествования):
        {4}

        Важная информация:
        {5}
        Не указывай сайты-источники!

        Не делай отсылок к прошлым или будущим главам. Не пиши ничего о том, что будет в следующей главе.

        Отвечай строго по шаблону ниже и больше никак!

        "Глава {2}"
        {3}   
        """
        if str(v) == "3.5":
            self.gpt = self.gpt35
        elif str(v) == "4.0":
            self.gpt = self.gpt4
        else:
            raise ValueError(f'Invalid GPT Version - {v}')
        self.genre = genre
        self.chapters = {}
        self.sections = []  # TODO
        self.book = book
        self.book_id = uuid.uuid4()
        self.pregeneration = ""

    @staticmethod
    async def gpt35(ans):
        logger.info(f'GPT-3.5 executing: {ans}')
        try:
            result = await g4f.ChatCompletion.create_async(
                model=g4f.models.Model(
                    name='gpt-3.5-turbo',
                    base_provider='openai',
                    best_provider=g4f.Provider.RetryProvider([
                        g4f.Provider.ChatgptX, g4f.Provider.GptGo, g4f.Provider.You,
                        g4f.Provider.NoowAi, g4f.Provider.GPTalk, g4f.Provider.GptForLove, g4f.Provider.Phind,
                    ])
                ),
                messages=[{"role": "user", "content": ans}],
                ignored=[""],
                timeout=300,
            )
        except Exception as exc:
            print(exc)
            await asyncio.sleep(300)
            result = await Vivid.gpt35(ans)
        return result

    @staticmethod
    async def gpt4(ans):
        logger.info(f'GPT-4 executing: {ans}')
        try:
            result = await g4f.ChatCompletion.create_async(
                model=g4f.models.gpt_4,
                messages=[{"role": "user", "content": ans}],
                timeout=300,
            )
        except Exception as exc:
            print(exc)
            await asyncio.sleep(300)
            result = await Vivid.gpt4(ans)
        return result

    # async def __call__(self, *args, **kwargs):
    #     print(f"Пожалуйста, подождите......", end='')
    #     chapters = []
    #     while len(chapters) != self.CHAPTERS_COUNT:
    #         _chapters = ""
    #         async for text in self.chapters_generator():
    #             _chapters += text
    #         chapters = re.findall(self.REQUEST_CHAPTERS_PATTERN, "".join(_chapters))
    #
    #     async for text in self.pregeneration_generator(self.book, chapters):
    #         self.pregeneration = text
    #         print(text)
    #
    #     print(f"\rПожалуйста, подождите...... [0/{self.CHAPTERS_COUNT}]", end='')
    #     tasks = []
    #     for idx, chapter in enumerate(chapters):
    #         task = asyncio.create_task(self.generate_chapter(idx, chapters))
    #         tasks.append(task)
    #     await asyncio.gather(*tasks)
    #     self.chapters.sort()
    #
    #     self.print_book()
    #     self.save_book_to_md()
    #     self.save_book_to_pdf()
    #     self.delete_md_chapters()
    #
    #     with open(f'books/book-{self.book_id}-{self.book}.md', 'r') as file:
    #         return "\n".join(file.readlines())

    async def generate_chapter(self, chapter: int, chapters: list[list]):
        chapter_text = ""
        while len(chapter_text) < self.CHAPTERS_LENGTH * 0.6 or chapter_text[-1] != '.':
            chapter_text = ""
            async for text in self.chapter_generator(chapter, chapters):
                chapter_text += text
        _uuid = uuid.uuid4()
        with open(f"books/chapter-{_uuid}-{self.book}.md", 'a') as file:
            file.write(chapter_text)
        chapters[chapter].append(_uuid)
        print(f"\rПожалуйста, подождите...... [{len(self.chapters)}/{self.CHAPTERS_COUNT}]", end='')
        # TODO: вывод прогресса в процентах: отдельная переменная для количества полностью готовых глав
        #  (кол-во готовых)*(100/(кол-во всего глав))+
        #  ((кол-во символов в неготовых)/(должно быть символов)*100)*(100/(кол-во всего глав))
        #  вроде как то так считается

    async def sections_generator(self):
        result = await self.gpt(self.REQUEST_SECTIONS.format(
            self.genre,
            self.book),
        )
        yield result

    async def generate_sections(self):
        sections = []
        while len(sections) != self.SECTIONS_COUNT:
            _sections = ""
            async for text in self.sections_generator():
                _sections += text
            sections = re.findall(self.REQUEST_CHAPTERS_PATTERN, "".join(_sections))
        return sections

    async def generate_chapters(self, section):
        chapters = []
        while len(chapters) != self.CHAPTERS_COUNT:
            _chapters = ""
            async for text in self.chapters_generator(section):
                _chapters += text
            chapters = re.findall(self.REQUEST_CHAPTERS_PATTERN, "".join(_chapters))
        return chapters

    async def chapters_generator(self, section):
        result = await self.gpt(self.REQUEST_CHAPTERS.format(
            self.genre,
            self.book,
            section,
            self.REQUEST_CHAPTERS_PATTERN),
        )
        yield result

    async def chapter_generator(self, chapter: int, chapters: list[list]):
        result = await self.gpt(
            self.REQUEST_CHAPTER.format(
                self.genre,
                self.book,
                f"{chapters[chapter][0]}. {chapters[chapter][1]}",
                self.REQUEST_CHAPTER_PATTERN,
                "\n".join(c[1] for c in chapters[:chapter + 1]),
                "".join(self.pregeneration)
            )
        )
        yield result

    async def generate_pregeneration(self):
        pregeneration = ""
        async for text in self.pregeneration_generator():
            pregeneration = text
            print(text)
        return pregeneration

    async def pregeneration_generator(self):
        result = await self.gpt(
            self.REQUEST_PREGENERATION.format(
                self.genre,
                self.book,
                "\n".join(c[1] for c in self.sections)
            )
        )
        yield result

    def print_book(self):
        print(f'\r{self.book}\n')
        print("Список глав:")
        for i, ch in enumerate(self.chapters):
            print(f"{i + 1}. {ch[0][1]}")
        print()

        for chapter in self.chapters:
            with open(f"books/chapter-{chapter[1]}-{self.book}.md", 'r') as file:
                print(chapter[0][1])
                print(*file.read().split('\n\n')[1:], sep='\n')
                print()

    def save_book_to_md(self):
        with open(f'books/book-{self.book_id}-{self.book}.md', 'a') as file:
            file.write(f"# {self.book}\n\nСписок глав:\n")
            for i, ch in enumerate(self.chapters):
                file.write(f"{i + 1}. {ch[0][1]}\n")
            file.write("\n")

            for ch in self.chapters:
                with open(f"books/chapter-{ch[1]}-{self.book}.md", 'r') as ch_file:
                    file.write(f"## {ch[0][1]}\n")
                    [file.write(f"{line}\n") for line in ch_file.read().split('\n\n')[1:]]
                    file.write('\n')

    #
    # def save_book_to_pdf(self):
    #     file = f'books/book-{self.book_id}-{self.book}.pdf'
    #     # TODO: Vyacheslav

    def delete_md_chapters(self):
        for ch in self.chapters:
            os.remove(f"books/chapter-{ch[1]}-{self.book}.md")
