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
            alert("Please enter clinical text or upload an image to extract anomalies.");
            return;
        }

        analyzeBtn.disabled = true;
        btnText.textContent = "PROCESSING...";
        btnSpinner.classList.remove('hidden');
        resultsArea.classList.add('hidden');

        try {
            let response;
            if (selectedImageFile) {
                // OCR Image Flow
                const formData = new FormData();
                formData.append("file", selectedImageFile);
                
                response = await fetch("/predict-image", {
                    method: "POST",
                    body: formData
                });
            } else {
                // Text Flow
                response = await fetch("/predict", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ text: input })
                });
            }

            if (!response.ok) throw new Error(`Server error: ${response.statusText}`);

            const data = await response.json();
            
            // If OCR was used, populate the text box so the user sees what was extracted
            if (selectedImageFile && data.extracted_text) {
                textInput.value = data.extracted_text;
                charCount.textContent = data.extracted_text.length;
            }

            const activeText = selectedImageFile ? data.extracted_text : input;
            
            latestResult = { 
                entities: data.entities, 
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

    // Colors for specific Medical NER Tags
    const tagColors = {
        'PROBLEM': 'bg-red-500/20 text-red-700 dark:text-red-400 border border-red-500/30',
        'TREATMENT': 'bg-blue-500/20 text-blue-700 dark:text-blue-400 border border-blue-500/30',
        'TEST': 'bg-green-500/20 text-green-700 dark:text-green-400 border border-green-500/30',
        'MEDICATION': 'bg-purple-500/20 text-purple-700 dark:text-purple-400 border border-purple-500/30',
        'DEFAULT': 'bg-yellow-500/20 text-yellow-700 dark:text-yellow-400 border border-yellow-500/30'
    };

    function getTagStyle(tag) {
        for (const [key, val] of Object.entries(tagColors)) {
            if (tag.toUpperCase().includes(key)) return val;
        }
        return tagColors.DEFAULT;
    }

    function displayResults(data) {
        // Clear old results
        entityTableBody.innerHTML = '';
        annotatedText.innerHTML = '';
        breakdownText.innerHTML = '';

        if (!data.entities || data.entities.length === 0) {
            annotatedText.innerHTML = `<span class="italic text-outline">No specific clinical entities detected in the text.</span>`;
            breakdownText.innerHTML = "The model did not recognize any strong clinical entities (e.g., conditions, treatments, or medications) within the provided context.";
            return;
        }

        // 1. Data Table
        let breakdownTags = new Set();
        data.entities.forEach(entity => {
            breakdownTags.add(entity.tag.replace(/^[BI]-/, '')); // Remove B-/I- prefixes for summary
            
            const tr = document.createElement('tr');
            tr.className = "hover:bg-surface-container transition-colors";
            
            const confPercent = (entity.confidence * 100).toFixed(1) + '%';
            const tagClass = getTagStyle(entity.tag);

            tr.innerHTML = `
                <td class="px-6 py-4 font-mono font-bold">${entity.word}</td>
                <td class="px-6 py-4">
                    <span class="px-2 py-1 rounded text-xs font-bold ${tagClass}">${entity.tag}</span>
                </td>
                <td class="px-6 py-4 font-mono text-outline">${confPercent}</td>
            `;
            entityTableBody.appendChild(tr);
        });

        // 2. XAI Annotated Text
        let activeText = data.text;
        let annotatedHtml = '';
        
        // Very basic string replace for demonstration of XAI token highlighting.
        // In a perfect world, we use start/end offsets, but basic token matching works for the MVP.
        let words = activeText.split(/(\\s+)/);
        words.forEach(word => {
            if (word.trim() === '') {
                annotatedHtml += word;
                return;
            }
            // Check if this word belongs to an entity
            const cleanWord = word.replace(/[^a-zA-Z0-9]/g, '');
            const matchingEntity = data.entities.find(e => e.word.toLowerCase() === cleanWord.toLowerCase() || e.word.includes(cleanWord));
            
            if (matchingEntity) {
                const tagClass = getTagStyle(matchingEntity.tag);
                annotatedHtml += `<span class="px-1 mx-0.5 rounded cursor-help font-semibold ${tagClass}" title="${matchingEntity.tag} (${(matchingEntity.confidence*100).toFixed(1)}%)">${word}</span>`;
            } else {
                annotatedHtml += word;
            }
        });

        annotatedText.innerHTML = annotatedHtml;

        // 3. Explainable AI Summary
        const uniqueTags = Array.from(breakdownTags);
        let summary = `This transcription contains key clinical markers relating to: <strong>${uniqueTags.join(', ')}</strong>.<br><br>`;
        summary += `The <em>Bio_ClinicalBERT</em> engine successfully extracted ${data.entities.length} distinct entity tokens. `;
        if (data.text.length > 0 && selectedImageFile) {
            summary += `The spatial data was extracted accurately from the image via <em>EasyOCR</em> before being fused into the language model pipeline.`;
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
            
            const entityCount = item.entities ? item.entities.length : 0;
            
            div.innerHTML = `
                <div class="flex flex-col gap-1 max-w-[70%]">
                    <p class="text-sm text-on-surface truncate font-medium">"${item.text.substring(0, 60)}..."</p>
                    <span class="text-[10px] text-outline font-medium">${new Date(item.timestamp).toLocaleTimeString()}</span>
                </div>
                <span class="px-3 py-1 bg-primary/10 text-primary border-primary/20 rounded-full text-xs font-bold border">${entityCount} Entities</span>
            `;
            historyList.appendChild(div);
        });
    }

    function clearHistory() {
        localStorage.removeItem('medvisionHistory');
        renderHistory();
    }
});
