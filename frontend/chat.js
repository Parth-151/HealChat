const token = localStorage.getItem("authToken");
const username = localStorage.getItem("UserName");
console.log(username)
    if (!token) {
      window.location.href = "login.html";
    }
    
    const chat = document.getElementById("chat");
    const userInput = document.getElementById("user-input");
    const sendBtn = document.getElementById("send-btn");
    const moodBtns = document.querySelectorAll(".mood-btn");
    const toggleBtn = document.getElementById("toggleTheme");
    const userDropdown = document.getElementById("userDropdown");
    const dropdownMenu = document.getElementById("dropdownMenu");
    const logoutBtn = document.getElementById("logoutBtn");
    const homeLogo = document.getElementById("homeLogo");

    userDropdown.innerText="👤" + username + " ▾"

    homeLogo.addEventListener("click", () => {
      window.location.href = "index.html"; 
    });
    
    userDropdown.addEventListener("click", () => {
      dropdownMenu.classList.toggle("hidden");
    });

    logoutBtn.addEventListener("click", () => {
      localStorage.removeItem("authToken");
      window.location.href = "index.html";
    });

    
    function addMessage(text, sender) {
      const row = document.createElement("div");
      row.className = `row ${sender}`;
      const bubble = document.createElement("div");
      bubble.className = `bubble ${sender}`;
      bubble.innerText = text;
      row.appendChild(bubble);
      chat.appendChild(row);
      chat.scrollTop = chat.scrollHeight;
    }

    async function loadMessages() {
      try {
        const res = await fetch("http://127.0.0.1:8000/api/chatbot/chat/", {
          headers: { "Authorization": token ? "Bearer " + token : "" },
        });
        const data = await res.json();
        data.forEach(m => {
          addMessage(m.message, "user");
          addMessage(m.response || "No response from server", "bot");
        });
      } catch {
        addMessage("⚠️ Could not connect to server.", "bot");
      }
    }

    loadMessages();

    async function sendMessage(msg) {
      addMessage(msg, "user");
      try {
        const res = await fetch("http://127.0.0.1:8000/api/chatbot/chat/", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Authorization": token ? "Bearer " + token : ""
          },
          body: JSON.stringify({ user_message: msg }),
        });
        const data = await res.json();
        addMessage(data.response || "No response from server", "bot");
      } catch {
        addMessage("⚠️ Error connecting to server.", "bot");
      }
    }

    sendBtn.addEventListener("click", () => {
      const msg = userInput.value.trim();
      if (!msg) return;
      sendMessage(msg);
      userInput.value = "";
    });

    userInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        const msg = userInput.value.trim();
        if (msg) sendMessage(msg);
        userInput.value = "";
      }
    });

    moodBtns.forEach(btn => {
      btn.addEventListener("click", () => {
        const mood = btn.getAttribute("data-mood");
        sendMessage(mood);
      });
    });

    toggleBtn.addEventListener("click", () => {
      document.body.classList.toggle("dark-mode");
      toggleBtn.textContent = document.body.classList.contains("dark-mode") ? "🌙" : "☀️";
    });