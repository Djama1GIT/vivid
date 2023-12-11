import React, { useState, useEffect, useRef } from 'react';
import styles from './App.css';

import { changeURLParam } from './Utils';

function App() {
  const [step, setStep] = useState(0);
  const [sectionsCount, setSectionsCount] = useState(3);
  const [sections, setSections] = useState([]);
  const [chaptersCount, setChaptersCount] = useState(4);
  const [chaptersLength, setChaptersLength] = useState(1500);
  const [gptVersion, setGptVersion] = useState("3.7");
  const [genre, setGenre] = useState("");
  const [bookName, setBookName] = useState("");
  const [pregeneration, setPregeneration] = useState("");
  const [alreadyGeneratedChaptersCount, setAlreadyGeneratedChaptersCount] = useState(0);
  const [bookLink, setBookLink] = useState("");

  const [errorMessage, setErrorMessage] = useState("");

  const [socketState, setSocketState] = useState(true);
  const CONNECTION_CLOSED = "Соединение с сервером потеряно. Попробуйте перезагрузить страницу.";

  const urlParams = new URLSearchParams(window.location.search);


  // WebSocket instance variable
  const socketRef = useRef(null);

  useEffect(() => {
    socketRef.current = new WebSocket(`ws://localhost:${process.env.REACT_APP_WEBSOCKET_PORT}/ws/`);

    // Connection opened
    socketRef.current.addEventListener('open', function (event) {
      console.log("Connection opened");
      setSocketState(true);
      setErrorMessage("");
      socketRef.current.send(JSON.stringify({
        session: urlParams.get('cache'),
      }));
    });

    // Listen for messages
    socketRef.current.addEventListener('message', function (event) {
      const data = JSON.parse(event.data);
      if (data.code === -1) {
        changeURLParam('cache', data.session);
      } else if (data.code === 1) {
        setGenre(data.genre);
        setBookName(data.bookName);
        setChaptersCount(data.chaptersCount);
        setChaptersLength(data.chaptersLength);
        setSectionsCount(data.sectionsCount);
        setGptVersion(data.gptVersion);
        setPregeneration(data.pregeneration);
        setBookLink(data.link)

        // set sections and chapters
        setSections(data.sections.map(([id, title]) => {
          return {
            name: title,
            chapters: data.chapters[title] ? data.chapters[title] : []
          }
        }));
      } else if (data.code === 2) {
        setSections(data.sections.map(([id, title]) => (
          {
            name: title,
            chapters: [],
          }
        )));
      } else if (data.code === 3) {
        setSections((prevSections) => {
          return prevSections.map((section) => {
            if (section.name === data.section) {
              return {
                ...section,
                chapters: data.chapters,
              };
            } else {
              return section;
            }
          });
        });
      } else if (data.code === 4) {
        setPregeneration(data.pregeneration)
      } else if (data.code === 5) {
        setSections((prevSections) => {
         return prevSections.map((section) => {
           if (section.name === data.section) {
             return {
               ...section,
               chapters: section.chapters.map((chapter, index) => {
                 if (index === data.chapter) {
                   return [chapter[0], chapter[1], data.chapter_text];
                 } else {
                   return chapter;
                 }
               }),
             };
           } else {
             return section;
           }
         });
       });
     } else if (data.code === 6) {
        setBookLink(data.link);
     } else if (data.code === 418) {
        setErrorMessage(data.message);
     }
     updateStep();
    });


    // Connection closed
    socketRef.current.addEventListener('close', function (event) {
      console.log('Connection closed');
      setSocketState(false);
    });

    // Connection error
    socketRef.current.addEventListener('error', function (event) {
      console.error('WebSocket error: ', event);
    });

    // Clean up function
    return () => {
      socketRef.current.close();
    };
  }, []);

  const updateStep = () => {
    let temp_step = 1
    if ( sections[0] && temp_step >= 1 ) {
      temp_step = 2;
    }
    if ( sections.some((section) => section.chapters.length > 0) && temp_step >= 2 ) {
      temp_step = 3;
    }
    if ( pregeneration && temp_step >= 3 ) {
      temp_step = 4;
    }
    let alreadyGenerated = 0;
    for ( const section of sections ) {
        for ( const chapter of section.chapters ) {
            if ( chapter.length > 2 ) {
                alreadyGenerated += 1;
            }
        }
    }
    if ( alreadyGenerated > 0 && temp_step >= 4) {
        temp_step = 5
    }
    setAlreadyGeneratedChaptersCount(alreadyGenerated);
    if (alreadyGenerated === chaptersCount * sectionsCount && temp_step >= 5) {
        temp_step = 5.1
    }
    if (bookLink && temp_step >= 5.1) {
        temp_step = 5.3
    }
    setStep(temp_step);
    setTimeout(() => {
      window.scrollTo({
        top: document.body.scrollHeight,
        behavior: 'smooth'
      });
    }, 100);
  };

  useEffect(() => {
    updateStep();
  }, [sections, pregeneration, bookLink]);

  useEffect(() => {
    if (!socketState) {
      setErrorMessage(socketState ? "" : (errorMessage ? errorMessage : CONNECTION_CLOSED));
    }
  }, [socketState]);

  const handleButtonClick = () => {
    socketRef.current.send(JSON.stringify({
        cmd: "create_or_update_vivid",
        sectionsCount,
        chaptersCount,
        chaptersLength,
        gptVersion,
        genre,
        bookName
    }));
    socketRef.current.send(JSON.stringify({
        cmd: "generate_sections",
    }));
    setStep(1.5);
  };

  const handleSectionsButtonClick = () => {
    const hasDuplicateSections = sections.some((currentSection, index) => {
      return sections.some((section, i) => i !== index && section.name === currentSection.name);
    });

    if (hasDuplicateSections) {
      const duplicateSections = sections.filter((currentSection, index) => {
        return sections.some((section, i) => i !== index && section.name === currentSection.name);
      });
      console.log(duplicateSections);
      const section1Index = sections.indexOf(duplicateSections[0]);
      const section2Index = sections.indexOf(duplicateSections[1]);

      const section1Id = `section-${section1Index + 1}`;
      const section2Id = `section-${section2Index + 1}`;
      const section1Element = document.getElementById(section1Id);
      const section2Element = document.getElementById(section2Id);

      section1Element.classList.add("flash");
      section2Element.classList.add("flash");

      setTimeout(() => {
        section1Element.classList.remove("flash");
        section2Element.classList.remove("flash");
      }, 1000);

      return;
    }

    socketRef.current.send(JSON.stringify({
        cmd: "confirm_sections",
        sections: sections,
    }));
    setStep(2.5);
  };

const handleChaptersButtonClick = () => {
  const duplicateChapters = [];

  sections.forEach((currentSection, sectionIndex) => {
    const chapters = currentSection.chapters.map((chapter) => chapter[1]);

    chapters.forEach((chapter, chapterIndex) => {
      const chapterOccurrences = chapters.filter((c) => c === chapter);

      if (chapterOccurrences.length > 1) {
        duplicateChapters.push({
          sectionIndex: sectionIndex,
          chapterIndex: chapterIndex
        });
      }
    });
  });

  if (duplicateChapters.length > 0) {
    duplicateChapters.forEach((duplicateChapter) => {
      const sectionIndex = duplicateChapter.sectionIndex;
      const chapterIndex = duplicateChapter.chapterIndex;

      const sectionId = `section-${sectionIndex + 1}`;
      const chapterId = `sections-${sectionIndex + 1}-chapter-${chapterIndex + 1}`;

      const sectionElement = document.getElementById(sectionId);
      const chapterElement = document.getElementById(chapterId);

      sectionElement.classList.add("flash");
      chapterElement.classList.add("flash");

      setTimeout(() => {
        sectionElement.classList.remove("flash");
        chapterElement.classList.remove("flash");
      }, 1000);
    });
  } else {
    socketRef.current.send(JSON.stringify({
      cmd: "confirm_chapters",
      sections: sections,
    }));
    setStep(3.5);
  }
};

  const handleDescriptionButtonClick = () => {
    socketRef.current.send(JSON.stringify({
        cmd: "generate_book",
        pregeneration: pregeneration,
    }));
    setStep(5);
  };

  const handleConfirmResultsButtonClick = () => {
    socketRef.current.send(JSON.stringify({
        cmd: "assemble_to_pdf",
    }));
    setStep(5.2);
  };


  return (
  <>
    {!errorMessage ? <div className="App">
      <a className="logo" href="/">Vivid</a>
      <p className="step step1">1</p>
      <div className="form" disabled={step > 1}>
        <div className="selector">
            <input type="number" id="sections_count" value={sectionsCount} onChange={(e) => setSectionsCount(e.target.value)} placeholder="Количество разделов" min="4" max="12" disabled={step != 1}/>
        </div>

        <div className="selector">
            <input type="number" id="chapters_count" value={chaptersCount} onChange={(e) => setChaptersCount(e.target.value)} placeholder="Кол-во глав в разделе" min="3" max="40" disabled={step != 1}/>
        </div>

        <div className="selector">
            <input type="number" id="chapters_length" value={chaptersLength} onChange={(e) => setChaptersLength(e.target.value)} placeholder="Средняя длина главы" min="300" max="4000" disabled={step != 1}/>
        </div>

        <div className="selector">
            <input type="text" id="genre" value={genre} onChange={(e) => setGenre(e.target.value)} placeholder="Жанр книги" disabled={step != 1}/>
        </div>

        <div className="selector">
            <input type="text" id="book_name" value={bookName} onChange={(e) => setBookName(e.target.value)} placeholder="Название книги" disabled={step != 1}/>
        </div>

        <div className="selector">
            <select id="gpt_version" name="gpt_version" value={gptVersion} onChange={(e) => setGptVersion(e.target.value)} disabled={step != 1}>
                <option value="3.0">GPT-3</option>
                <option value="3.5">GPT-3.5</option>
                <option value="3.7">GPT-3.5/4</option>
                <option value="4.0">GPT-4</option>
            </select>
        </div>

        {step === 1 ? <button id="requestButton" onClick={handleButtonClick}>Начать генерацию</button> : ""}
   </div>

   {step >= 2 ? <div className="sections">
     <p className="step">2</p>
     <p className="label">Названия разделов</p>
     <div>
       {sections.map((section, index) => (
          <input
            disabled={step != 2}
            key={index}
            type="text"
            id={`section-${index + 1}`}
            className="section"
            value={`${index + 1}. ${section.name}`}
            onChange={(e) => {
              const newName = e.target.value.split(". ")[1];
              setSections((prevSections) => {
                return prevSections.map((section, idx) => {
                  if (idx === index) {
                    return { name: newName ? newName : "", chapters: section.chapters };
                  } else {
                    return section;
                  }
                });
              });
            }}
          />
        ))}
     </div>
     {step === 2 ? <button id="confirmSections" onClick={handleSectionsButtonClick}>Подтвердить</button> : "" }
    </div> : ""}

   {step >= 3 ? <div className="chapters">
      <p className="step">3</p>
      <p className="label">Названия глав</p>
      {sections.map((section, sectionIndex) => (
        <div key={`section-${sectionIndex}`} class={`section-${sectionIndex}`}>
          <p className="section-label">{section.name}</p>
          {section.chapters.map(([id, title, chapter], chapterIndex) => (
            <>
            <input
              disabled={step != 3}
              key={`chapter-${chapterIndex}`}
              type="text"
              id={`sections-${sectionIndex + 1}-chapter-${chapterIndex + 1}`}
              className="chapter"
              value={`${chapterIndex + 1}. ${title}`}
              onChange={(e) => {
                const newTitle = e.target.value.split(". ")[1];
                setSections((prevSections) => {
                  return prevSections.map((section, idx) => {
                    if (idx === sectionIndex) {
                      return {
                        ...section,
                        chapters: section.chapters.map((chapter, idx) => {
                          if (idx === chapterIndex) {
                            return [id, newTitle ? newTitle : ""];
                          } else {
                            return chapter;
                          }
                        }),
                      };
                    } else {
                      return section;
                    }
                  });
                });
              }}
            />
            {chapter ? <span title={chapter}> ✅</span> : <span title={`Глава "${title}" еще не сгенерирована`}> ❌</span>}
            </>
          ))}
        </div>
      ))}
      {(step === 3 && sections.every((section) => section.chapters.length > 0) ) ?
      <button id="confirmChapters" onClick={handleChaptersButtonClick}>Подтвердить</button> : "" }
    </div> : ""}



   {step >= 4 ? <div className="description">
       <p className="step">4</p>
       <p className="label">Небольшое описание книги</p>
       <div>
        <textarea
          type="text"
          className="area-description"
          value={pregeneration}
          disabled={step != 4}/>
       </div>
       {step === 4 ? <button id="confirmDescription" onClick={handleDescriptionButtonClick}>
         Сгенерировать книгу
       </button> : "" }
   </div> : ""}

   {step >= 5 ? <div className="result">
       <p className="step">5</p>
       <p className="label">Результаты</p>
       <div>
        <div type="text" className="area-results disabled">
            { step < 5.2 ? <div>
                Генерация... {(alreadyGeneratedChaptersCount / (sectionsCount * chaptersCount) * 100).toFixed(2)}%
            </div> : ""}
            {step === 5.2 ? <div>
                Книга собирается в pdf...
            </div> : ""}
            {step === 5.3 ? <div>
                Книга готова! Ссылка: <a href={bookLink} target="_blank" rel="noopener noreferrer">клик</a>
            </div> : ""}
        </div>
       </div>
       {step === 5.1 ? <button id="confirmResults" onClick={handleConfirmResultsButtonClick}>
         Собрать книгу в pdf
       </button> : "" }
   </div> : ""}

   </div> : ""}
   <div className={`errorMessage ${(!socketState && errorMessage) ? 'show' : ''}`}>{errorMessage}</div>
   </>
  );
}

export default App;
