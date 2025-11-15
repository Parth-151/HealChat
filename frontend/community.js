const params = new URLSearchParams(window.location.search);
const slug = params.get("slug");
const baseUrl = `http://127.0.0.1:8000/api/groups/${slug}/messages/`;
console.log(baseUrl)
const token = localStorage.getItem("authToken");

const chatBox = document.getElementById("chatBox");
const socket = new WebSocket(`ws://127.0.0.1:8000/ws/groups/${slug}/`);

socket.onmessage = (e) => {
  const data = JSON.parse(e.data);
  const div = document.createElement("div");
  div.className = "mb-2";
  div.innerHTML = `<strong>${data.username}</strong>: ${data.message}`;
  chatBox.appendChild(div);
  chatBox.scrollTop = chatBox.scrollHeight;
};

async function loadMessages() {
  const res = await fetch(baseUrl, { headers: { Authorization: `Bearer ${token}` }});
  console.log(res)
  const data = await res.json();
  data.forEach(m => {
    chatBox.innerHTML += `<div><strong>${m.sender.username}</strong>: ${m.content}</div>`;
  });
  chatBox.scrollTop = chatBox.scrollHeight;
}

document.getElementById("msgForm").addEventListener("submit", e => {
  e.preventDefault();
  const msg = msgInput.value.trim();
  if (msg) {
    socket.send(JSON.stringify({ message: msg }));
    msgInput.value = "";
  }
});

loadMessages();