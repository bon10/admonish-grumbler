const messageInput = document.getElementById("messageInput");
const messageList = document.getElementById("messageList");

const postForm = document.getElementById("postForm");
const postButton = postForm.querySelector(".btn-post");
const postTextarea = postForm.querySelector('textarea[name="content"]');
const POST_BUTTON_LABEL = postButton.textContent;

// 本アプリは投稿時にリンク先のOGP取得を挟むため、/post の応答に数秒かかることがある。
// その間に利用者が「投稿」を連打すると同じ愚痴が複数件登録されてしまうため、
// 応答が返るまで送信処理自体を受け付けないようにする。
let isPosting = false;

function setPostingState(posting) {
  isPosting = posting;
  postButton.disabled = posting;
  postButton.textContent = posting ? "投稿中…" : POST_BUTTON_LABEL;
}

postForm.addEventListener("submit", function (event) {
  event.preventDefault();
  // Enterキー送信など、ボタンのdisabledを経由しない送信経路もここで止める
  if (isPosting) return;

  var content = postTextarea.value;
  setPostingState(true);

  fetch("/post", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ content: content }),
  })
    .then(function (response) {
      if (response.ok) {
        console.log("愚痴の投稿に成功しました🤓");
        postTextarea.value = ""; // テキストエリアをクリア
        // 成功時はリロードで画面が作り直されるため、ボタンは無効のままにしておく
        location.reload();
      } else {
        alert("愚痴の投稿に失敗しました😭");
        console.log("愚痴の投稿に失敗しました😭");
        setPostingState(false);
      }
    })
    .catch(function (error) {
      console.log("通信エラー:", error);
      setPostingState(false);
    });
});

// ブラウザバックでキャッシュから復帰したときに、ボタンが「投稿中…」のまま
// 押せなくなるのを防ぐ
window.addEventListener("pageshow", function (event) {
  if (event.persisted) setPostingState(false);
});

document.addEventListener("DOMContentLoaded", (event) => {
  // 削除ボタン
  document.querySelectorAll(".delete-post-button").forEach((button) => {
    button.addEventListener("click", (e) => {
      e.preventDefault();
      const postId = button.getAttribute("data-post-id");
      const confirmDelete = confirm("この投稿を削除しますか？");

      if (confirmDelete) {
        fetch(`/post/${postId}`, { method: "DELETE" })
          .then((response) => {
            if (response.ok) {
              location.reload();
            } else {
              alert("削除に失敗しました。");
            }
          })
          .catch((error) => console.error("Error:", error));
      }
    });
  });

  // 編集ボタン
  document.querySelectorAll(".edit-post-button").forEach((button) => {
    button.addEventListener("click", (e) => {
      e.preventDefault();
      const postCard = button.closest(".post-card");
      const postBody = postCard.querySelector(".post-body");
      const postActions = postCard.querySelector(".post-actions");
      const postId = button.getAttribute("data-post-id");

      // 既に編集中なら何もしない
      if (postCard.querySelector(".post-edit-form")) return;

      // 現在のテキストを取得（HTMLタグを除去）
      const currentText = postBody.innerText;

      // 編集フォームを作成
      const editForm = document.createElement("div");
      editForm.className = "post-edit-form";
      editForm.innerHTML = `
        <textarea class="edit-textarea">${currentText}</textarea>
        <div class="post-edit-actions">
          <button class="btn-edit-cancel" type="button">キャンセル</button>
          <button class="btn-edit-save" type="button">保存</button>
        </div>
      `;

      // 本文とアクションを隠して編集フォームを表示
      postBody.style.display = "none";
      postActions.style.display = "none";
      postBody.after(editForm);

      // テキストエリアにフォーカス
      const textarea = editForm.querySelector(".edit-textarea");
      textarea.focus();
      textarea.setSelectionRange(textarea.value.length, textarea.value.length);

      // キャンセルボタン
      editForm.querySelector(".btn-edit-cancel").addEventListener("click", () => {
        editForm.remove();
        postBody.style.display = "";
        postActions.style.display = "";
      });

      // 保存ボタン
      editForm.querySelector(".btn-edit-save").addEventListener("click", () => {
        const newContent = textarea.value.trim();
        if (!newContent) {
          alert("投稿内容が空です。");
          return;
        }

        fetch(`/post/${postId}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ content: newContent }),
        })
          .then((response) => {
            if (response.ok) {
              location.reload();
            } else {
              alert("更新に失敗しました。");
            }
          })
          .catch((error) => console.error("Error:", error));
      });
    });
  });
});
