// Socket.io
const socket = io();
const messageInput = document.getElementById('messageInput');
const messageList = document.getElementById('messageList');

document.getElementById('postForm').addEventListener('submit', function(event) {
  event.preventDefault();
  var content = document.querySelector('textarea[name="content"]').value;
  fetch('/post', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ content: content }),
  })
  .then(function(response) {
    if (response.ok) {
      console.log('愚痴の投稿に成功しました🤓');
      document.querySelector('textarea[name="content"]').value = ''; // テキストエリアをクリア
      location.reload();
      // ここで投稿データを追加表示するなどの処理を行う
    } else {
      console.log('愚痴の投稿に失敗しました😭');
    }
  })
  .catch(function(error) {
    console.log('通信エラー:', error);
  });
});

socket.on('connect', () => {
  console.log('Connected to server');
});

socket.on('disconnect', () => {
  console.log('Disconnected from server');
});

socket.on('new_message', (post) => {
  const listItem = document.createElement('li');
  listItem.textContent = post.content;  // 投稿の内容を表示
  messageList.appendChild(listItem);
});
