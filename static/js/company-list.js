// ファイルパス: static/js/company-list.js

document.addEventListener("DOMContentLoaded", function () {
  const nameInput = document.getElementById("filter-name");
  const addressInput = document.getElementById("filter-address");
  const statusSelect = document.getElementById("filter-status");
  const tableBody = document.querySelector("table tbody");

  // --- テーブルフィルタリング機能 ---
  function filterTable() {
    const nameFilter = nameInput.value.toLowerCase();
    const addressFilter = addressInput.value.toLowerCase();
    const statusFilter = statusSelect.value;
    // データ行と詳細行をペアで処理
    for (let i = 0; i < tableBody.rows.length; i += 2) {
      const dataRow = tableBody.rows[i];
      const detailRow = tableBody.rows[i + 1];

      const name = dataRow.querySelector(".company-name")?.textContent.toLowerCase() || "";
      const address = dataRow.cells[4]?.textContent.toLowerCase() || "";
      const status = dataRow.querySelector(".sales-status")?.textContent || "";

      const isMatch =
        name.includes(nameFilter) &&
        address.includes(addressFilter) &&
        (!statusFilter || status === statusFilter);

      dataRow.style.display = isMatch ? "" : "none";
      // フィルタリング時は詳細行を常に非表示にする
      if (detailRow && detailRow.classList.contains("detail-row")) {
        detailRow.style.display = "none";
        // 表示される行の詳細トグルアイコンをリセット
        if(isMatch) {
           const icon = dataRow.querySelector(".toggle-icon");
           if(icon) icon.textContent = "▼";
        }
      }
    }
  }

  if (nameInput) nameInput.addEventListener("input", filterTable);
  if (addressInput) addressInput.addEventListener("input", filterTable);
  if (statusSelect) statusSelect.addEventListener("change", filterTable);


  // --- Excel出力機能 ---
  const exportBtn = document.getElementById("exportVisible");
  if (exportBtn) {
    exportBtn.addEventListener("click", () => {
      const name = nameInput.value.trim();
      const address = addressInput.value.trim();
      const status = statusSelect.value.trim();

      fetch("/export_excel_filtered", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, address, status }),
      })
      .then(res => res.blob())
      .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "filtered_companies.xlsx";
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
      })
      .catch(error => console.error('Excel export error:', error));
    });
  }

  // --- イベントデリゲーションによるイベント処理 ---
  document.addEventListener('click', function (e) {
    const editButton = e.target.closest('.edit-btn');
    const toggleButton = e.target.closest('.toggle-details');

    // 編集ボタンの処理
    if (editButton) {
      document.getElementById('edit_id').value = editButton.dataset.id || '';
      document.getElementById('edit_name').value = editButton.dataset.companyName || '';
      document.getElementById('edit-url-top').value = editButton.dataset.urlTop || '';
      document.getElementById('edit-url-form').value = editButton.dataset.urlForm || '';
      document.getElementById('edit_address').value = editButton.dataset.address || '';
      document.getElementById('edit_tel').value = editButton.dataset.tel || '';
      document.getElementById('edit_fax').value = editButton.dataset.fax || '';
      document.getElementById('edit_category').value = editButton.dataset.category || '';
      document.getElementById('edit_description').value = editButton.dataset.description || '';
      document.getElementById('edit_status').value = editButton.dataset.salesStatus || '未連絡';
      document.getElementById('edit_note').value = editButton.dataset.salesNote || '';
      return;
    }

    // 詳細表示トグルボタンの処理
    if (toggleButton) {
      const row = toggleButton.closest("tr");
      const detailRow = row.nextElementSibling;
      const icon = toggleButton.querySelector(".toggle-icon");

      if (detailRow && detailRow.classList.contains("detail-row")) {
        const isVisible = detailRow.style.display !== "none";
        detailRow.style.display = isVisible ? "none" : "table-row";
        icon.textContent = isVisible ? "▼" : "▲";
      }
    }
  });
});