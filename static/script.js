document.addEventListener("DOMContentLoaded", () => {
    const predictButton = document.getElementById("predict-button");
    const reviewInput = document.getElementById("reviewInput");
    const modelInfoButton = document.getElementById("model-info-button");
    const modal = document.getElementById("infoModal");
    const closeModalButton = modal.querySelector(".close-button");
    const modalOkButton = modal.querySelector(".modal-ok-button");
    const modelSelect = document.getElementById("model-select");
    const breakdownContainer = document.getElementById("breakdown-container");
    const copyResultsButton = document.getElementById("copy-results-button");
    const historyList = document.getElementById("history-list");
    const historyEmptyMessage = document.getElementById("history-empty-message");
    const clearHistoryButton = document.getElementById("clear-history-button");

    let latestResult = null;
    let confidenceGauge = null;

    // Restore last used model
    const savedModel = localStorage.getItem("selectedModel");
    if (["fast", "accurate"].includes(savedModel)) modelSelect.value = savedModel;

    modelSelect.addEventListener("change", () => {
        localStorage.setItem("selectedModel", modelSelect.value);
    });

    predictButton.addEventListener("click", handlePrediction);
    modelInfoButton.addEventListener("click", handleModelInfo);
    closeModalButton.addEventListener("click", closeModal);
    modalOkButton.addEventListener("click", closeModal);
    copyResultsButton.addEventListener("click", copyResultsToClipboard);
    clearHistoryButton.addEventListener("click", clearHistory);

    window.addEventListener("click", (event) => {
        if (event.target === modal) closeModal();
    });

    loadHistory();
    revealSections();
    window.addEventListener("scroll", revealSections);

    async function handlePrediction() {
        const reviewText = reviewInput.value.trim();
        if (!reviewText) return showModal("Error", "Please enter a movie review first.");

        const loader = predictButton.querySelector(".btn-loader");
        const btnText = predictButton.querySelector(".btn-text");
        const resultArea = document.getElementById('result-area');

        loader.style.display = "inline-block";
        btnText.textContent = "Analyzing...";
        predictButton.disabled = true;
        resultArea.style.display = 'none';

        const modelChoice = modelSelect.value;

        setTimeout(async () => {
            try {
                const response = await fetch("/predict", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ review: reviewText, model_choice: modelChoice })
                });

                if (!response.ok) throw new Error(`Server error: ${response.statusText}`);

                const data = await response.json();
                latestResult = { ...data, review: reviewText };
                displayResults(latestResult);
                saveToHistory(latestResult);

            } catch (error) {
                showModal("Error", `Failed to get prediction. ${error.message}`);
            } finally {
                loader.style.display = "none";
                btnText.textContent = "Analyze Sentiment";
                predictButton.disabled = false;
            }
        }, 3000);
    }

    function displayResults(data) {
        const verdictEl = document.getElementById('verdict');
        const resultArea = document.getElementById('result-area');

        verdictEl.textContent = data.verdict;
        verdictEl.className = data.prediction === 'positive' ? 'verdict-positive' : 'verdict-negative';
        createOrUpdateGauge(data.confidence, data.prediction);

        if (data.model_used === 'accurate' || !Object.keys(data.word_importances).length) {
            breakdownContainer.style.display = 'none';
        } else {
            breakdownContainer.style.display = 'block';
            renderHighlightedReview(data.review, data.word_importances);
        }

        resultArea.style.display = 'block';
    }

    function createOrUpdateGauge(confidence, sentiment) {
        const ctx = document.getElementById('confidenceGauge').getContext('2d');
        const gaugeLabel = document.getElementById('confidence-label');
        const score = Math.round(confidence * 100);
        const color = sentiment === 'positive' ? 'rgba(76, 175, 80, 1)' : 'rgba(244, 67, 54, 1)';

        gaugeLabel.textContent = `${score}%`;
        gaugeLabel.style.color = color;

        if (confidenceGauge) {
            confidenceGauge.data.datasets[0].data[0] = score;
            confidenceGauge.data.datasets[0].backgroundColor[0] = color;
            confidenceGauge.update();
        } else {
            confidenceGauge = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    datasets: [{
                        data: [score, 100 - score],
                        backgroundColor: [color, 'rgba(255, 255, 255, 0.1)'],
                        borderWidth: 0,
                        circumference: 180,
                        rotation: 270
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    cutout: '80%',
                    plugins: { tooltip: { enabled: false } },
                    animation: { animateRotate: true }
                }
            });
        }
    }

    function renderHighlightedReview(originalText, wordImportances) {
        const container = document.getElementById('highlighted-review');
        const maxImportance = Math.max(...Object.values(wordImportances).map(Math.abs), 1);

        const highlightedHTML = originalText.split(/(\s+)/).map(part => {
            if (part.trim() === '') return part;
            const word = part;
            const cleanWord = word.toLowerCase().replace(/[^\w]/g, '');
            const importance = wordImportances[cleanWord];

            if (importance) {
                const isPositive = importance > 0;
                const opacity = Math.min(Math.abs(importance) / maxImportance + 0.2, 1);
                return `<span class="highlighted-word ${isPositive ? 'positive' : 'negative'}" style="--bg-opacity: ${opacity};">
                            ${word}
                            <span class="tooltip">Importance: ${importance.toFixed(3)}</span>
                        </span>`;
            }
            return word;
        }).join('');
        container.innerHTML = highlightedHTML;
    }

    function copyResultsToClipboard() {
        if (!latestResult) return;
        const summary = `Sentiment Analysis Result:\n--------------------------\nReview: "${latestResult.review}"\nVerdict: ${latestResult.verdict}\nPrediction: ${latestResult.prediction}\nConfidence: ${(latestResult.confidence * 100).toFixed(1)}%\nModel Used: ${latestResult.model_used}`;
        navigator.clipboard.writeText(summary).then(() => {
            const icon = copyResultsButton.querySelector("i");
            const text = copyResultsButton.querySelector("span");
            icon.className = "fas fa-check";
            text.textContent = "Copied!";
            setTimeout(() => {
                icon.className = "fas fa-clipboard";
                text.textContent = "Copy Results";
            }, 2000);
        });
    }

    function saveToHistory(result) {
        let history = getHistory();
        history.unshift(result);
        history = history.slice(0, 5);
        localStorage.setItem('sentimentHistory', JSON.stringify(history));
        localStorage.setItem("selectedModel", result.model_used);
        renderHistory();
    }

    function getHistory() {
        return JSON.parse(localStorage.getItem("sentimentHistory") || "[]");
    }

    function renderHistory() {
        const history = getHistory();
        historyList.innerHTML = "";
        if (!history.length) {
            historyEmptyMessage.style.display = 'block';
            clearHistoryButton.style.display = 'none';
            return;
        }
        historyEmptyMessage.style.display = 'none';
        clearHistoryButton.style.display = 'inline-flex';
        history.forEach(item => {
            const div = document.createElement('div');
            div.className = 'history-item';
            div.innerHTML = `<p class="history-item-text">"${item.review}"</p>
                             <span class="history-item-verdict ${item.prediction === 'positive' ? 'verdict-positive' : 'verdict-negative'}">
                                ${item.prediction.charAt(0).toUpperCase() + item.prediction.slice(1)}
                             </span>`;
            historyList.appendChild(div);
        });
    }

    function clearHistory() {
        localStorage.removeItem('sentimentHistory');
        renderHistory();
    }

    function loadHistory() {
        renderHistory();
    }

    async function handleModelInfo() {
        try {
            const modelChoice = modelSelect.value;
            const response = await fetch(`/model-info?model=${modelChoice}`);
            const data = await response.json();
            const formatted = JSON.stringify(data, null, 2);
            showModal(`Model Info: ${modelChoice}`, `<pre>${formatted}</pre>`);
        } catch (e) {
            showModal("Error", "Could not fetch model info.");
        }
    }

    function showModal(title, bodyHTML) {
        document.getElementById("modalTitle").textContent = title;
        document.getElementById("modalBody").innerHTML = bodyHTML;
        modal.style.display = "flex";
    }

    function closeModal() {
        modal.style.display = "none";
    }

    function revealSections() {
        const reveals = document.querySelectorAll(".reveal-hero, .reveal-right, .reveal-left");
        for (let el of reveals) {
            const windowHeight = window.innerHeight;
            const elementTop = el.getBoundingClientRect().top;
            if (elementTop < windowHeight - 150) {
                el.classList.add("active");
            } else {
                el.classList.remove("active");
            }
        }
    }
});
