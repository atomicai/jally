import { Routes, Route } from "react-router-dom";
import AddBook from "./components/AddBook";
import EditorHome from "./components/EditorHome";
import EditorLogin from "./components/EditorLogin";
import Home from "./components/Home";
import Login from "./components/Login";
import Register from "./components/Register";

function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/editor" exact element={<EditorHome />} />
      <Route path="/login" exact element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/login/editor" exact element={<EditorLogin />} />
      <Route path="/editor/add" exact element={<AddBook />} />
    </Routes>
  );
}

export default App;
