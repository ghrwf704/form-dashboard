// ファイルパス: static/js/main.js

document.addEventListener("DOMContentLoaded", function () {
  // --- 天気情報取得 ---
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      function (pos) {
        const lat = pos.coords.latitude;
        const lon = pos.coords.longitude;

        fetch("/get_weather_by_coords", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ lat, lon }),
        })
          .then((res) => res.json())
          .then((data) => {
            document.getElementById("weather-city").textContent = data.city;
            document.getElementById("weather-description").textContent = data.description;
            document.getElementById("weather-temp").textContent = data.temp + "℃";
            document.getElementById("weather-date").textContent = data.date;
            document.getElementById("weather-weekday").textContent = data.weekday;
            document.getElementById("weather-time").textContent = data.time;
          })
          .catch(error => console.error('Weather fetch error:', error));
      },
      function (error) {
        console.error("Geolocation error:", error);
        document.getElementById("weather-city").textContent = "取得失敗";
      }
    );
  } else {
    document.getElementById("weather-city").textContent = "非対応ブラウザ";
  }

  // --- 汎用モーダル処理 ---
  // モーダルが閉じられたときにフォームをリセットする
  const editModal = document.getElementById("editModal");
  if (editModal) {
    editModal.addEventListener("hidden.bs.modal", function () {
      const form = editModal.querySelector("form");
      if (form) {
        form.reset();
      }
    });
  }

  // モーダルの背景が残ってしまう問題への対策
  document.addEventListener("click", function () {
    const backdrop = document.querySelector(".modal-backdrop");
    const isModalOpen = document.querySelector(".modal.show");
    if (backdrop && !isModalOpen) {
      backdrop.remove();
      document.body.classList.remove("modal-open");
      document.body.style.paddingRight = "";
    }
  });
});