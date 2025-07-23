document.addEventListener('DOMContentLoaded', function() {
    // Mobile menu toggle
    const menuButton = document.getElementById('mobile-menu-button');
    const mobileMenu = document.getElementById('mobile-menu');
    menuButton.addEventListener('click', () => {
        mobileMenu.classList.toggle('hidden');
    });
});

// Hide all response boxes
function hideAllBoxes() {
    document.getElementById('responseBox').style.display = 'none';
    document.getElementById('modelInfoBox').style.display = 'none';
}

// Show a specific box
function showBox(boxId) {
    hideAllBoxes();
    document.getElementById(boxId).style.display = 'block';
}

async function sendReview() {
    const reviewText = document.getElementById("reviewInput").value.trim();
    const loader = document.getElementById("loader");

    if (!reviewText) {
        alert("Please enter a review.");
        return;
    }

    loader.style.display = "block";
    hideAllBoxes();

    try {
        const response = await fetch("/predict", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ review: reviewText }),
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        loader.style.display = "none";

        // Populate verdict and confidence
        document.getElementById("verdict").innerText = data.verdict;
        document.getElementById("confidence").innerText = `${(data.confidence * 100).toFixed(2)}%`;
        
        // Populate top words as tags
        const topWordsContainer = document.getElementById("topWords");
        topWordsContainer.innerHTML = ''; // Clear previous words
        data.top_words.forEach(word => {
            const tag = document.createElement('span');
            tag.className = 'word-tag';
            tag.innerText = word;
            topWordsContainer.appendChild(tag);
        });

        showBox('responseBox');

    } catch (err) {
        loader.style.display = "none";
        alert("Error analyzing review: " + err.message);
    }
}

async function getModelInfo() {
    const loader = document.getElementById("loader");
    
    loader.style.display = "block";
    hideAllBoxes();

    try {
        const response = await fetch("/model-info");
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        loader.style.display = "none";
        
        // Format the JSON data for pretty printing
        document.getElementById("modelInfoContent").innerText = JSON.stringify(data, null, 2);
        showBox('modelInfoBox');

    } catch (err) {
        loader.style.display = "none";
        alert("Error fetching model info: " + err.message);
    }
}