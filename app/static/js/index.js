const messageInput = document.getElementById("messageInput");
const messageList = document.getElementById("messageList");

document
  .getElementById("postForm")
  .addEventListener("submit", function (event) {
    event.preventDefault();
    var content = document.querySelector('textarea[name="content"]').value;
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
          document.querySelector('textarea[name="content"]').value = ""; // テキストエリアをクリア
          location.reload();
          // ここで投稿データを追加表示するなどの処理を行う
        } else {
          alert("愚痴の投稿に失敗しました😭");
          console.log("愚痴の投稿に失敗しました😭");
        }
      })
      .catch(function (error) {
        console.log("通信エラー:", error);
      });
  });

document.addEventListener("DOMContentLoaded", (event) => {
  document.querySelectorAll(".delete-post-button").forEach((button) => {
    button.addEventListener("click", (e) => {
      e.preventDefault();
      const postId = button.getAttribute("data-post-id");
      const confirmDelete = confirm("この投稿を削除しますか？");

      if (confirmDelete) {
        // 削除処理をここに実装
        // 例: fetch APIを使用してサーバーに削除リクエストを送信
        fetch(`/post/${postId}`, { method: "DELETE" })
          .then((response) => {
            if (response.ok) {
              // 削除が成功した場合、ページを再読み込み
              location.reload();
            } else {
              alert("削除に失敗しました。");
            }
          })
          .catch((error) => console.error("Error:", error));
      }
    });
  });
});
