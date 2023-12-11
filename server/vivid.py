import asyncio
import re

import g4f

from utils.logger import logger

from schemas import BookOfSessionBaseWithExtra

from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import simpleSplit
from reportlab.lib.pagesizes import letter


class Vivid:
    """
    Vivid(яркий) - просто слово, состоящее из 3 различных букв
    V - Вячеслав
    I - Ибро
    D - Джамал
    """

    CHAPTER_OR_SECTION_PATTERN = r'(\d+)\.\s(.*)'
    CHAPTER_TEXT_PATTERN = "Текст главы"

    REQUEST_CHAPTERS = """
    Действуй в роли писателя в жанре "{0}"! Пиши на русском языке!
    Сгенерируй названия {3} штук различных глав для раздела "{2}" книги "{1}".
    Не указывай сайты-источники!
    В конце предложений ставь "."!
    Отвечай строго по шаблону ниже и больше никак!
    
    Номер. Название главы
    """

    REQUEST_SECTIONS = """
    Действуй в роли писателя в жанре "{0}"! Пиши на русском языке!
    Сгенерируй названия {2} штук различных разделов книги "{1}".
    Не указывай сайты-источники!
    В конце предложений ставь "."!
    Отвечай строго по шаблону ниже и больше никак!

    Номер. Название раздела
    """

    REQUEST_PREGENERATION = """
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

    REQUEST_CHAPTER = """
    Действуй в роли писателя в жанре "{0}"! Пиши на русском языке!
    Сгенерируй текст размером {7} символов главы "{3}" раздела "{2}" книги "{1}".
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

    @staticmethod
    def gpt(ans, v):
        if str(v) in ["3.5", "3.0", "3"]:
            return Vivid.gpt35(ans)
        elif str(v) == "3.7":
            return Vivid.gpt35_andor_gpt4(ans)
        elif str(v) in ["4.0", "4"]:
            return Vivid.gpt4(ans)
        else:
            raise ValueError(f'Invalid GPT Version - {v}')

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
    async def gpt35_andor_gpt4(ans):
        ans = ans.replace("\t", "").replace("  ", " ").replace("  ", " ").replace("   ", "")
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
                        g4f.Provider.Liaobots, g4f.Provider.ChatAnywhere, g4f.Provider.Chatgpt4Online,
                        g4f.Provider.ChatgptDemoAi, g4f.Provider.OnlineGpt, g4f.Provider.FakeGpt,
                        g4f.Provider.FreeGpt, g4f.Provider.Koala, g4f.Provider.ChatgptNext,
                        g4f.Provider.ChatgptAi, g4f.Provider.Vercel,
                    ])
                ),
                messages=[{"role": "user", "content": ans}],
                ignored=[""],
                timeout=300,
            )
        except Exception as exc:
            logger.error(exc)
            await asyncio.sleep(300)
            result = await Vivid.gpt35_andor_gpt4(ans)
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

    @staticmethod
    async def generate_chapter(book: BookOfSessionBaseWithExtra, section: str, chapter: int, chapters: list[list]):
        chapter_text = ""
        while len(chapter_text) < book.chapters_length * 0.6 or chapter_text[-1] != '.':
            if chapter_text:
                chapter_text = chapter_text
                logger.error(f"Что-то пошло не так... перезапуск. ["
                             f"len={len(chapter_text) >= book.chapters_length * 0.6}, "
                             f".={chapter_text[-1] == '.'}]")
            chapter_text = ""
            async for text in Vivid.chapter_generator(book, section, chapter, chapters):
                chapter_text += text
            temp_chapter_text = re.findall(r'```([\s\S]*?)```', chapter_text)
            if temp_chapter_text and len(temp_chapter_text[0]) > book.chapters_length * 0.5:
                chapter_text = temp_chapter_text[0].strip()
            chapter_text = re.sub(r'\nГлава .?\d.*', '', chapter_text)
            chapter_text = re.sub(r'\nЭта глава .*', '', chapter_text)
            # chapter_text = re.sub(r'Эта глава посвящена.*', '', chapter_text)  ### проверка на уничтожение
            # chapter_text = re.sub(r'В (этой|следующей) главе.*', '', chapter_text)  ### проверка на уничтожение
            chapter_text = re.sub(r'\nВ этой главе .*', '', chapter_text)
            chapter_text = re.sub(r'\nВ следующей главе .*', '', chapter_text)
            chapter_text = re.sub(r'(^(?!Глава\n).*?\.)\s*(.*)', '', chapter_text.strip()).strip()
            chapter_text = re.sub(r'[Кк]онец главы.*', '', chapter_text.strip()).strip()
            chapter_text = re.sub(r'Эта глава.*', '', chapter_text.strip()).strip()
            chapter_text = re.sub('<.*?>', '', chapter_text.strip()).strip()
            chapter_text = re.sub(r'#{2,}', '', chapter_text.strip()).strip()
            chapter_text = re.sub(r'\*{2,}', '', chapter_text.strip()).strip()
            if '\n\n' in chapter_text:
                chapter_text = chapter_text.replace('\n\n', '\n\n\u2800\n\n')
            else:
                chapter_text = chapter_text.replace('\n', '\n\n\u2800\n\n')
            logger.info(f"Generated chapter: {chapter_text}")

        return chapter_text

    @staticmethod
    async def sections_generator(book: BookOfSessionBaseWithExtra):
        result = await Vivid.gpt(
            Vivid.REQUEST_SECTIONS.format(
                book.genre,
                book.book,
                book.sections_count),
            book.v,
        )
        yield result

    @staticmethod
    async def generate_sections(book: BookOfSessionBaseWithExtra):
        sections = []
        while len(sections) != book.sections_count:
            _sections = ""
            async for text in Vivid.sections_generator(book):
                _sections += text
            sections = re.findall(Vivid.CHAPTER_OR_SECTION_PATTERN, "".join(_sections))
            logger.info(f"Generated sections: {sections}")
        return sections

    @staticmethod
    async def generate_chapters(book: BookOfSessionBaseWithExtra, section):
        chapters = []
        while len(chapters) != book.chapters_count:
            _chapters = ""
            async for text in Vivid.chapters_generator(book, section):
                _chapters += text
            chapters = re.findall(Vivid.CHAPTER_OR_SECTION_PATTERN, "".join(_chapters))
            logger.info(f"Generated chapters for section {section}: {chapters}")
        return chapters

    @staticmethod
    async def chapters_generator(book: BookOfSessionBaseWithExtra, section):
        result = await Vivid.gpt(
            Vivid.REQUEST_CHAPTERS.format(
                book.genre,
                book.book,
                section,
                book.chapters_count
            ),
            book.v,
        )
        yield result

    @staticmethod
    async def chapter_generator(book: BookOfSessionBaseWithExtra, section: str, chapter: int, chapters: list[list]):
        result = await Vivid.gpt(
            Vivid.REQUEST_CHAPTER.format(
                book.genre,
                book.book,
                section,
                f"{chapters[chapter][0]}. {chapters[chapter][1]}",
                Vivid.CHAPTER_TEXT_PATTERN,
                "\n".join(c[1] for c in chapters[:chapter]) or "Это первая глава",
                "".join(book.pregeneration),
                book.chapters_length,
            ),
            book.v,
        )
        yield result

    @staticmethod
    async def generate_pregeneration(book: BookOfSessionBaseWithExtra):
        pregeneration = ""
        while len(pregeneration) < 50:
            pregeneration = ""
            async for text in Vivid.pregeneration_generator(book):
                pregeneration += text
        logger.info(f"Generated pregeneration: {pregeneration}")
        return pregeneration

    @staticmethod
    async def pregeneration_generator(book: BookOfSessionBaseWithExtra):
        result = await Vivid.gpt(
            Vivid.REQUEST_PREGENERATION.format(
                book.genre,
                book.book,
                "\n".join(c[1] for c in book.sections_list)
            ),
            book.v,
        )
        yield result

    @staticmethod
    def save_book_to_file(book):
        pdf_file_path = f'books/book-{book.id}-{book.book}.pdf'
        c = canvas.Canvas(pdf_file_path, pagesize=letter)
        c.setTitle(book.book)

        font_name = "DejaVuSerif"
        pdfmetrics.registerFont(TTFont(font_name, f'{font_name}.ttf'))

        # Задаем размеры страницы
        width, height = letter

        # Задаем Размеры шрифтов
        font_sizes = {
            "title": 28,
            "genre": 14,
            "table_title": 16,
            "section_title": 14,
            "chapter_text": 14,
            "chapter_title": 12,
        }

        line_spacing = {
            "section_title": 14,
            "chapter_title": 12,
            "chapter_text": 12,
        }

        # Добавляем список разделов и глав на титульный лист
        c.setFont(font_name, font_sizes["title"] * font_sizes["title"] / len(book.book))
        # c.drawString(50, height - 20, f"{book.book}")
        c.drawCentredString(width // 2, height // 2 + 60, f"{book.book}")
        c.setFont(font_name, font_sizes["genre"] * font_sizes["genre"] / len(book.genre))
        c.drawCentredString(width // 2, height // 2 + 30, f"{book.genre}")
        c.setFont(font_name, font_sizes["chapter_title"])
        c.drawString(30, 50, f"Сгенерировано AI")
        c.drawString(30, 30, f"Авторы: Гаджиявов Джамал, Валуевич Вячеслав, Ибрагим Баро")
        c.showPage()
        c.setFont(font_name, font_sizes["table_title"])
        c.drawString(50, height - 50, "Содержание:")
        y_position = height - 70

        for idx, section in enumerate(book.sections_list):
            if y_position < 140:
                c.showPage()
                c.setFont(font_name, font_sizes["table_title"])
                c.drawString(50, height - 50, "Содержание:")
                y_position = height - 70
            y_position -= line_spacing["section_title"]
            c.setFont(font_name, font_sizes["section_title"])
            section_lines = f"Раздел №{idx + 1}. {section[1]}"
            sec_lines = simpleSplit(section_lines, font_name, font_sizes["section_title"], width - 100)
            for line in sec_lines:
                c.drawString(70, y_position, line)
                y_position -= line_spacing["chapter_title"]  # crutch (it's not chapter title)
            # c.drawString(70, y_position, f"Раздел №{idx + 1}. {section[1]}")

            for i, ch in enumerate(book.chapters[section[1]]):
                y_position -= line_spacing["chapter_title"]
                c.setFont(font_name, font_sizes["chapter_title"])
                chapter_lines = f"{i + 1}. {ch[1]}"
                ch_lines = simpleSplit(chapter_lines, font_name, font_sizes["chapter_title"], width - 100)

                if y_position >= 100:
                    for line in ch_lines:
                        c.drawString(90, y_position, line)
                        y_position -= line_spacing["chapter_title"]
                else:
                    c.showPage()
                    c.setFont(font_name, font_sizes["table_title"])
                    c.drawString(50, height - 50, "Содержание:")
                    y_position = height - 70

                    c.setFont(font_name, font_sizes["section_title"])
                    for line in sec_lines:
                        c.drawString(70, y_position, line)
                        y_position -= line_spacing["chapter_title"]
                    # c.drawString(70, y_position, f"Раздел №{idx + 1}. {section[1]}")
                    y_position -= line_spacing["section_title"]
                    c.setFont(font_name, font_sizes["chapter_title"])
                    for line in ch_lines:
                        c.drawString(90, y_position, line)
                        y_position -= line_spacing["chapter_title"]
                    # c.drawString(90, y_position, f"{i + 1}. {ch[1]}")

        # страницы с главами и их содержанием
        for idx, section in enumerate(book.sections_list):
            c.showPage()
            y_position = height - 70
            c.setFont(font_name, font_sizes["section_title"] + 2)
            section_lines = f"Раздел №{idx + 1}. {section[1]}"
            sec_lines = simpleSplit(section_lines, font_name, font_sizes["section_title"] + 2, width - 100)
            for line in sec_lines:
                c.drawString(70, y_position, line)
                y_position -= line_spacing["chapter_title"]  # crutch
            # c.drawString(70, y_position, f"Раздел №{idx + 1}. {section[1]}")

            for i, ch in enumerate(book.chapters[section[1]]):
                y_position -= line_spacing["chapter_title"]
                if y_position < 150:
                    c.showPage()
                    y_position = height - 70
                c.setFont(font_name, font_sizes["chapter_title"] + 2)
                chapter_lines = f"{i + 1}. {ch[1]}"
                ch_lines = simpleSplit(chapter_lines, font_name, font_sizes["chapter_title"] + 2, width - 100)
                for line in ch_lines:
                    c.drawString(90, y_position, line)
                    y_position -= 14
                # c.drawString(80, y_position, f"{i + 1}. {ch[1]}")

                if len(ch) > 2:  # Проверяем наличие текста главы
                    chapter = '\n'.join(ch[2].split('\n')[0:]).strip()
                    lines = simpleSplit(chapter, font_name, font_sizes["chapter_text"], width - 100)

                    y_position -= line_spacing["chapter_title"]
                    for line in lines:
                        y_position -= line_spacing["chapter_text"]
                        if y_position < 100:
                            c.showPage()
                            y_position = height - 70
                        c.setFont(font_name, font_sizes["chapter_title"])
                        c.drawString(90, y_position, line)
                    y_position -= line_spacing["chapter_title"]

        c.save()
        logger.info(f"Книга {book.book}({book.id}) сохранена в файл {pdf_file_path}")
        return f"/{pdf_file_path}"
