import React, { useEffect, useRef } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { ChevronDownIcon } from "@heroicons/react/outline";
import toast, { Toaster } from "react-hot-toast";

const AddBook = () => {
  const [isOpen, setIsOpen] = React.useState(false);
  const [selectedOption, setSelectedOption] = React.useState("book");
  const titleRef = useRef();
  const authorRef = useRef();
  const yearRef = useRef();
  const descriptionRef = useRef();
  const genreRef = useRef();
  const [selectedFile, setSelectedFile] = React.useState("");
  const [loading, setLoading] = React.useState(false);
  const navigate = useNavigate();

  function signOut() {
    sessionStorage.removeItem("accessToken");
    navigate("/");
  }

  function onSuccesfulResponce() {
    toast.success("Книга успешно добавлена");
  }

  async function onSubmit(e) {
    e.preventDefault();
    try {
      setLoading(true);
      await fetch(process.env.REACT_APP_MAIN_ROOT + "/lib/books/list/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: "Bearer " + sessionStorage.getItem("accessToken"),
        },
        body: JSON.stringify({
          author: authorRef.current.value,
          genre: genreRef.current.value,
          publishing_house: "we",
          title: titleRef.current.value,
          description: descriptionRef.current.value,
          year: yearRef.current.value,
          status: true,
        }),
      })
        .then((response) => {
          if (response.ok) {
            onSuccesfulResponce();
          } else {
            throw Error(response.statusText);
          }
        })
        .catch((error) => {
          console.log(error);
        });
    } catch {
      Error("Failed to create an account");
    } finally {
      setLoading(false);
    }
  }

  return sessionStorage.getItem("accessToken") ? (
    <div>
      <div>
        <Toaster />
      </div>
      <nav className="w-full h-14 flex justify-between mt-2">
        <div className="flex justify-center items-center">
          <img src="/logo_main.png" className="w-24 h-24" />

          <span className="text-[30px]">Цифровая библиотека</span>
        </div>
        <div className="flex justify-evenly items-center text-md w-3/6">
          <span>
            {" "}
            <a href="/editor">Поиск</a>
          </span>
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

      <form className="w-2/3 mt-8 flex flex-col ml-8" onSubmit={onSubmit}>
        <span className="text-4xl ml-10">Добавить издание</span>
        <label className="w-28 h-36 bg-slate-200 rounded-sm flex justify-center items-center hover:cursor-pointer mt-4 ml-10">
          <input
            type="file"
            onChange={(e) => setSelectedFile(e.target.files[0])}
            accept="image/png, image/gif, image/jpeg"
            name="picture"
          />
          Фото
        </label>

        <div className="flex justify-between">
          <div className="flex flex-col items-end w-1/6 mt-6 h-60">
            <span className="h-12">Классификация</span>
            <span className="h-12 mt-2">Название</span>
            <span className="h-12 mt-3">Автор</span>
            <span className="h-12 mt-3">Год</span>
            <span className="h-12 mt-3">Жанр</span>
            <span className="h-12 mt-3">Описание</span>
          </div>
          <div className="flex flex-col w-5/6 mt-6 ml-7 justify-between h-auto">
            <div className="flex mt-2 mb-2 ">
              <div className="flex h-5 flex-row mr-2">
                <input
                  className="mt-1"
                  type="radio"
                  checked={selectedOption === "book"}
                  onChange={(e) => setSelectedOption(e.target.value)}
                  value="book"
                />
                <span className="text-[14px] ml-1">Книга</span>
              </div>
              <div className="flex h-5 mr-2">
                <input
                  className="mt-1"
                  type="radio"
                  checked={selectedOption === "magazine"}
                  onChange={(e) => setSelectedOption(e.target.value)}
                  value="magazine"
                />
                <span className="text-[14px] ml-1">Журнал</span>
              </div>
              <div className="flex h-5">
                <input
                  className="mt-1"
                  type="radio"
                  checked={selectedOption === "newspaper"}
                  onChange={(e) => setSelectedOption(e.target.value)}
                  value="newspaper"
                />
                <span className="text-[14px] ml-1">Газета</span>
              </div>
            </div>

            <input
              type="text"
              className="bg-slate-200 rounded-sm w-2/3 mt-3"
              ref={titleRef}
              required
            />
            <input
              type="text"
              className="bg-slate-200 rounded-sm w-2/3 mt-3"
              ref={authorRef}
              required
            />
            <input
              type="text"
              className="bg-slate-200 rounded-sm w-2/3 mt-3"
              ref={yearRef}
              required
            />
            <input
              type="text"
              className="bg-slate-200 rounded-sm w-2/3 mt-3"
              ref={genreRef}
              required
            />
            <textarea
              className="bg-slate-200 rounded-sm w-2/3 h-72 mt-4"
              ref={descriptionRef}
              required
            />
          </div>
        </div>
        <button
          className="absolute right-1/3 bottom-16 w-44 bg-red-300 rounded-sm"
          type="submit"
        >
          Добавить
        </button>
      </form>
    </div>
  ) : (
    <Navigate to="/login/editor"></Navigate>
  );
};

export default AddBook;
