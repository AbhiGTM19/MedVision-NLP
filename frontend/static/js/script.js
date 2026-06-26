document.addEventListener("DOMContentLoaded", () => {
    // UI Elements
    const htmlElement = document.documentElement;
    
    const textInput = document.getElementById('text-input');
    const charCount = document.getElementById('char-count');
    const analyzeBtn = document.getElementById('analyze-btn');
    const btnText = document.getElementById('btn-text');
    const btnSpinner = document.getElementById('btn-spinner');
    
    const resultsArea = document.getElementById('results-area');
    const annotatedText = document.getElementById('annotated-text');
    const breakdownText = document.getElementById('breakdown-text');
    // Removed dynamic RAG Response container injection

    
    const historyList = document.getElementById('history-list');
    const historyEmptyMessage = document.getElementById('history-empty-message');
    const clearHistoryBtn = document.getElementById('clear-history-button');

    let latestResult = null;

    // Event Listeners
    if (textInput) textInput.addEventListener('input', () => { charCount.textContent = textInput.value.length; });
    if (analyzeBtn) analyzeBtn.addEventListener('click', runAnalysis);
    if (clearHistoryBtn) clearHistoryBtn.addEventListener('click', clearHistory);

    // Modal Elements
    const modelInfoBtn = document.getElementById('model-info-btn');
    const archModal = document.getElementById('arch-modal');
    const closeModalBtn = document.getElementById('close-modal-btn');
    const modalOverlay = document.getElementById('modal-overlay');
    const modalBody = document.getElementById('modalBody');
    const modalModelSelect = document.getElementById('modalModelSelect');

    const mobileMenuBtn = document.getElementById('mobile-menu-btn');
    const mobileNavPanel = document.getElementById('mobile-nav-panel');

    // Modal Handlers
    if (modelInfoBtn) {
        modelInfoBtn.addEventListener('click', () => {
            archModal.classList.remove('hidden');
            populateModal(modalModelSelect.value);
        });
    }

    if (closeModalBtn) {
        closeModalBtn.addEventListener('click', () => archModal.classList.add('hidden'));
        modalOverlay.addEventListener('click', () => archModal.classList.add('hidden'));
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') archModal.classList.add('hidden');
        });
        modalModelSelect.addEventListener('change', (e) => populateModal(e.target.value));
    }

    // Mobile Menu Handler
    if (mobileMenuBtn && mobileNavPanel) {
        mobileMenuBtn.addEventListener('click', () => {
            mobileNavPanel.classList.toggle('hidden');
        });
    }

    function populateModal(type) {
        if (type === 'fast') {
            modalBody.innerHTML = `<p class="type-body">The <strong class="text-primary">RAG Knowledge Pipeline</strong> retrieves relevant medical knowledge from a Vector Database (ChromaDB) to augment and ground language model predictions.</p>`;
        } else {
            modalBody.innerHTML = `<p class="type-body">The <strong class="text-secondary">Bio_ClinicalBERT Classifier</strong> uses a pre-trained Transformer model fine-tuned on the MIMIC-III clinical database. It computes dense embeddings of the transcribed text and applies a sequence classification head to predict the medical specialty.</p>`;
        }
    }


    if(historyList) renderHistory();

    // Predictor API Call
    async function runAnalysis() {
        const input = textInput.value.trim();
        
        if (!input) {
            alert("Please enter clinical text to classify.");
            return;
        }

        analyzeBtn.disabled = true;
        btnText.textContent = "PROCESSING...";
        btnSpinner.classList.remove('hidden');
        resultsArea.classList.add('hidden');

        try {
            let response = await fetch("/predict-rag", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ text: input })
            });

            if (!response.ok) throw new Error(`Server error: ${response.statusText}`);

            const data = await response.json();
            
            latestResult = { 
                specialty: data.specialty,
                confidence: data.confidence,
                attributions: data.word_attributions, 
                rag_response: data.rag_response,
                text: input,
                timestamp: new Date().toISOString()
            };
            
            displayResults(latestResult);
            addToHistory(latestResult);

        } catch (error) {
            alert(`Analysis failed: ${error.message}`);
        } finally {
            analyzeBtn.disabled = false;
            btnText.textContent = "CLASSIFY SPECIALTY";
            btnSpinner.classList.add('hidden');
            resultsArea.classList.remove('hidden');
            resultsArea.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    }

    function interpolateColor(score) {
        // Map score to a background color opacity. 
        // We highlight positive attributions in a blue/green hue.
        // Negative attributions could be red, but for XAI usually we just show magnitude.
        if (score <= 0.05) return '';
        
        // Max opacity at 0.5 score
        let opacity = Math.min(score * 2, 0.8).toFixed(2);
        return `background-color: rgba(59, 130, 246, ${opacity}); color: ${opacity > 0.4 ? 'white' : 'inherit'};`;
    }

    function displayResults(data) {
        annotatedText.innerHTML = '';
        breakdownText.innerHTML = '';

        const confPercent = (data.confidence * 100).toFixed(1) + '%';

        // 2. XAI Annotated Text (Feature Attribution)
        let annotatedHtml = '';
        const attrDict = {};
        
        if (data.attributions) {
            data.attributions.forEach(attr => {
                // Normalize to lowercase for matching
                attrDict[attr.word.toLowerCase()] = Math.max(attrDict[attr.word.toLowerCase()] || 0, attr.score);
            });
        }

        let words = data.text.split(/(\s+)/);
        words.forEach(word => {
            if (word.trim() === '') {
                annotatedHtml += word;
                return;
            }
            
            const cleanWord = word.replace(/[^a-zA-Z0-9]/g, '').toLowerCase();
            const score = attrDict[cleanWord] || 0;
            
            if (score > 0.05) {
                const style = interpolateColor(score);
                annotatedHtml += `<span class="px-1 mx-0.5 rounded cursor-help font-semibold transition-colors" style="${style}" title="Attribution: ${score.toFixed(3)}">${word}</span>`;
            } else {
                annotatedHtml += word;
            }
        });

        annotatedText.innerHTML = annotatedHtml;

        // 3. Explainable AI Summary
        let summary = `The <em>Bio_ClinicalBERT</em> engine classified this text as <strong>${data.specialty}</strong> with ${confPercent} confidence.<br><br>`;
        summary += `The highlighted text above uses <strong>PyTorch Captum (Integrated Gradients)</strong> to visualize Feature Attribution. Darker highlights indicate words that had the strongest influence on the model's classification.`;
        breakdownText.innerHTML = summary;

        // Bridge to Chat UI
        const chatAssistantLink = document.getElementById('chat-assistant-link');
        if (chatAssistantLink && data.text) {
            chatAssistantLink.href = `/chat-ui?initial_query=${encodeURIComponent("Please analyze this clinical case: " + data.text)}`;
        }
    }

    // History Logic
    function addToHistory(result) {
        let history = getHistory();
        history.unshift(result);
        history = history.slice(0, 5); // Keep last 5
        localStorage.setItem('medvisionHistory', JSON.stringify(history));
        if(historyList) renderHistory();
    }

    function getHistory() {
        return JSON.parse(localStorage.getItem("medvisionHistory") || "[]");
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
            const div = document.createElement('div');
            div.className = "bg-white p-4 rounded-xl flex justify-between items-center border border-outline-variant/30 shadow-sm animate-in slide-in-from-left duration-500";
            
            div.innerHTML = `
                <div class="flex flex-col gap-1 max-w-[70%]">
                    <p class="type-body truncate">"${item.text.substring(0, 60)}..."</p>
                    <span class="type-caption">${new Date(item.timestamp).toLocaleTimeString()}</span>
                </div>
                <span class="px-3 py-1 bg-primary/10 text-primary border-primary/20 rounded-full type-caption border">${item.specialty}</span>
            `;
            historyList.appendChild(div);
        });
    }

    function clearHistory() {
        localStorage.removeItem('medvisionHistory');
        if(historyList) renderHistory();
    }

    // Intersection Observer for Bento Animations
    const bentoCards = document.querySelectorAll('.bento-card');
    if (bentoCards.length > 0) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-fade-in-up');
                    observer.unobserve(entry.target);
                }
            });
        }, {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        });

        bentoCards.forEach(card => observer.observe(card));
    }
});
