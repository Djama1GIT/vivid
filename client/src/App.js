import React, { useState, useEffect, useRef } from 'react';
import styles from './App.css';

function App() {
  const [sectionsCount, setSectionsCount] = useState(7);

  const unfilledChapters = [
    ['1', "Название главы №1 еще не сгенерировано"],
    ['2', "Название главы №2 еще не сгенерировано"],
    ['3', "Название главы №3 еще не сгенерировано"],
    ['4', "Название главы №4 еще не сгенерировано"],
    ['5', "Название главы №5 еще не сгенерировано"],
    ['6', "Название главы №6 еще не сгенерировано"],
    ['7', "Название главы №7 еще не сгенерировано"],
  ];

  const [sections, setSections] = useState([
     { name: 'Название раздела №1 еще не сгенерировано', chapters: JSON.parse(JSON.stringify(unfilledChapters)) },
     { name: 'Название раздела №2 еще не сгенерировано', chapters: JSON.parse(JSON.stringify(unfilledChapters)) },
     { name: 'Название раздела №3 еще не сгенерировано', chapters: JSON.parse(JSON.stringify(unfilledChapters)) },
     { name: 'Название раздела №4 еще не сгенерировано', chapters: JSON.parse(JSON.stringify(unfilledChapters)) },
     { name: 'Название раздела №5 еще не сгенерировано', chapters: JSON.parse(JSON.stringify(unfilledChapters)) },
     { name: 'Название раздела №6 еще не сгенерировано', chapters: JSON.parse(JSON.stringify(unfilledChapters)) },
     { name: 'Название раздела №7 еще не сгенерировано', chapters: JSON.parse(JSON.stringify(unfilledChapters)) },
    ]);


  const [chaptersCount, setChaptersCount] = useState(12);
  const [chaptersLength, setChaptersLength] = useState(4000);
  const [gptVersion, setGptVersion] = useState("3.5");
  const [genre, setGenre] = useState("");
  const [bookName, setBookName] = useState("");
  const [responseGPT, setResponseGPT] = useState("Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry's standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book. It has survived not only five centuries, but also the leap into electronic typesetting, remaining essentially unchanged. It was popularised in the 1960s with the release of Letraset sheets containing Lorem Ipsum passages, and more recently with desktop publishing software like Aldus PageMaker including versions of Lorem Ipsum.");

  // WebSocket instance variable
  const socketRef = useRef(null);

  useEffect(() => {
    socketRef.current = new WebSocket('ws://127.0.0.1:8081/ws/');

    // Connection opened
    socketRef.current.addEventListener('open', function (event) {
      console.log("Connection opened");
    });

    // Listen for messages
    socketRef.current.addEventListener('message', function (event) {
      const data = JSON.parse(event.data);
      if (data.code == 1) {
        setGenre(data.genre);
        setBookName(data.bookName);
        setChaptersCount(data.chaptersCount);
        setChaptersLength(data.chaptersLength);
        setSectionsCount(data.sectionsCount);
        setGptVersion(data.gptVersion);
        setResponseGPT(data.pregeneration)
      } else if (data.code == 2) {
        setSections(data.sections.map(([id, title]) => (
          {
            name: title,
            chapters: JSON.parse(JSON.stringify(unfilledChapters)),
          }
        )));
      } else if (data.code == 3) {
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
      } else if (data.code == 4) {
        setResponseGPT(data.pregeneration)
      }
    });


    // Connection closed
    socketRef.current.addEventListener('close', function (event) {
      console.log('Connection closed');
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
  };

  const handleSectionsButtonClick = () => {
    socketRef.current.send(JSON.stringify({
        cmd: "confirm_sections",
        sections: sections,
    }));
  };

  const handleChaptersButtonClick = () => {
    socketRef.current.send(JSON.stringify({
        cmd: "confirm_chapters",
        sections: sections,
    }));
  };


  return (
    <div className="App">
      <p className="step">1</p>
      <div className="form">
        <div className="selector">
            <input type="number" id="sections_count" value={sectionsCount} onChange={(e) => setSectionsCount(e.target.value)} placeholder="Sections count" min="4" max="12"/>
        </div>

        <div className="selector">
            <input type="number" id="chapters_count" value={chaptersCount} onChange={(e) => setChaptersCount(e.target.value)} placeholder="Chapters count" min="3" max="40"/>
        </div>

        <div className="selector">
            <input type="number" id="chapters_length" value={chaptersLength} onChange={(e) => setChaptersLength(e.target.value)} placeholder="Chapters length" min="300" max="4000"/>
        </div>

        <div className="selector">
            <input type="text" id="genre" value={genre} onChange={(e) => setGenre(e.target.value)} placeholder="Жанр книги"/>
        </div>

        <div className="selector">
            <input type="text" id="book_name" value={bookName} onChange={(e) => setBookName(e.target.value)} placeholder="Название книги"/>
        </div>

        <div className="selector">
            <select id="gpt_version" name="gpt_version" value={gptVersion} onChange={(e) => setGptVersion(e.target.value)}>
                <option value="3">GPT-3</option>
                <option value="3.5">GPT-3.5</option>
                <option value="4">GPT-4</option>
            </select>
        </div>

        <button id="requestButton" onClick={handleButtonClick}>Начать генерацию</button>
   </div>

   <div className="sections">
     <p className="step">2</p>
     <p className="label">Названия разделов</p>
     <div>
       {sections.map((section, index) => (
          <input
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
                    return { name: newName ? newName : "" };
                  } else {
                    return section;
                  }
                });
              });
            }}
          />
        ))}
     </div>
     <button id="confirmSections" onClick={handleSectionsButtonClick}>Подтвердить</button>
    </div>

   <div className="chapters">
      <p className="step">3</p>
      <p className="label">Названия глав</p>
      {sections.map((section, sectionIndex) => (
        <div key={`section-${sectionIndex}`}>
          <p className="section-label">{section.name}</p>
          {section.chapters.map(([id, title], chapterIndex) => (
            <input
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
          ))}
        </div>
      ))}
      <button id="confirmChapters" onClick={handleChaptersButtonClick}>
        Подтвердить
      </button>
    </div>



   <div className="description">
       <p className="step">4</p>
       <p className="label">Небольшое описание книги</p>
       <div>
        <textarea type="text" id="description" value={responseGPT}/>
       </div>
   </div>


   </div>
  );
}

export default App;
