import React from "react";

function EditorBook({
  image,
  status,
  title,
  genre,
  recommended,
  year,
  description,
  author,
}) {
  function truncate(str) {
    return str.length > 150 ? str.substring(0, 150) + "..." : str;
  }
  return (
    <div className="w-full h-1/4 flex mb-6">
      <div className="flex flex-col w-1/16 h-full mr-4 justify-center items-center">
        <img
          src="/harry.jpeg"
          alt="Picture of the author"
          className="rounded-sm w-24 h-36 mt-2"
        />
        <div className="border-2 border-red-400 text-[11px] mt-2 rounded-sm hover: cursor-pointer w-[120px] text-center">
          {status ? "ЗАБРОНИРОВАНО: 0" : "ЗАБРОНИРОВАНО: 1"}
        </div>
        <span className="text-[11px] mt-0 hover:cursor-pointer">
          Посмотреть отзывы
        </span>
      </div>
      <div className="flex flex-col w-10/12 h-full">
        <div>
          <span className="font-medium">{title}</span>{" "}
          <span className="hover:cursor-pointer bg-slate-200 w-24 ml-2 rounded-md text-sm p-1 font-medium">
            Редактировать
          </span>
        </div>
        <div className="text-[20px]">
          <span className="font-medium">Автор: </span>
          <span className="font-light">{author}</span>
        </div>
        <div className="text-[20px]">
          <span className="font-medium">Жанр: </span>
          <span className="font-light">{genre}</span>
        </div>
        <div className="text-[20px]">
          <span className="font-medium">Год: </span>
          <span className="font-light">{year}</span>
        </div>
        <div className="text-[20px]">
          <span className="font-medium">Статус: </span>
          <span className="font-light">
            {status ? "в наличии" : "нет в наличии"}
          </span>
          <span className="hover:cursor-pointer bg-slate-200 w-24 ml-2 rounded-md text-sm p-1">
            Изменить
          </span>
        </div>
        <div className="text-[20px]">
          <span className="font-medium">Описание: </span>
          <span className="font-light text-ellipsis">
            {truncate(description)}
          </span>
          <span className="font-medium hover:cursor-pointer"> Подробнее</span>
        </div>
      </div>
    </div>
  );
}

export default EditorBook;
