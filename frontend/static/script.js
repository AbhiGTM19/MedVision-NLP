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
    const entityTableBody = document.getElementById('entity-table-body');
    const breakdownText = document.getElementById('breakdown-text');
    
    const historyList = document.getElementById('history-list');
    const historyEmptyMessage = document.getElementById('history-empty-message');
    const clearHistoryBtn = document.getElementById('clear-history-button');

    // OCR Elements
    const dropzone = document.getElementById('dropzone');
    const imageInput = document.getElementById('image-input');
    const imagePreviewContainer = document.getElementById('image-preview-container');
    const imagePreview = document.getElementById('image-preview');
    let selectedImageFile = null;

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

    // OCR Event Listeners
    dropzone.addEventListener('click', () => imageInput.click());
    dropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropzone.classList.add('border-primary', 'bg-surface-container-high');
    });
    dropzone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        dropzone.classList.remove('border-primary', 'bg-surface-container-high');
    });
    dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.classList.remove('border-primary', 'bg-surface-container-high');
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            handleImageUpload(e.dataTransfer.files[0]);
        }
    });
    imageInput.addEventListener('change', (e) => {
        if (e.target.files && e.target.files[0]) {
            handleImageUpload(e.target.files[0]);
        }
    });

    function handleImageUpload(file) {
        if (!file.type.startsWith('image/')) {
            alert('Please upload a valid image file.');
            return;
        }
        selectedImageFile = file;
        const reader = new FileReader();
        reader.onload = (e) => {
            imagePreview.src = e.target.result;
            imagePreviewContainer.classList.remove('hidden');
            textInput.value = '';
            charCount.textContent = '0';
        };
        reader.readAsDataURL(file);
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
        
        if (!input && !selectedImageFile) {
            alert("Please enter clinical text or upload an image to classify.");
            return;
        }

        analyzeBtn.disabled = true;
        btnText.textContent = "PROCESSING...";
        btnSpinner.classList.remove('hidden');
        resultsArea.classList.add('hidden');

        try {
            let response;
            if (selectedImageFile) {
                const formData = new FormData();
                formData.append("file", selectedImageFile);
                
                response = await fetch("/predict-image", {
                    method: "POST",
                    body: formData
                });
            } else {
                response = await fetch("/predict", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ text: input })
                });
            }

            if (!response.ok) throw new Error(`Server error: ${response.statusText}`);

            const data = await response.json();
            
            if (selectedImageFile && data.extracted_text) {
                textInput.value = data.extracted_text;
                charCount.textContent = data.extracted_text.length;
            }

            const activeText = selectedImageFile ? data.extracted_text : input;
            
            latestResult = { 
                specialty: data.specialty,
                confidence: data.confidence,
                attributions: data.word_attributions, 
                text: activeText,
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
            
            selectedImageFile = null;
            imageInput.value = '';
            imagePreviewContainer.classList.add('hidden');
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
        entityTableBody.innerHTML = '';
        annotatedText.innerHTML = '';
        breakdownText.innerHTML = '';

        // 1. Data Table
        const tr = document.createElement('tr');
        tr.className = "hover:bg-surface-container transition-colors";
        
        const confPercent = (data.confidence * 100).toFixed(1) + '%';

        tr.innerHTML = `
            <td class="px-6 py-4 font-mono font-bold">Overarching Diagnosis</td>
            <td class="px-6 py-4">
                <span class="px-2 py-1 rounded text-xs font-bold bg-primary/20 text-primary border border-primary/30">${data.specialty}</span>
            </td>
            <td class="px-6 py-4 font-mono text-outline">${confPercent}</td>
        `;
        entityTableBody.appendChild(tr);

        // 2. XAI Annotated Text (Feature Attribution)
        let annotatedHtml = '';
        const attrDict = {};
        
        if (data.attributions) {
            data.attributions.forEach(attr => {
                // Normalize to lowercase for matching
                attrDict[attr.word.toLowerCase()] = Math.max(attrDict[attr.word.toLowerCase()] || 0, attr.score);
            });
        }

        let words = data.text.split(/(\\s+)/);
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
        summary += `The highlighted text above uses <strong>PyTorch Captum (Integrated Gradients)</strong> to visualize Feature Attribution. Darker highlights indicate words that had the strongest influence on the model's classification. `;
        if (data.text.length > 0 && selectedImageFile) {
            summary += `The text was seamlessly transcribed via <em>TrOCR</em>.`;
        }
        breakdownText.innerHTML = summary;
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
});
