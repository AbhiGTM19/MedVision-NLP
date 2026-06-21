document.addEventListener("DOMContentLoaded", () => {
    // UI Elements
    const themeBtn = document.getElementById('theme-btn');
    const themeIcon = document.getElementById('theme-icon');
    const htmlElement = document.documentElement;
    
    const textInput = document.getElementById('text-input');
    const charCount = document.getElementById('char-count');
    const analyzeBtn = document.getElementById('analyze-btn');
    const btnText = document.getElementById('btn-text');
    const btnSpinner = document.getElementById('btn-spinner');
    
    const resultsArea = document.getElementById('results-area');
    const annotatedText = document.getElementById('annotated-text');
    const breakdownText = document.getElementById('breakdown-text');
    const ragResponseContainer = document.createElement('div');
    ragResponseContainer.className = 'w-full bg-surface-container-low rounded-2xl p-8 border border-outline-variant/50 shadow-inner mt-8';
    ragResponseContainer.innerHTML = '<h3 class="text-sm font-label uppercase tracking-widest text-outline mb-4">RAG Assistant Analysis</h3><div id="rag-content" class="text-on-surface leading-relaxed"></div>';
    breakdownText.parentElement.parentElement.parentElement.appendChild(ragResponseContainer);
    const ragContent = document.getElementById('rag-content');

    
    const historyList = document.getElementById('history-list');
    const historyEmptyMessage = document.getElementById('history-empty-message');
    const clearHistoryBtn = document.getElementById('clear-history-button');

    // Chat UI Elements
    const chatFab = document.getElementById('chat-fab');
    const chatPanel = document.getElementById('chat-panel');
    const closeChatBtn = document.getElementById('close-chat-btn');
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const chatMessages = document.getElementById('chat-messages');
    const chatSubmitBtn = document.getElementById('chat-submit-btn');
    
    let chatHistory = [];


    let latestResult = null;

    // Initialize Theme
    if (localStorage.theme === 'dark' || (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        htmlElement.classList.add('dark');
        themeIcon.textContent = 'light_mode';
    } else {
        htmlElement.classList.remove('dark');
        themeIcon.textContent = 'dark_mode';
    }

    // Event Listeners
    themeBtn.addEventListener('click', toggleTheme);
    textInput.addEventListener('input', () => { charCount.textContent = textInput.value.length; });
    analyzeBtn.addEventListener('click', runAnalysis);
    clearHistoryBtn.addEventListener('click', clearHistory);

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

    // Chat Panel Handlers
    chatFab.addEventListener('click', () => {
        chatPanel.classList.remove('translate-x-full');
    });

    closeChatBtn.addEventListener('click', () => {
        chatPanel.classList.add('translate-x-full');
    });

    chatForm.addEventListener('submit', handleChatSubmit);

    function populateModal(type) {
        if (type === 'fast') {
            modalBody.innerHTML = `<p class="text-on-surface-variant leading-relaxed">The <strong class="text-primary">RAG Knowledge Pipeline</strong> retrieves relevant medical knowledge from a Vector Database (ChromaDB) to augment and ground language model predictions.</p>`;
        } else {
            modalBody.innerHTML = `<p class="text-on-surface-variant leading-relaxed">The <strong class="text-secondary">Bio_ClinicalBERT Classifier</strong> uses a pre-trained Transformer model fine-tuned on the MIMIC-III clinical database. It computes dense embeddings of the transcribed text and applies a sequence classification head to predict the medical specialty.</p>`;
        }
    }


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
    }

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
        ragContent.innerHTML = '';

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
        
        // 4. RAG Response
        if (data.rag_response) {
            let ragHtml = `<p>${data.rag_response.answer}</p>`;
            if (data.rag_response.sources && data.rag_response.sources.length > 0) {
                ragHtml += `<div class="mt-4 text-xs text-outline font-label uppercase tracking-widest">Sources: ${data.rag_response.sources.join(', ')}</div>`;
            }
            ragContent.innerHTML = ragHtml;
            ragResponseContainer.classList.remove('hidden');
        } else {
            ragResponseContainer.classList.add('hidden');
        }
    }

    // History Logic
    function addToHistory(result) {
        let history = getHistory();
        history.unshift(result);
        history = history.slice(0, 5); // Keep last 5
        localStorage.setItem('medvisionHistory', JSON.stringify(history));
        renderHistory();
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
            div.className = "bg-surface dark:bg-surface-container p-4 rounded-xl flex justify-between items-center border border-outline-variant dark:border-outline-variant/10 shadow-sm dark:shadow-none animate-in slide-in-from-left duration-500";
            
            div.innerHTML = `
                <div class="flex flex-col gap-1 max-w-[70%]">
                    <p class="text-sm text-on-surface truncate font-medium">"${item.text.substring(0, 60)}..."</p>
                    <span class="text-[10px] text-outline font-medium">${new Date(item.timestamp).toLocaleTimeString()}</span>
                </div>
                <span class="px-3 py-1 bg-primary/10 text-primary border-primary/20 rounded-full text-xs font-bold border">${item.specialty}</span>
            `;
            historyList.appendChild(div);
        });
    }

    function clearHistory() {
        localStorage.removeItem('medvisionHistory');
        renderHistory();
    }

    // Chat Logic
    function appendChatMessage(role, text) {
        const div = document.createElement('div');
        div.className = `max-w-[85%] p-3 shadow-sm border ${role === 'user' ? 'self-end bg-primary text-on-primary rounded-2xl rounded-tr-sm border-primary' : 'self-start bg-surface-container rounded-2xl rounded-tl-sm border-outline-variant/20 text-on-surface'}`;
        div.innerHTML = `<p class="text-sm">${text}</p>`;
        chatMessages.appendChild(div);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    async function handleChatSubmit(e) {
        e.preventDefault();
        const input = chatInput.value.trim();
        if (!input) return;

        // Add user message to UI and history
        appendChatMessage('user', input);
        chatHistory.push({ role: 'user', content: input });
        chatInput.value = '';
        
        // Disable input
        chatInput.disabled = true;
        chatSubmitBtn.disabled = true;

        // Add loading indicator
        const loadingDiv = document.createElement('div');
        loadingDiv.id = 'chat-loading';
        loadingDiv.className = 'self-start max-w-[85%] bg-surface-container rounded-2xl rounded-tl-sm p-3 shadow-sm border border-outline-variant/20';
        loadingDiv.innerHTML = '<div class="flex gap-1 items-center h-4"><div class="w-1.5 h-1.5 bg-outline rounded-full animate-bounce"></div><div class="w-1.5 h-1.5 bg-outline rounded-full animate-bounce" style="animation-delay: 0.1s"></div><div class="w-1.5 h-1.5 bg-outline rounded-full animate-bounce" style="animation-delay: 0.2s"></div></div>';
        chatMessages.appendChild(loadingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ messages: chatHistory })
            });

            if (!response.ok) throw new Error('Chat API failed');
            const data = await response.json();
            
            // Remove loading
            document.getElementById('chat-loading').remove();
            
            // Add assistant message
            appendChatMessage('assistant', data.response);
            chatHistory.push({ role: 'assistant', content: data.response });
            
        } catch (error) {
            document.getElementById('chat-loading').remove();
            appendChatMessage('assistant', `Error: ${error.message}`);
        } finally {
            chatInput.disabled = false;
            chatSubmitBtn.disabled = false;
            chatInput.focus();
        }
    }
});
