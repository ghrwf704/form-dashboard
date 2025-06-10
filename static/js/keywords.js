// ファイルパス: static/js/keywords.js

document.addEventListener("DOMContentLoaded", function () {
  // イベントデリゲーションを使用して、テーブル内のクリックを処理
  const table = document.querySelector(".keywords-table");
  if (!table) return;

  table.addEventListener("click", function (e) {
    const target = e.target;

    // --- 削除ボタンの確認ダイアログ ---
    if (target.classList.contains("delete-btn")) {
      if (!confirm("このキーワードを本当に削除しますか？")) {
        e.preventDefault(); // aタグの遷移をキャンセル
      }
      return; // 他の処理は不要なのでここで終了
    }

    // --- 変更ボタンの処理 ---
    if (target.classList.contains("edit-btn")) {
      e.preventDefault(); // aタグの遷移をキャンセル
      const row = target.closest("tr");
      
      const keywordSpan = row.querySelector(".keyword-text");
      const editForm = row.querySelector(".edit-form");

      // 表示と編集フォームを切り替える
      keywordSpan.style.display = "none";
      editForm.style.display = "flex"; // 横並びにするためflex
      return;
    }

    // --- キャンセルボタンの処理 ---
    if (target.classList.contains("cancel-btn")) {
      e.preventDefault(); // buttonのデフォルト動作をキャンセル
      const row = target.closest("tr");

      const keywordSpan = row.querySelector(".keyword-text");
      const editForm = row.querySelector(".edit-form");

      // 編集フォームを隠して、表示に戻す
      editForm.style.display = "none";
      keywordSpan.style.display = "block";
    }
  });
});