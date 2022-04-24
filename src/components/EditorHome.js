import React from "react";
import EditorPage from "./EditorPage";
import StartingPage from "./StartingPage";

function EditorHome() {
  return sessionStorage.getItem("accessToken") ? (
    <EditorPage />
  ) : (
    <StartingPage />
  );
}

export default EditorHome;
