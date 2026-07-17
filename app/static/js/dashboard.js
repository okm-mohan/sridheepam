document.addEventListener("DOMContentLoaded", function () {
    startClock();
    setGreeting();
    animateMoneyCounters();
    loadSalesChart();
    initVoiceAssistant();
});

function startClock() {
    const dateElement = document.getElementById("todayDate");
    const clockElement = document.getElementById("liveClock");

    function update() {
        const now = new Date();

        if (dateElement) {
            dateElement.textContent = now.toLocaleDateString("en-IN", {
                weekday: "long",
                year: "numeric",
                month: "long",
                day: "numeric"
            });
        }

        if (clockElement) {
            clockElement.textContent = now.toLocaleTimeString("en-IN", {
                hour: "2-digit",
                minute: "2-digit",
                second: "2-digit"
            });
        }
    }

    update();
    setInterval(update, 1000);
}

function setGreeting() {
    const hour = new Date().getHours();
    const heading = document.getElementById("dashboardGreeting");

    if (!heading) {
        return;
    }

    let greeting = "Good Evening";

    if (hour < 12) {
        greeting = "Good Morning";
    } else if (hour < 17) {
        greeting = "Good Afternoon";
    }

    const userName = (heading.dataset.userName || "User").trim();
    heading.textContent = `${greeting}, ${userName}`;
}

function animateMoneyCounters() {
    document.querySelectorAll("[data-counter]").forEach(function (element) {
        const target = Number(element.dataset.counter || 0);
        const steps = 36;
        const increment = target / steps;
        let current = 0;
        let tick = 0;

        const timer = setInterval(function () {
            tick += 1;
            current += increment;

            if (tick >= steps) {
                current = target;
                clearInterval(timer);
            }

            element.textContent = "\u20B9 " + Math.round(current).toLocaleString("en-IN");
        }, 18);
    });
}

function loadSalesChart() {
    const canvas = document.getElementById("salesChart");

    if (!canvas || typeof Chart === "undefined") {
        return;
    }

    let labels = [];
    let values = [];

    try {
        labels = JSON.parse(canvas.dataset.labels || "[]");
        values = JSON.parse(canvas.dataset.values || "[]").map(Number);
    } catch (error) {
        labels = [];
        values = [];
    }

    if (!labels.length) {
        labels = ["No Data"];
        values = [0];
    }

    new Chart(canvas, {
        type: "line",
        data: {
            labels,
            datasets: [{
                label: "Sales",
                data: values,
                borderColor: "#0e7490",
                backgroundColor: "rgba(14,116,144,.12)",
                pointBackgroundColor: "#047857",
                pointBorderColor: "#ffffff",
                pointRadius: 4,
                borderWidth: 3,
                fill: true,
                tension: 0.35
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            return "\u20B9 " + Number(context.parsed.y || 0).toLocaleString("en-IN");
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { color: "#64748b", font: { weight: "700" } }
                },
                y: {
                    beginAtZero: true,
                    grid: { color: "rgba(148,163,184,.22)" },
                    ticks: {
                        color: "#64748b",
                        callback: function (value) {
                            return "\u20B9 " + Number(value).toLocaleString("en-IN");
                        }
                    }
                }
            }
        }
    });
}

