import asyncio
import re

import g4f


class Vivid:
    """
    Vivid(яркий) - просто слово, состоящее из 3 различных букв
    V - Вячеслав
    I - Ибро
    D - Джамал
    """
    CHAPTERS_COUNT = 4
    REQUEST_CHAPTERS_PATTERN = r'(\d+)\.\s(.*)'
    REQUEST_CHAPTERS = """Действуй в роли писателя в жанре "{0}"! Пиши книгу на русском языке!
    Сгенерируй названия """ + str(CHAPTERS_COUNT) + """" штук глав для книги "{1}".
    Отвечай строго по шаблону ниже и больше никак!
        
    Номер. Название главы
    
    """

    CHAPTERS_LENGTH = 500
    REQUEST_CHAPTER_PATTERN = "Текст главы"
    REQUEST_CHAPTER = """Действуй в роли писателя в жанре "{0}"! Пиши книгу на русском языке!
    Сгенерируй текст размером """ + str(CHAPTERS_LENGTH) + """ символов главы "{2}" для книги "{1}".
    Названия прошлых глав(используй для правильной последовательности повествования):
    {4}
    
    Не делай отсылок к прошлым или будущим главам. Не пиши ничего о том, что будет в следующей главе.
    
    Отвечай строго по шаблону ниже и больше никак!
    
    "Глава {2}"
    {3}   
    """

    def __init__(self, v="3.5", genre="не указан"):
        if v in ["3.5", "3"]:
            self.gpt = self.gpt35
        elif v == '4':
            self.gpt = self.gpt4
        else:
            raise ValueError('Invalid GPT Version')
        self.genre = genre
        self.chapters = []

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
                ignored=[""]
            )
        except Exception as exc:
            print(exc)
            await asyncio.sleep(5)
            result = await Vivid.gpt35(ans)
        return result

    @staticmethod
    async def gpt4(ans):
        try:
            result = await g4f.ChatCompletion.create_async(
                model=g4f.models.gpt_4,
                messages=[{"role": "user", "content": ans}],
            )
        except Exception as exc:
            print(exc)
            await asyncio.sleep(5)
            result = await Vivid.gpt4(ans)
        return result

    async def __call__(self, *args, **kwargs):
        print()
        print("Пожалуйста, подождите......", end='')
        chapters = []
        while len(chapters) != self.CHAPTERS_COUNT:
            _chapters = ""
            async for text in self.chapters_generator(args[0]):
                _chapters += text
            chapters = re.findall(self.REQUEST_CHAPTERS_PATTERN, "".join(_chapters))
        tasks = []
        for idx, chapter in enumerate(chapters):
            task = asyncio.create_task(self.generate_chapter(args[0], idx, chapters))
            tasks.append(task)
        await asyncio.gather(*tasks)
        self.chapters.sort()

    async def generate_chapter(self, book, chapter: int, chapters: list[tuple[int, str]]):
        chapter_text = ""
        while len(chapter_text) < 300 or chapter_text[-1] != '.':
            chapter_text = ""
            async for text in self.chapter_generator(book, chapter, chapters):
                chapter_text += text
        self.chapters += [(chapters[chapter], chapter_text)]

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


vivid = Vivid('3.5', input('Введите название жанра: '))
asyncio.run(vivid(input("Введите название книги: ")))
print('\r', end='')
for chapter in vivid.chapters:
    print(chapter[0][1])
    print(*chapter[1].split('\n\n')[1:], sep='\n')
    print()
