import asyncio
import re

import g4f
import uuid

from logger import logger


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
            sections_count=3,
            chapters_count=4,
            chapters_length=1500,
            v: int | float | str = "3.7",
            genre="",
            book=""
    ):
        if sections_count < 3:
            chapters_count = 3
            logger.warning('Кол-во разделов не может быть меньше 3, поэтому установлено как 3')
        elif sections_count > 12:
            chapters_count = 12
            logger.warning('Кол-во разделов не может быть больше 12, поэтому установлено как 12')

        if chapters_count < 4:
            chapters_count = 4
            logger.warning('Кол-во глав в разделе не может быть меньше 4, поэтому установлено как 4')
        elif chapters_count > 40:
            chapters_count = 40
            logger.warning('Кол-во глав в разделе не может быть больше 40, поэтому установлено как 40')

        if chapters_length < 300:
            chapters_length = 300
            logger.warning('Кол-во символов в главе не может быть меньше 300, поэтому установлено как 300')
        elif chapters_length > 4000:
            chapters_length = 4000
            logger.warning('Кол-во символов в главе не может быть больше 4000, поэтому установлено как 4000')

        self.CHAPTERS_COUNT = chapters_count
        self.CHAPTERS_LENGTH = chapters_length
        self.REQUEST_CHAPTERS = """
        Действуй в роли писателя в жанре "{0}"! Пиши на русском языке!
        Сгенерируй названия """ + str(self.CHAPTERS_COUNT) + """ штук различных глав для раздела "{2}" книги "{1}".
        Не указывай сайты-источники!
        В конце предложений ставь "."!
        Отвечай строго по шаблону ниже и больше никак!

        Номер. Название главы
        """

        self.SECTIONS_COUNT = sections_count
        self.REQUEST_SECTIONS = """
        Действуй в роли писателя в жанре "{0}"! Пиши на русском языке!
        Сгенерируй названия """ + str(self.SECTIONS_COUNT) + """ штук различных разделов книги "{1}".
        Не указывай сайты-источники!
        В конце предложений ставь "."!
        Отвечай строго по шаблону ниже и больше никак!

        Номер. Название раздела
        """  # TODO

        self.REQUEST_PREGENERATION = """
        Действуй в роли писателя в жанре "{0}"! Пиши на русском языке!
        Сгенерируй названия основных сюжетных мест и имён героев для книги "{1}".
        Названия разделов этой книги:
        {2}

        Не указывай сайты-источники!
        В конце предложений ставь "."!
        Ответь строго по шаблону ниже:
        Основные сюжетные места/темы/имена/названия мест/имена героев(если уместно в данной книге):
        ...

        {1} - книга о ...
        """
        self.REQUEST_CHAPTER = """
        Действуй в роли писателя в жанре "{0}"! Пиши на русском языке!
        Сгенерируй текст размером """ + str(self.CHAPTERS_LENGTH) + """ символов главы "{3}" раздела "{2}" книги "{1}".
        Названия прошлых глав(используй для правильной последовательности повествования):
        {5}

        Важная информация:
        После конца главы обязательно напиши дословно: "Конец главы. Эта глава была о" + о чем была глава!
        {6}
        В конце предложений ставь "."!
        Не указывай сайты-источники!

        Не делай отсылок к прошлым или будущим главам. Не пиши ничего о том, что будет в следующей главе.

        Отвечай строго по шаблону ниже и больше никак!

        "Глава {3}"
        {4}   
        """
        if str(v) == "3.5":
            self.gpt = self.gpt35
        elif str(v) == "3.7":
            self.gpt = self.gpt37
        elif str(v) == "4.0":
            self.gpt = self.gpt4
        else:
            raise ValueError(f'Invalid GPT Version - {v}')
        self.genre = genre
        self.chapters = {}
        self.sections = []
        self.book = book
        self.book_id = uuid.uuid4()
        self.pregeneration = ""

    @staticmethod
    async def gpt35(ans):
        ans = ans.replace("  ", " ").replace("  ", " ").replace("\t", "").replace("   ", "")
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
            logger.error(exc)
            await asyncio.sleep(300)
            result = await Vivid.gpt35(ans)
        logger.info(f'GPT-3.5 result:\n{result}')
        return result

    @staticmethod
    async def gpt37(ans):
        ans = ans.replace("  ", " ").replace("  ", " ").replace("\t", "").replace("   ", "")
        logger.info(f'GPT-3.5/4 executing: {ans}')
        try:
            result = await g4f.ChatCompletion.create_async(
                model=g4f.models.Model(
                    name='gpt-3.5-or-gpt-4',
                    base_provider='openai',
                    best_provider=g4f.Provider.RetryProvider([
                        g4f.Provider.ChatgptX, g4f.Provider.GptGo, g4f.Provider.You,
                        g4f.Provider.NoowAi, g4f.Provider.GPTalk, g4f.Provider.GptForLove,
                        g4f.Provider.Phind, g4f.Provider.Bing, g4f.Provider.GeekGpt,
                    ])
                ),
                messages=[{"role": "user", "content": ans}],
                ignored=[""],
                timeout=300,
            )
        except Exception as exc:
            logger.error(exc)
            await asyncio.sleep(300)
            result = await Vivid.gpt35(ans)
        logger.info(f'GPT-3.5/4 result:\n{result}')
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
            logger.error(exc)
            await asyncio.sleep(300)
            result = await Vivid.gpt4(ans)
        logger.info(f'GPT-4 result:\n{result}')
        return result

    async def generate_chapter(self, section: str, chapter: int, chapters: list[list]):
        chapter_text = ""
        while len(chapter_text) < self.CHAPTERS_LENGTH * 0.6 or chapter_text[-1] != '.':
            if chapter_text:
                chapter_text = chapter_text
                logger.error(f"Что-то пошло не так... перезапуск. ["
                             f"len={len(chapter_text) >= self.CHAPTERS_LENGTH * 0.6}, "
                             f".={chapter_text[-1] == '.'}]")
            chapter_text = ""
            async for text in self.chapter_generator(section, chapter, chapters):
                chapter_text += text
            chapter_text = re.sub(r'[Кк]онец главы.*', '', chapter_text.strip()).strip()
            logger.info(f"Generated chapter: {chapter_text}")

        return chapter_text

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
            logger.info(f"Generated sections: {sections}")
        return sections

    async def generate_chapters(self, section):
        chapters = []
        while len(chapters) != self.CHAPTERS_COUNT:
            _chapters = ""
            async for text in self.chapters_generator(section):
                _chapters += text
            chapters = re.findall(self.REQUEST_CHAPTERS_PATTERN, "".join(_chapters))
            logger.info(f"Generated chapters for section {section}: {chapters}")
        return chapters

    async def chapters_generator(self, section):
        result = await self.gpt(self.REQUEST_CHAPTERS.format(
            self.genre,
            self.book,
            section,
            self.REQUEST_CHAPTERS_PATTERN),
        )
        yield result

    async def chapter_generator(self, section: str, chapter: int, chapters: list[list]):
        result = await self.gpt(
            self.REQUEST_CHAPTER.format(
                self.genre,
                self.book,
                section,
                f"{chapters[chapter][0]}. {chapters[chapter][1]}",
                self.REQUEST_CHAPTER_PATTERN,
                "\n".join(c[1] for c in chapters[:chapter]) or "Это первая глава",
                "".join(self.pregeneration)
            )
        )
        yield result

    async def generate_pregeneration(self):
        pregeneration = ""
        async for text in self.pregeneration_generator():
            pregeneration = text
        logger.info(f"Generated pregeneration: {pregeneration}")
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

    def save_book_to_file(self):
        # temporarily, and then it will save books in pdf
        # TODO
        with open(f'books/book-{self.book_id}-{self.book}.md', 'a') as file:
            file.write(f"## {self.book}\n\nСодержание:\n")
            for idx, section in enumerate(self.sections):
                file.write(f"#### Раздел №{idx + 1}. {section[1]}\n")
                for i, ch in enumerate(self.chapters[section[1]]):
                    file.write(f"       {i + 1}. {ch[1]}\n")
            file.write("\n")

            for section in self.sections:
                file.write(f"## {section[1]}\n")
                for ch in self.chapters[section[1]]:
                    file.write(f"### {ch[1]}\n")
                    chapter = [[]]
                    for sentence in ch[2].split('\n\n')[1:]:
                        for word in sentence.split():
                            chapter[-1].append(word)
                            if sum(len(word) for word in chapter[-1]) > 80:
                                chapter.append([])
                    for line in chapter:
                        for word in line:
                            file.write(f"{word} ")
                        file.write('\n')
                    file.write('\n')
            logger.info(f"Книга {self.book}({self.book_id}) сохранена в файл")
