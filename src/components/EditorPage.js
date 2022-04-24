import React, { useEffect, useRef } from "react";
import { ChevronDownIcon, SearchIcon } from "@heroicons/react/outline";
import EditorBook from "../components/EditorBook";

import { useNavigate } from "react-router-dom";

function EditorPage() {
  const [isOpen, setIsOpen] = React.useState(false);
  const [filter, setFilter] = React.useState("");
  const [selectedOption, setSelectedOption] = React.useState("books");
  const [status, setStatus] = React.useState("available");
  const [genre, setGenre] = React.useState("fantasy");
  const navigate = useNavigate();
  const searchRef = useRef();

  function signOut() {
    sessionStorage.removeItem("accessToken");
    navigate("/");
  }
  const [loading, setLoading] = React.useState(false);
  const [books, setBooks] = React.useState([]);

  useEffect(() => {
    fetchData();
    setLoading(false);
    console.log(books);
  }, []);

  async function fetchData() {
    setBooks([]);
    setLoading(true);
    await fetch(process.env.REACT_APP_MAIN_ROOT + "/lib/books/list/", {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        Authorization: "Bearer " + sessionStorage.getItem("accessToken"),
      },
    })
      .then((response) => {
        if (response.ok) {
          return response.json();
        } else {
          throw Error(response.statusText);
        }
      })
      .then((data) => {
        setBooks(data);
      });

    // booksData.map((book) => {
    //   setBooks((books) => [...books, book]);
    // });
  }

  async function handleSearch() {
    setBooks([]);
    setLoading(true);

    try {
      await fetch(
        process.env.REACT_APP_MAIN_ROOT +
          `/lib/books/list/?title=${searchRef.current.value}`,
        {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
            Authorization: "Bearer " + sessionStorage.getItem("accessToken"),
          },
        }
      )
        .then((response) => {
          if (response.ok) {
            return response.json();
          } else {
            throw Error(response.statusText);
          }
        })
        .then((data) => {
          setBooks(data);
        });
    } catch (e) {
      console.log(e);
    } finally {
      setLoading(false);
    }

    // booksData.map((book) => {
    //   setBooks((books) => [...books, book]);
    // });
  }

  return (
    <div>
      <nav className="w-full h-14 flex justify-between mt-2">
        <div className="flex justify-center items-center">
          <img src="/logo_main.png" className="w-24 h-24" />

          <span className="text-[30px]">Цифровая библиотека</span>
        </div>
        <div className="flex justify-evenly items-center text-md w-3/6">
          <span>Поиск</span>
          <span className="hover:cursor-pointer">
            <a href="/editor/add">Добавить издание</a>
          </span>

          <div
            className="flex flex-row hover:cursor-pointer"
            onClick={() => setIsOpen(!isOpen)}
          >
            <span>Личный кабинет</span>
            <ChevronDownIcon className="h-10 w-10 text-red-400" />
          </div>

          {isOpen ? (
            <div className="absolute right-20 top-32 border-2 border-red-400 rounded-lg p-4 flex flex-col items-center">
              <span className="hover:cursor-pointer">Редактировать</span>
              <span className="hover:cursor-pointer">Помощь</span>
              <span className="hover:cursor-pointer">Настройки</span>
              <span className="hover:cursor-pointer" onClick={() => signOut()}>
                Выйти
              </span>
            </div>
          ) : null}
          <div className="h-14 w-14 relative border-2 border-red-400 rounded-full">
            <img
              src="/cat.jpeg"
              alt="Picture of the author"
              className="rounded-full"
            />
          </div>
        </div>
      </nav>
      <nav className="w-full h-14 flex justify-end">
        <div className="flex justify-evenly items-center text-md w-3/6">
          <span>Пользователи</span>
          <span>Отзывы</span>

          <span>Продленные книги</span>
        </div>
      </nav>
      <div className="ml-24 mt-10 flex">
        <input
          className="w-2/3 bg-gray-200 flex pl-12 rounded-sm bg-search-pattern bg-no-repeat opacity-50 "
          type="text"
          onKeyPress={(event) => event.key === "Enter" && handleSearch()}
          ref={searchRef}
        />
        <div
          className="w-32 bg-gray-200 ml-2 rounded-sm flex flex-row justify-center items-center hover:cursor-pointer"
          onClick={() => setFilter(!filter)}
        >
          <span>Фильтр</span>
          <ChevronDownIcon className="h-5 w-5 text-red-400" />
        </div>
        {filter ? (
          <div className="absolute right-72 top-52 border-2 border-red-400 rounded-lg p-4 flex flex-col text-md">
            <div>
              <span className="text-[20px] font-medium">Классификация</span>
              <div className="flex flex-col ml-4">
                <div className="flex h-5">
                  <input
                    className="mt-1"
                    type="radio"
                    checked={selectedOption === "books"}
                    onChange={(e) => setSelectedOption(e.target.value)}
                    value="books"
                  />
                  <span className="text-[14px] ml-1">Книги</span>
                </div>
                <div className="flex h-5">
                  <input
                    className="mt-1"
                    type="radio"
                    checked={selectedOption === "magazines"}
                    onChange={(e) => setSelectedOption(e.target.value)}
                    value="magazines"
                  />
                  <span className="text-[14px] ml-1">Журналы</span>
                </div>
                <div className="flex h-5">
                  <input
                    className="mt-1"
                    type="radio"
                    checked={selectedOption === "newspaper"}
                    onChange={(e) => setSelectedOption(e.target.value)}
                    value="newspaper"
                  />
                  <span className="text-[14px] ml-1">Газеты</span>
                </div>
              </div>
            </div>
            <div>
              <span className="text-[20px] font-medium">Наличие</span>
              <div className="flex flex-col ml-4">
                <div className="flex h-5">
                  <input
                    className="mt-1"
                    type="radio"
                    checked={status === "available"}
                    onChange={(e) => setStatus(e.target.value)}
                    value="available"
                  />
                  <span className="text-[14px] ml-1">В наличии</span>
                </div>
                <div className="flex h-5">
                  <input
                    className="mt-1"
                    type="radio"
                    checked={status === "unavailable"}
                    onChange={(e) => setStatus(e.target.value)}
                    value="unavailable"
                  />
                  <span className="text-[14px] ml-1">Не в наличии</span>
                </div>
              </div>
            </div>
            <div>
              <span className="text-[20px] font-medium">Жанр</span>
              <div className="flex flex-col ml-4">
                <div className="flex h-5">
                  <input
                    className="mt-1"
                    type="radio"
                    checked={genre === "fantasy"}
                    onChange={(e) => setGenre(e.target.value)}
                    value="fantasy"
                  />
                  <span className="text-[14px] ml-1">Фантастика</span>
                </div>
                <div className="flex h-5">
                  <input
                    className="mt-1"
                    type="radio"
                    checked={genre === "detective"}
                    onChange={(e) => setGenre(e.target.value)}
                    value="detective"
                  />
                  <span className="text-[14px] ml-1">Детектив</span>
                </div>
                <div className="flex h-5">
                  <input
                    className="mt-1"
                    type="radio"
                    checked={genre === "roman"}
                    onChange={(e) => setGenre(e.target.value)}
                    value="roman"
                  />
                  <span className="text-[14px] ml-1">Роман</span>
                </div>
                <div className="flex h-5">
                  <input
                    className="mt-1"
                    type="radio"
                    checked={genre === "biography"}
                    onChange={(e) => setGenre(e.target.value)}
                    value="biography"
                  />
                  <span className="text-[14px] ml-1">Биография</span>
                </div>
                <div className="flex h-5">
                  <input
                    className="mt-1"
                    type="radio"
                    checked={genre === "nonfiction"}
                    onChange={(e) => setGenre(e.target.value)}
                    value="nonfiction"
                  />
                  <span className="text-[14px] ml-1">Non-fiction</span>
                </div>
              </div>
            </div>
            <div>
              <span className="text-[20px] font-medium">Год</span>
              <div className="flex flex-col">
                <div className="flex h-5">
                  <span className="text-[14px] ml-1 mr-1">1869</span>
                  <input className="mt-1" type="range" min={1869} max={2022} />
                  <span className="text-[14px] ml-1">2022</span>
                </div>
              </div>
            </div>
          </div>
        ) : null}
      </div>
      <section className="ml-24 mt-10 flex w-2/3 flex-col overflow-auto">
        {books.map((book) => {
          return (
            <EditorBook
              key={book.id}
              image={book.image}
              status={book.status}
              title={book.title}
              genre={book.genre}
              recommended={book.recommended}
              year={book.year}
              description={book.description}
              author={book.author}
            />
          );
        })}
      </section>
    </div>
  );
}

export default EditorPage;
