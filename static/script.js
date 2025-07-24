document.addEventListener('DOMContentLoaded', function () {
    const predictButton = document.getElementById('predict-button');
    const modelInfoButton = document.getElementById('model-info-button');
    const modal = document.getElementById('infoModal');
    const closeButton = document.querySelector('.close-button');
    const okButton = document.querySelector('.modal-ok-button');
    // Select all types of reveal elements
    const revealElements = document.querySelectorAll('.reveal-hero, .reveal-right, .reveal-left');

    // --- Event Listeners ---
    predictButton.addEventListener('click', handlePrediction);
    modelInfoButton.addEventListener('click', handleModelInfo);
    closeButton.addEventListener('click', closeModal);
    okButton.addEventListener('click', closeModal);
    window.addEventListener('click', (event) => {
        if (event.target === modal) {
            closeModal();
        }
    });
    window.addEventListener('scroll', handleScroll);
    handleScroll(); // Trigger once on load to reveal hero section

    // --- Handlers ---
    async function handlePrediction() {
        const reviewText = document.getElementById('reviewInput').value.trim();
        if (!reviewText) {
            showModal('Error', 'Please enter a review before analyzing.');
            return;
        }

        toggleLoader(predictButton, true);
        document.getElementById('result-area').style.display = 'none';

        setTimeout(async () => {
            try {
                const response = await fetch("/predict", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ review: reviewText }),
                });

                if (!response.ok) throw new Error(`Server error: ${response.statusText}`);

                const data = await response.json();
                displayResults(data);

            } catch (error) {
                showModal('Prediction Error', `An error occurred: ${error.message}`);
            } finally {
                toggleLoader(predictButton, false);
            }
        }, 3000); 
    }

    async function handleModelInfo() {
        try {
            const response = await fetch("/model-info");
            if (!response.ok) throw new Error(`Server error: ${response.statusText}`);

            const data = await response.json();
            const formattedData = JSON.stringify(data, null, 2);
            showModal('Model Information', formattedData, true);

        } catch (error) {
            showModal('Error', `Could not fetch model info: ${error.message}`);
        }
    }

    // --- Animation Handler ---
    function handleScroll() {
        const windowHeight = window.innerHeight;
        revealElements.forEach(el => {
            const elementTop = el.getBoundingClientRect().top;
            if (elementTop < windowHeight - 100) { // 100px buffer
                el.classList.add('active');
            }
        });
    }

    // --- UI Functions ---
    function displayResults(data) {
        const verdictEl = document.getElementById('verdict');
        verdictEl.textContent = data.verdict;
        verdictEl.classList.remove('verdict-positive', 'verdict-negative');
        if (data.prediction === 'positive') {
            verdictEl.classList.add('verdict-positive');
        } else {
            verdictEl.classList.add('verdict-negative');
        }

        document.getElementById('confidence').textContent = `${(data.confidence * 100).toFixed(2)}%`;

        const topWordsContainer = document.getElementById('topWords');
        topWordsContainer.innerHTML = ''; // Clear previous
        data.top_words.forEach(word => {
            const tag = document.createElement('span');
            tag.className = 'keyword-tag';
            tag.textContent = word;
            topWordsContainer.appendChild(tag);
        });

        document.getElementById('result-area').style.display = 'block';
    }

    function showModal(title, body, isCode = false) {
        document.getElementById('modalTitle').textContent = title;
        const modalBody = document.getElementById('modalBody');
        
        if (isCode) {
            modalBody.innerHTML = `<pre><code>${body}</code></pre>`;
        } else {
            modalBody.innerHTML = `<p>${body}</p>`;
        }
        
        modal.style.display = 'flex';
    }

    function closeModal() {
        modal.style.display = 'none';
    }

    function toggleLoader(button, isLoading) {
        const btnText = button.querySelector('.btn-text');
        const btnLoader = button.querySelector('.btn-loader');
        if (isLoading) {
            if (btnText) btnText.style.display = 'none';
            if (btnLoader) btnLoader.style.display = 'block';
            button.disabled = true;
        } else {
            if (btnText) btnText.style.display = 'inline';
            if (btnLoader) btnLoader.style.display = 'none';
            button.disabled = false;
        }
    }
});