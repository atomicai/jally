import React from "react";
import ReaderPage from "./ReaderPage";
import StartingPage from "./StartingPage";

function Home() {
  return sessionStorage.getItem("accessToken") ? (
    <ReaderPage />
  ) : (
    <StartingPage />
  );
}

export default Home;
