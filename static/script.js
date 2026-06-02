document.addEventListener("DOMContentLoaded", () => {
    // UI Elements
    const themeBtn = document.getElementById('theme-btn');
    const themeIcon = document.getElementById('theme-icon');
    const htmlElement = document.documentElement;
    
    const reviewInput = document.getElementById('review-input');
    const charCount = document.getElementById('char-count');
    const modelSelect = document.getElementById('model-select');
    const analyzeBtn = document.getElementById('analyze-btn');
    const btnText = document.getElementById('btn-text');
    const btnSpinner = document.getElementById('btn-spinner');
    
    const resultsArea = document.getElementById('results-area');
    const scoreVal = document.getElementById('score-val');
    const verdictText = document.getElementById('verdict-text');
    const verdictIcon = document.getElementById('verdict-icon');
    const verdictTag = document.getElementById('verdict-tag');
    const breakdownContainer = document.getElementById('breakdown-container');
    const breakdownText = document.getElementById('breakdown-text');
    
    const historyList = document.getElementById('history-list');
    const historyEmptyMessage = document.getElementById('history-empty-message');
    const clearHistoryBtn = document.getElementById('clear-history-button');

    // Modal Dropdown Element
    const modalModelSelect = document.getElementById('modalModelSelect');

    const modelInfoBtn = document.getElementById('model-info-btn');
    const archModal = document.getElementById('arch-modal');
    const modalOverlay = document.getElementById('modal-overlay');
    const closeModalBtn = document.getElementById('close-modal-btn');
    const modalTitle = document.getElementById('modalTitle');
    const modalBody = document.getElementById('modalBody');

    let gaugeChart = null;
    let latestResult = null;
    let currentScore = 0;
    let currentChartColor = '#f59e0b';
    let chartTimeout = null;

    // Initialize Theme
    if (localStorage.theme === 'dark' || (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        htmlElement.classList.add('dark');
        themeIcon.textContent = 'light_mode';
    } else {
        htmlElement.classList.remove('dark');
        themeIcon.textContent = 'dark_mode';
    }

    // Restore Model choice
    const savedModel = localStorage.getItem("selectedModel");
    if (["fast", "accurate"].includes(savedModel)) {
        modelSelect.value = savedModel;
    }

    // Event Listeners
    themeBtn.addEventListener('click', toggleTheme);
    reviewInput.addEventListener('input', () => { charCount.textContent = reviewInput.value.length; });
    analyzeBtn.addEventListener('click', runAnalysis);
    modelInfoBtn.addEventListener('click', () => handleModelInfo(false));
    closeModalBtn.addEventListener('click', () => toggleModal(false));
    modalOverlay.addEventListener('click', () => toggleModal(false));
    clearHistoryBtn.addEventListener('click', clearHistory);
    modelSelect.addEventListener('change', () => localStorage.setItem("selectedModel", modelSelect.value));

    // Load initial data
    initChart(0);
    renderHistory();

    // Theme Logic
    function toggleTheme() {
        if (htmlElement.classList.contains('dark')) {
            htmlElement.classList.remove('dark');
            themeIcon.textContent = 'dark_mode';
            localStorage.theme = 'light';
        } else {
            htmlElement.classList.add('dark');
            themeIcon.textContent = 'light_mode';
            localStorage.theme = 'dark';
        }
        initChart(currentScore, currentChartColor, false);
    }

    // Modal Logic
    function toggleModal(show, title = '', bodyHTML = '') {
        if (show) {
            modalTitle.textContent = title;
            modalBody.innerHTML = bodyHTML;
            archModal.classList.remove('hidden');
            document.body.style.overflow = 'hidden';
        } else {
            archModal.classList.add('hidden');
            document.body.style.overflow = 'auto';
        }
    }

    async function handleModelInfo(isFromModalDropdown = false) {
        try {
            let modelChoice;
            
            if (isFromModalDropdown === true) {
                // If triggered by the modal dropdown, trust its current value
                modelChoice = modalModelSelect.value;
            } else {
                // If triggered by the main button, sync from the predictor
                modelChoice = modelSelect.value;
                if (modalModelSelect) {
                    modalModelSelect.value = modelChoice;
                }
            }

            const response = await fetch(`/model-info?model=${modelChoice}`);
            if (!response.ok) throw new Error("Could not fetch model info");
            const data = await response.json();
            
            let html = '';
            
            // Inject an architectural context paragraph based on the model choice
            const modelDesc = modelChoice === 'fast' 
                ? "The <strong>Fast Heuristics Pipeline</strong> uses a Scikit-Learn SGD Classifier coupled with a TF-IDF Vectorizer. It is highly optimized for rapid inference, acting as the baseline MLOps model. The frontend communicates with the FastAPI backend via REST, receiving linear feature weights for glass-box explainability."
                : "The <strong>Deep Transformer Pipeline</strong> leverages a Hugging Face DistilBERT architecture fine-tuned on movie reviews. Inference is served via a decoupled FastAPI endpoint. For explainability, it utilizes a surrogate mapping to the linear model's token weights, showcasing complex model integration strategies.";
                
            html += `
                <div class="mb-6 p-4 bg-surface-container-low rounded-xl border border-outline-variant/50 text-sm text-on-surface-variant leading-relaxed">
                    <h4 class="font-bold text-on-surface mb-2 flex items-center gap-2"><span class="material-symbols-outlined text-[18px] text-primary" data-icon="architecture">architecture</span> Pipeline Integration</h4>
                    ${modelDesc}
                </div>
                <h4 class="font-bold text-sm uppercase tracking-widest text-outline mb-4">Raw Configuration Parameters</h4>
            `;

            for (const [key, val] of Object.entries(data)) {
                html += `
                    <div class="bg-primary/5 border border-primary/20 p-3 rounded-lg mb-3">
                        <span class="font-bold text-sm uppercase">${key}:</span>
                        <span class="text-sm font-mono ml-2 break-all text-on-surface-variant">${JSON.stringify(val)}</span>
                    </div>
                `;
            }
            toggleModal(true, `Architecture: ${modelChoice.toUpperCase()}`, html);
        } catch (e) {
            toggleModal(true, "Error", `<p class="text-error">${e.message}</p>`);
        }
    }

    // Modal Dropdown Event Listener
    if (modalModelSelect) {
        modalModelSelect.addEventListener('change', () => {
            handleModelInfo(true);
        });
    }

    // Chart Setup
    function initChart(score, color = '#f59e0b', animate = false) {
        if (chartTimeout) {
            clearTimeout(chartTimeout);
            chartTimeout = null;
        }
        
        const ctx = document.getElementById('gaugeChart');
        currentScore = score;
        currentChartColor = color;

        const isDark = document.documentElement.classList.contains('dark');
        const bgColor = isDark ? '#ffffff' : color;
        const trackColor = isDark ? '#262626' : '#e5e7eb';

        if (!gaugeChart) {
            gaugeChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    datasets: [{
                        data: [0, 100],
                        backgroundColor: [bgColor, trackColor],
                        borderWidth: 0,
                        circumference: 180,
                        rotation: 270,
                        cutout: '85%',
                        borderRadius: 10
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: { tooltip: { enabled: false } },
                    events: [],
                    animation: false
                }
            });
        }

        gaugeChart.options.animation = false;
        gaugeChart.data.datasets[0].backgroundColor = [bgColor, trackColor];

        if (animate) {
            gaugeChart.data.datasets[0].data = [0, 100];
            gaugeChart.update();

            chartTimeout = setTimeout(() => {
                gaugeChart.options.animation = { duration: 1500, easing: 'easeOutQuart' };
                gaugeChart.data.datasets[0].data = [score, 100 - score];
                gaugeChart.update();
            }, 50);
        } else {
            gaugeChart.data.datasets[0].data = [score, 100 - score];
            gaugeChart.update();
        }
    }

    // Predictor API Call
    async function runAnalysis() {
        const input = reviewInput.value.trim();
        if (!input) {
            alert("Please enter a review to analyze.");
            return;
        }

        analyzeBtn.disabled = true;
        btnText.textContent = "PROCESSING...";
        btnSpinner.classList.remove('hidden');
        resultsArea.classList.add('hidden');

        try {
            const response = await fetch("/predict", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ review: input, model_choice: modelSelect.value })
            });

            if (!response.ok) throw new Error(`Server error: ${response.statusText}`);

            const data = await response.json();
            latestResult = { ...data, review: input };
            displayResults(latestResult);
            addToHistory(latestResult);

        } catch (error) {
            alert(`Analysis failed: ${error.message}`);
        } finally {
            analyzeBtn.disabled = false;
            btnText.textContent = "ANALYZE SENTIMENT";
            btnSpinner.classList.add('hidden');
            resultsArea.classList.remove('hidden');
            resultsArea.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    }

    // Display Logic
    function displayResults(data) {
        const score = Math.round(data.confidence * 100);
        scoreVal.textContent = `${score}%`;
        
        const isPositive = data.prediction === 'positive';
        const primaryColor = isPositive ? '#f59e0b' : '#ef4444'; // Amber or Red
        
        initChart(score, primaryColor, true);

        if (isPositive) {
            verdictText.textContent = data.verdict;
            verdictIcon.textContent = "thumb_up";
            verdictTag.className = "text-4xl font-black flex items-center gap-3 text-primary";
        } else {
            verdictText.textContent = data.verdict;
            verdictIcon.textContent = "thumb_down";
            verdictTag.className = "text-4xl font-black flex items-center gap-3 text-error";
        }

        if (!data.word_importances || Object.keys(data.word_importances).length === 0) {
            breakdownContainer.style.display = 'none';
        } else {
            breakdownContainer.style.display = 'block';
            renderHighlightedReview(data.review, data.word_importances);
        }
    }

    function renderHighlightedReview(originalText, wordImportances) {
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
        breakdownText.innerHTML = highlightedHTML;
    }

    // History Logic
    function addToHistory(result) {
        let history = getHistory();
        history.unshift(result);
        history = history.slice(0, 5); // Keep last 5
        localStorage.setItem('sentimentHistory', JSON.stringify(history));
        renderHistory();
    }

    function getHistory() {
        return JSON.parse(localStorage.getItem("sentimentHistory") || "[]");
    }

    function renderHistory() {
        const history = getHistory();
        historyList.innerHTML = "";
        
        if (!history.length) {
            historyEmptyMessage.classList.remove('hidden');
            clearHistoryBtn.classList.add('hidden');
            return;
        }
        
        historyEmptyMessage.classList.add('hidden');
        clearHistoryBtn.classList.remove('hidden');

        history.forEach(item => {
            const isPos = item.prediction === 'positive';
            
            const div = document.createElement('div');
            div.className = "bg-surface dark:bg-surface-container p-4 rounded-xl flex justify-between items-center border border-outline-variant dark:border-outline-variant/10 shadow-sm dark:shadow-none animate-in slide-in-from-left duration-500";
            div.innerHTML = `
                <div class="flex flex-col gap-1 max-w-[70%]">
                    <p class="text-sm text-on-surface truncate font-medium">"${item.review}"</p>
                    <span class="text-[10px] text-outline font-medium">Score: ${(item.confidence * 100).toFixed(1)}% | ${item.model_used.toUpperCase()}</span>
                </div>
                <span class="px-3 py-1 ${isPos ? 'bg-[#f59e0b]/10 text-[#f59e0b] border-[#f59e0b]/20' : 'bg-[#ef4444]/10 text-[#ef4444] border-[#ef4444]/20'} rounded-full text-xs font-bold border">${isPos ? 'POSITIVE' : 'NEGATIVE'}</span>
            `;
            historyList.appendChild(div);
        });
    }

    function clearHistory() {
        localStorage.removeItem('sentimentHistory');
        renderHistory();
    }
});
