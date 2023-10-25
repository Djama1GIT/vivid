import asyncio
import re

import g4f
import uuid


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
            chapters_count=4,
            chapters_length=500,
            v: int | float | str = "3.5",
            genre="не указан",
            book="не указан"
    ):
        if chapters_count < 4:
            chapters_count = 4
            print('Кол-во глав не может быть меньше 4, поэтому установлено как 4')
        if chapters_length < 300:
            chapters_length = 300
            print('Кол-во символов в главе не может быть меньше 300, поэтому установлено как 300')
        self.CHAPTERS_COUNT = chapters_count
        self.CHAPTERS_LENGTH = chapters_length
        self.REQUEST_CHAPTERS = """Действуй в роли писателя в жанре "{0}"! Пиши книгу на русском языке!
           Сгенерируй названия """ + str(self.CHAPTERS_COUNT) + """" штук глав для книги "{1}".
           Отвечай строго по шаблону ниже и больше никак!

           Номер. Название главы

           """

        self.REQUEST_CHAPTER = """Действуй в роли писателя в жанре "{0}"! Пиши книгу на русском языке!
           Сгенерируй текст размером """ + str(self.CHAPTERS_LENGTH) + """ символов главы "{2}" для книги "{1}".
           Названия прошлых глав(используй для правильной последовательности повествования):
           {4}

           Не делай отсылок к прошлым или будущим главам. Не пиши ничего о том, что будет в следующей главе.

           Отвечай строго по шаблону ниже и больше никак!

           "Глава {2}"
           {3}   
           """
        if str(v) in ["3.5", "3"]:
            self.gpt = self.gpt35
        elif str(v) == '4':
            self.gpt = self.gpt4
        else:
            raise ValueError('Invalid GPT Version')
        self.genre = genre
        self.chapters = []
        self.book = book

    @staticmethod
    async def gpt35(ans):
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
                timeout=180,
            )
        except Exception as exc:
            print(exc)
            await asyncio.sleep(300)
            result = await Vivid.gpt35(ans)
        return result

    @staticmethod
    async def gpt4(ans):
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

    async def __call__(self, *args, **kwargs):
        print(f"Пожалуйста, подождите......", end='')
        chapters = []
        while len(chapters) != self.CHAPTERS_COUNT:
            _chapters = ""
            async for text in self.chapters_generator(self.book):
                _chapters += text
            chapters = re.findall(self.REQUEST_CHAPTERS_PATTERN, "".join(_chapters))
        print(f"\rПожалуйста, подождите...... [0/{self.CHAPTERS_COUNT}]", end='')
        tasks = []
        for idx, chapter in enumerate(chapters):
            task = asyncio.create_task(self.generate_chapter(self.book, idx, chapters))
            tasks.append(task)
        await asyncio.gather(*tasks)
        self.chapters.sort()

        self.print_book()
        self.save_book_to_md()

    async def generate_chapter(self, book, chapter: int, chapters: list[tuple[int, str]]):
        chapter_text = ""
        while len(chapter_text) < self.CHAPTERS_LENGTH * 0.6 or chapter_text[-1] != '.':
            chapter_text = ""
            async for text in self.chapter_generator(book, chapter, chapters):
                chapter_text += text
        self.chapters += [(chapters[chapter], chapter_text)]
        print(f"\rПожалуйста, подождите...... [{len(self.chapters)}/{self.CHAPTERS_COUNT}]", end='')
        # TODO: вывод прогресса в процентах: отдельная переменная для количества полностью готовых глав
        # (кол-во готовых)*(100/(кол-во всего глав))+
        # ((кол-во символов в неготовых)/(должно быть символов)*100)*(100/(кол-во всего глав))
        # вроде как то так считается

    async def chapters_generator(self, book):
        result = await self.gpt(self.REQUEST_CHAPTERS.format(
            self.genre,
            book,
            self.REQUEST_CHAPTERS_PATTERN),
        )
        yield result

    async def chapter_generator(self, book, chapter: int, chapters: list[tuple[int, str]]):
        result = await self.gpt(self.REQUEST_CHAPTER.format(
            self.genre,
            book,
            f"{chapters[chapter][0]}. {chapters[chapter][1]}",
            self.REQUEST_CHAPTER_PATTERN,
            "\n".join(c[1] for c in chapters[:chapter + 1]))
        )
        yield result

    def print_book(self):
        print(f'\r{self.book}\n')
        print("Список глав:")
        for i, ch in enumerate(self.chapters):
            print(f"{i + 1}. {ch[0][1]}")
        print()

        for chapter in self.chapters:
            print(chapter[0][1])
            print(*chapter[1].split('\n\n')[1:], sep='\n')
            print()

    def save_book_to_md(self):
        _uuid = uuid.uuid4()

        with open(f'books/{_uuid}-{self.book}.txt', 'a') as file:
            file.write(f"# {self.book}\n\nСписок глав:\n")
            for i, ch in enumerate(self.chapters):
                file.write(f"{i + 1}. {ch[0][1]}\n")
            file.write("\n")

            for ch in self.chapters:
                file.write(f"## {ch[0][1]}\n")
                [file.write(f"{line}\n") for line in ch[1].split('\n\n')[1:]]
                file.write('\n')


# vivid = Vivid(chapters_count=int(input('Введите количество глав: ')),
#               chapters_length=int(input('Введите количество символов в одной главе: ')),
#               v=input('Введите версию GPT: '),
#               genre=input('Введите название жанра: '),
#               book=input("Введите название книги: "))

vivid = Vivid(chapters_count=4,
              chapters_length=300,
              v=3.5,
              genre="Фэнтези",
              book="жил был сдох")

asyncio.run(vivid())