function initVoiceAssistant() {
    const launcher = document.getElementById("voiceAssistantLauncher");
    const popup = document.getElementById("voiceAssistantPopup");
    const closeButton = document.getElementById("assistantClose");
    const clearButton = document.getElementById("assistantClear");
    const form = document.getElementById("assistantForm");
    const input = document.getElementById("assistantInput");
    const micButton = document.getElementById("assistantMic");
    const messages = document.getElementById("assistantMessages");
    const quickQuestions = document.getElementById("assistantQuickQuestions");
    const insightsBox = document.getElementById("assistantInsights");
    const notification = document.getElementById("assistantNotification");
    const status = document.getElementById("assistantStatus");
    const language = document.getElementById("assistantLanguage");
    const soundToggle = document.getElementById("assistantSoundToggle");

    if (!launcher || !popup || !form || !input || !messages) {
        return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    let recognition = null;
    let listening = false;
    let spokenReplies = true;
    let insightsLoaded = false;
    let conversationHistory = [];

    function setOpen(open) {
        popup.hidden = !open;
        launcher.setAttribute("aria-expanded", String(open));
        document.getElementById("voiceAssistant").classList.toggle("open", open);
        if (open) {
            notification.hidden = true;
            input.focus();
            if (!insightsLoaded) {
                loadInsights();
            }
        }
    }

    function setStatus(label, state) {
        status.className = state || "";
        status.innerHTML = `<i></i> ${label}`;
    }

    function addMessage(text, who) {
        const bubble = document.createElement("div");
        bubble.className = `assistant-message assistant-message-${who}`;
        bubble.textContent = text;
        messages.appendChild(bubble);
        messages.scrollTop = messages.scrollHeight;
        return bubble;
    }

    function setThinking(active) {
        const existing = messages.querySelector(".assistant-thinking");
        if (existing) {
            existing.remove();
        }
        if (active) {
            const thinking = document.createElement("div");
            thinking.className = "assistant-message assistant-message-ai assistant-thinking";
            thinking.innerHTML = "<span></span><span></span><span></span>";
            messages.appendChild(thinking);
            messages.scrollTop = messages.scrollHeight;
        }
    }

    function speak(text) {
        if (!spokenReplies || !("speechSynthesis" in window)) {
            return;
        }
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(text.replace(/Rs\./g, "rupees"));
        utterance.lang = language.value;
        utterance.rate = 0.96;
        const voices = window.speechSynthesis.getVoices();
        const matchingVoice = voices.find(function (voice) {
            return voice.lang.toLowerCase() === language.value.toLowerCase();
        });
        if (matchingVoice) {
            utterance.voice = matchingVoice;
        }
        window.speechSynthesis.speak(utterance);
    }

    async function askAssistant(question) {
        const cleanQuestion = (question || "").trim();
        if (!cleanQuestion) {
            return;
        }

        const previousHistory = conversationHistory.slice(-12);
        addMessage(cleanQuestion, "user");
        conversationHistory.push({ role: "user", content: cleanQuestion });
        input.value = "";
        setThinking(true);
        setStatus("Checking company data...", "thinking");

        try {
            const response = await fetch("/ai-chatbot/ask", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ question: cleanQuestion, history: previousHistory })
            });
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.answer || "Unable to answer right now.");
            }
            setThinking(false);
            addMessage(data.answer, "ai");
            conversationHistory.push({ role: "assistant", content: data.answer });
            renderQuickQuestions(data.suggestions || []);
            setStatus(data.mode === "ai" ? "Conversational AI" : "ERP data mode", "");
            speak(data.answer);
        } catch (error) {
            setThinking(false);
            addMessage(error.message || "I could not reach the assistant. Please try again.", "ai");
            setStatus("Please try again", "error");
        }
    }

    function renderQuickQuestions(items) {
        if (!items.length) {
            return;
        }
        quickQuestions.replaceChildren();
        items.slice(0, 4).forEach(function (question) {
            const button = document.createElement("button");
            button.type = "button";
            button.textContent = question;
            button.addEventListener("click", function () { askAssistant(question); });
            quickQuestions.appendChild(button);
        });
    }

    function renderInsights(items, summary) {
        insightsBox.replaceChildren();
        const summaryLine = document.createElement("p");
        summaryLine.className = "assistant-daily-summary";
        summaryLine.textContent = summary;
        insightsBox.appendChild(summaryLine);

        items.slice(0, 3).forEach(function (item) {
            const card = document.createElement(item.action_url ? "a" : "div");
            card.className = `assistant-insight assistant-insight-${item.type}`;
            if (item.action_url) {
                card.href = item.action_url;
            }
            const icon = document.createElement("i");
            icon.className = item.type === "warning" ? "bi bi-exclamation-triangle-fill" :
                item.type === "reminder" ? "bi bi-alarm-fill" :
                item.type === "success" ? "bi bi-check-circle-fill" : "bi bi-lightbulb-fill";
            const copy = document.createElement("span");
            const title = document.createElement("strong");
            const description = document.createElement("small");
            title.textContent = item.title;
            description.textContent = item.message;
            copy.append(title, description);
            card.append(icon, copy);
            insightsBox.appendChild(card);
        });
        insightsBox.hidden = false;
    }

    async function loadInsights() {
        insightsLoaded = true;
        try {
            const response = await fetch("/ai-assistant/insights");
            if (!response.ok) {
                throw new Error("Insights unavailable");
            }
            const data = await response.json();
            renderInsights(data.items || [], data.summary || "");
            renderQuickQuestions(data.quick_questions || []);
            setStatus(data.chat_mode === "ai" ? "Conversational AI" : "ERP data mode", "");
            const attentionCount = (data.items || []).filter(function (item) {
                return item.type === "warning" || item.type === "reminder";
            }).length;
            if (attentionCount && popup.hidden) {
                notification.textContent = attentionCount > 9 ? "9+" : String(attentionCount);
                notification.hidden = false;
            }
        } catch (error) {
            insightsLoaded = false;
        }
    }

    if (SpeechRecognition) {
        recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = true;

        recognition.addEventListener("start", function () {
            listening = true;
            micButton.classList.add("listening");
            setStatus("Listening...", "listening");
            input.placeholder = "Listening to your question...";
        });

        recognition.addEventListener("result", function (event) {
            let transcript = "";
            for (let index = event.resultIndex; index < event.results.length; index += 1) {
                transcript += event.results[index][0].transcript;
            }
            input.value = transcript.trim();
            if (event.results[event.results.length - 1].isFinal) {
                askAssistant(input.value);
            }
        });

        recognition.addEventListener("end", function () {
            listening = false;
            micButton.classList.remove("listening");
            input.placeholder = "Ask or speak about your business...";
            if (!messages.querySelector(".assistant-thinking")) {
                setStatus("Ready to help", "");
            }
        });

        recognition.addEventListener("error", function (event) {
            if (event.error !== "aborted") {
                addMessage("I could not hear that clearly. Please try again or type your question.", "ai");
            }
            setStatus("Voice input paused", "error");
        });
    } else {
        micButton.title = "Voice input is not supported in this browser";
        micButton.classList.add("unsupported");
    }

    launcher.addEventListener("click", function () { setOpen(popup.hidden); });
    closeButton.addEventListener("click", function () { setOpen(false); });
    clearButton.addEventListener("click", function () {
        conversationHistory = [];
        window.speechSynthesis.cancel();
        messages.replaceChildren();
        addMessage("New chat started. What would you like to know about your business?", "ai");
        input.value = "";
        input.focus();
        setStatus("Ready for a new question", "");
    });
    form.addEventListener("submit", function (event) {
        event.preventDefault();
        askAssistant(input.value);
    });
    micButton.addEventListener("click", function () {
        if (!recognition) {
            addMessage("Voice input is not supported here, but you can type your question below.", "ai");
            return;
        }
        recognition.lang = language.value;
        if (listening) {
            recognition.stop();
        } else {
            window.speechSynthesis.cancel();
            recognition.start();
        }
    });
    soundToggle.addEventListener("click", function () {
        spokenReplies = !spokenReplies;
        soundToggle.classList.toggle("active", spokenReplies);
        soundToggle.innerHTML = spokenReplies ? '<i class="bi bi-volume-up-fill"></i>' : '<i class="bi bi-volume-mute-fill"></i>';
        soundToggle.title = spokenReplies ? "Spoken replies on" : "Spoken replies off";
        soundToggle.setAttribute("aria-label", spokenReplies ? "Turn spoken replies off" : "Turn spoken replies on");
        if (!spokenReplies) {
            window.speechSynthesis.cancel();
        }
    });
    quickQuestions.querySelectorAll("button").forEach(function (button) {
        button.addEventListener("click", function () { askAssistant(button.textContent); });
    });
    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape" && !popup.hidden) {
            setOpen(false);
        }
    });

    loadInsights();
}
