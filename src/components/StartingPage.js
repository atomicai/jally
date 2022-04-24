import { React, useState } from "react";
import { useNavigate } from "react-router-dom";

function StartingPage() {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  function handleReaderRedirect() {
    navigate("/login");
  }

  function handleEditorRedirect() {
    navigate("/login/editor");
  }

  return (
    <main className="flex h-screen w-screen justify-center items-center">
      <div className="h-1/3 w-3/12 flex flex-col border-2 border-red-300 items-center justify-evenly">
        <button
          className="w-2/3 h-12 bg-red-300 text-white"
          disabled={loading}
          onClick={() => handleReaderRedirect()}
        >
          Войти как читатель
        </button>
        <button
          className="w-2/3 h-12 bg-red-300 text-white"
          disabled={loading}
          onClick={() => handleEditorRedirect()}
        >
          Войти как редактор
        </button>
      </div>
    </main>
  );
}

export default StartingPage;
