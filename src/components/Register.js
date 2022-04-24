import { React, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

function Register() {
  const usernameRef = useRef();
  const passwordRef = useRef();
  const passwordConfirmRef = useRef();

  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  async function handleRegister(e) {
    e.preventDefault();

    if (passwordRef.current.value !== passwordConfirmRef.current.value) {
      return alert("Passwords do not match");
    }

    try {
      setLoading(true);
      await fetch(process.env.REACT_APP_MAIN_ROOT + "/user/reg/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          username: usernameRef.current.value,
          password: passwordRef.current.value,
          password2: passwordConfirmRef.current.value,
        }),
      })
        .then((response) => {
          if (response.ok) {
            navigate("/login");
            return response.json();
          } else {
            throw Error(response.statusText);
          }
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
        className="h-2/5 w-3/12 flex flex-col border-2 border-red-300 items-center justify-evenly"
        onSubmit={handleRegister}
      >
        <div className="w-2/3 h-12 text-center">Регистрация</div>

        <input
          className="w-2/3 h-12 border-2 border-red-300 text-center"
          placeholder="Имя пользователя"
          type="text"
          ref={usernameRef}
          required
        />

        <input
          className="w-2/3 h-12 border-2 border-red-300 text-center"
          placeholder="Пароль"
          type="password"
          ref={passwordRef}
          autoComplete="new-password"
          required
        />
        <input
          className="w-2/3 h-12 border-2 border-red-300 text-center"
          placeholder="Подтверждение пароля"
          type="password"
          ref={passwordConfirmRef}
          required
        />

        <button className="w-2/3 h-12 bg-red-300 text-white" disabled={loading}>
          Зарегестрироваться
        </button>
        <div className="text-sm">
          Есть аккаунт?{" "}
          <a className="font-medium text-red-300" href="/login">
            Войти
          </a>
        </div>
      </form>
    </main>
  );
}

export default Register;
