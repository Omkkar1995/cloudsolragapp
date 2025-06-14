function handleLogin() {
    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value.trim();

    const validUsers = {
        admin: "adminpass",
        user1: "user123"
    };

    if (!username || !password) {
        document.getElementById("login-error").textContent = "Username and password required.";
        return;
    }

    if (validUsers[username] && validUsers[username] === password) {
        localStorage.setItem("loggedInUser", username);  // ✅ Save login state
        showChat();
    } else {
        document.getElementById("login-error").textContent = "Invalid credentials.";
    }
}

function showChat() {
    document.querySelector(".login-container").style.display = "none";
    document.getElementById("chat-app").style.display = "flex";
}


window.onload = function () {
    const user = localStorage.getItem("loggedInUser");
    if (user) {
        showChat();  // ✅ Automatically log in
    }
};


let chatHistory = [];

function updateUI() {
    const chatWindow = document.getElementById('chat-window');
    chatWindow.innerHTML = '';
    chatHistory.forEach(entry => {
        chatWindow.innerHTML += `
      <div class="chat-entry">
        <div class="user">あなた: ${entry.question}</div>
        <div class="bot">ボット:<br>${marked.parse(entry.answer)}</div>
      </div>`;
    });
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

async function askQuestion() {
    const input = document.getElementById('question');
    const question = input.value.trim();
    if (!question) return;

    chatHistory.push({ question, answer: '考え中.. <span class="spinner"></span>' });
    updateUI();
    input.value = '';

    try {
        const res = await fetch('/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question })
        });

        const data = await res.json();
        chatHistory[chatHistory.length - 1].answer = data.answer;
        updateUI();
    } catch (err) {
        chatHistory[chatHistory.length - 1].answer = '⚠️ Error getting response.';
        updateUI();
    }
}

function resetChat() {
    chatHistory = [];
    updateUI();
}
