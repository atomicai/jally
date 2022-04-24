import { React, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

function Login() {
  const usernameRef = useRef();
  const passwordRef = useRef();

  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  async function handleLogin(e) {
    e.preventDefault();

    try {
      setLoading(true);
      await fetch(process.env.REACT_APP_MAIN_ROOT + "/api/token/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          username: usernameRef.current.value,
          password: passwordRef.current.value,
        }),
      })
        .then((response) => {
          if (response.ok) {
            return response.json();
          } else {
            throw Error(response.statusText);
          }
        })
        .then((data) => {
          sessionStorage.setItem("accessToken", data.access);

          navigate("/");
        })
        .catch((error) => {
          console.log(error);
        });
    } catch {
      Error("Failed to create an account");
    }
    setLoading(false);
  }

  return (
    <main className="flex h-screen w-screen justify-center items-center">
      <form
        className="h-1/3 w-3/12 flex flex-col border-2 border-red-300 items-center justify-evenly"
        onSubmit={handleLogin}
      >
        <div className="w-2/3 h-12 text-center">Вход в систему</div>

        <input
          className="w-2/3 h-12 border-2 border-red-300 text-center"
          placeholder="Имя пользователя"
          type="text"
          ref={usernameRef}
          required
        />
        <input
          className="w-2/3 h-12 border-2 border-red-300 text-center"
          type="password"
          ref={passwordRef}
          autoComplete="new-password"
          required
          placeholder="Пароль"
        />

        <button className="w-2/3 h-12 bg-red-300 text-white" disabled={loading}>
          Войти
        </button>
        <div className="text-sm">
          Нет аккаунта?{" "}
          <a className="font-medium text-red-300" href="/register">
            Зарегистрироваться
          </a>
        </div>
      </form>
    </main>
  );
}

export default Login;
