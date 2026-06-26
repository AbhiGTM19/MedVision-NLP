document.addEventListener("DOMContentLoaded", () => {
    // UI Elements
    const htmlElement = document.documentElement;

    const leftSidebarWrapper = document.getElementById('left-sidebar-wrapper');
    const mobileSidebarToggleBtn = document.getElementById('mobile-sidebar-toggle-btn');
    const leftSidebarToggleBtn = document.getElementById('left-sidebar-toggle-btn');
    const leftToggleIcon = document.getElementById('left-toggle-icon');

    const rightSidebarWrapper = document.getElementById('right-sidebar-wrapper');
    const rightSidebarToggleBtn = document.getElementById('right-sidebar-toggle-btn');
    const rightToggleIcon = document.getElementById('right-toggle-icon');
    const newChatBtn = document.getElementById('new-chat-btn');
    const sessionList = document.getElementById('session-list');

    const chatMessages = document.getElementById('chat-messages');
    const emptyState = document.getElementById('empty-state');
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const chatSubmitBtn = document.getElementById('chat-submit-btn');

    const contextEmptyState = document.getElementById('context-empty-state');
    const contextContent = document.getElementById('context-content');
    const contextSourcesList = document.getElementById('context-sources-list');
    const contextSnippet = document.getElementById('context-snippet');

    // State
    let currentSessionId = null;
    let sessions = JSON.parse(localStorage.getItem('medvision_chat_sessions') || '[]');

    // --- Custom Marked.js Renderer ---
    const renderer = {
        blockquote(tokenOrQuote) {
            let quote = typeof tokenOrQuote === 'string' ? tokenOrQuote : (tokenOrQuote.text || '');
            // Strip out surrounding <p> tags from quote to parse content easily
            let text = quote.replace(/<\/?p>/g, '').trim();

            let type = 'note';
            let icon = 'info';
            let title = 'Note';

            // Match GFM alert syntax
            if (text.startsWith('[!NOTE]')) {
                type = 'note'; icon = 'info'; title = 'Note';
                text = text.replace(/\[!NOTE\]\s*<br>\s*/, '').replace(/\[!NOTE\]\s*/, '');
            } else if (text.startsWith('[!IMPORTANT]')) {
                type = 'important'; icon = 'priority_high'; title = 'Important';
                text = text.replace(/\[!IMPORTANT\]\s*<br>\s*/, '').replace(/\[!IMPORTANT\]\s*/, '');
            } else if (text.startsWith('[!WARNING]')) {
                type = 'warning'; icon = 'warning'; title = 'Warning';
                text = text.replace(/\[!WARNING\]\s*<br>\s*/, '').replace(/\[!WARNING\]\s*/, '');
            } else if (text.startsWith('[!CAUTION]')) {
                type = 'caution'; icon = 'error'; title = 'Caution';
                text = text.replace(/\[!CAUTION\]\s*<br>\s*/, '').replace(/\[!CAUTION\]\s*/, '');
            } else if (text.startsWith('[!TIP]')) {
                type = 'tip'; icon = 'lightbulb'; title = 'Tip';
                text = text.replace(/\[!TIP\]\s*<br>\s*/, '').replace(/\[!TIP\]\s*/, '');
            }

            return `
                <div class="callout callout-${type} my-4 p-4 border-l-4 rounded-r-lg flex flex-col gap-1">
                    <div class="flex items-center gap-2 font-semibold">
                        <span class="material-symbols-outlined select-none text-[20px]" aria-hidden="true">${icon}</span>
                        <span>${title}</span>
                    </div>
                    <div class="type-body">${text}</div>
                </div>
            `;
        },
        heading(tokenOrText, levelFallback) {
            const text = typeof tokenOrText === 'string' ? tokenOrText : (tokenOrText.text || '');
            const level = typeof tokenOrText === 'string' ? levelFallback : (tokenOrText.depth || 1);
            const tag = `h${level}`;
            let icon = '';

            // Add specific icons based on the heading text for structured medical sections
            const lowerText = text.toLowerCase();
            if (lowerText.includes('overview') || lowerText.includes('summary')) {
                icon = '<span class="material-symbols-outlined select-none text-primary text-[24px]" aria-hidden="true">summarize</span>';
            } else if (lowerText.includes('key point')) {
                icon = '<span class="material-symbols-outlined select-none text-primary text-[24px]" aria-hidden="true">checklist</span>';
            } else if (lowerText.includes('treatment') || lowerText.includes('diagnosis')) {
                icon = '<span class="material-symbols-outlined select-none text-primary text-[24px]" aria-hidden="true">medication</span>';
            } else if (lowerText.includes('reference') || lowerText.includes('citation')) {
                icon = '<span class="material-symbols-outlined select-none text-primary text-[24px]" aria-hidden="true">menu_book</span>';
            }

            // For h2s, render them as flex containers with icons if present
            if (level === 2 && icon) {
                return `<${tag} class="section-header type-h2 text-primary flex items-center gap-2 mt-8 mb-4 border-b border-outline-variant/30 pb-2">
                    ${icon}
                    <span>${text}</span>
                </${tag}>`;
            }

            return `<${tag} class="type-h${level} mt-6 mb-3">${text}</${tag}>`;
        },
        table(tokenOrHeader, bodyFallback) {
            // For marked v13+, table rendering needs to process tokens if we override it,
            // which can be complex since we must parse child tokens.
            // If it's v13+, let's skip overriding table or handle it carefully.
            // Actually, for tables, returning false in the renderer tells marked to use default!
            // Wait, returning false in a renderer function uses default renderer in older versions, 
            // but we can just let it fallback by not implementing `table` if it's token-based.
            if (typeof tokenOrHeader !== 'string') {
                return false; // Fallback to default renderer
            }
            const header = tokenOrHeader;
            const body = bodyFallback;
            return `
                <div class="overflow-x-auto w-full my-6 rounded-xl border border-outline-variant/50 shadow-sm">
                    <table class="w-full text-left border-collapse">
                        <thead class="bg-surface-container text-on-surface font-semibold border-b border-outline-variant/50">
                            ${header}
                        </thead>
                        <tbody class="divide-y divide-outline-variant/30">
                            ${body}
                        </tbody>
                    </table>
                </div>
            `;
        },
        hr(token) {
            if (typeof token !== 'string' && token) {
                // v13+ fallback to default or just return our custom hr
            }
            return `<hr class="my-8 border-t border-outline-variant/50" />`;
        }
    };

    marked.use({ renderer });

    // Initialize Heartbeat Lottie Animation
    const lottieContainer = document.getElementById('lottie-heartbeat');
    if (lottieContainer && typeof lottie !== 'undefined') {
        lottie.loadAnimation({
            container: lottieContainer,
            renderer: 'svg',
            loop: true,
            autoplay: true,
            path: '/static/assets/animations/Heartbeat Lottie Animation.json'
        });
    }

    // Initialize Doctor Lottie Animation
    const doctorContainer = document.getElementById('lottie-doctor');
    if (doctorContainer && typeof lottie !== 'undefined') {
        lottie.loadAnimation({
            container: doctorContainer,
            renderer: 'svg',
            loop: true,
            autoplay: true,
            path: '/static/assets/animations/Doctor.json'
        });
    }


    // Sidebar Toggle (Mobile)
    if (mobileSidebarToggleBtn) {
        mobileSidebarToggleBtn.addEventListener('click', () => {
            leftSidebarWrapper.classList.toggle('-translate-x-full');
        });
    }

    // Sidebar Toggles (Desktop)
    if (leftSidebarToggleBtn) {
        leftSidebarToggleBtn.addEventListener('click', () => {
            leftSidebarWrapper.classList.toggle('w-72');
            leftSidebarWrapper.classList.toggle('w-0');

            if (leftSidebarWrapper.classList.contains('w-0')) {
                leftToggleIcon.textContent = 'chevron_right';
                leftSidebarToggleBtn.classList.remove('bg-white', 'text-outline', 'hover:text-primary', 'hover:bg-surface-container');
                leftSidebarToggleBtn.classList.add('bg-[#000]', 'text-white', 'hover:bg-gray-800');
            } else {
                leftToggleIcon.textContent = 'chevron_left';
                leftSidebarToggleBtn.classList.remove('bg-[#000]', 'text-white', 'hover:bg-gray-800');
                leftSidebarToggleBtn.classList.add('bg-white', 'text-outline', 'hover:text-primary', 'hover:bg-surface-container');
            }
        });
    }

    if (rightSidebarToggleBtn) {
        rightSidebarToggleBtn.addEventListener('click', () => {
            rightSidebarWrapper.classList.toggle('w-80');
            rightSidebarWrapper.classList.toggle('w-0');

            if (rightSidebarWrapper.classList.contains('w-0')) {
                rightToggleIcon.textContent = 'chevron_left';
                rightSidebarToggleBtn.classList.remove('bg-white', 'text-outline', 'hover:text-primary', 'hover:bg-surface-container');
                rightSidebarToggleBtn.classList.add('bg-[#000]', 'text-white', 'hover:bg-gray-800');
            } else {
                rightToggleIcon.textContent = 'chevron_right';
                rightSidebarToggleBtn.classList.remove('bg-[#000]', 'text-white', 'hover:bg-gray-800');
                rightSidebarToggleBtn.classList.add('bg-white', 'text-outline', 'hover:text-primary', 'hover:bg-surface-container');
            }
        });
    }

    // Auto-resize textarea
    chatInput.addEventListener('input', function () {
        this.style.height = '48px';
        this.style.height = (this.scrollHeight) + 'px';
        if (this.value.trim() === '') {
            chatSubmitBtn.disabled = true;
        } else {
            chatSubmitBtn.disabled = false;
        }
    });

    // Enter to submit (Shift+Enter for newline)
    chatInput.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if (this.value.trim() !== '') {
                chatForm.dispatchEvent(new Event('submit'));
            }
        }
    });

    // Generate UUID
    function generateUUID() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
            var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }

    // Save Sessions
    function saveSessions() {
        localStorage.setItem('medvision_chat_sessions', JSON.stringify(sessions));
        renderSidebar();
    }

    // Render Sidebar
    function renderSidebar() {
        sessionList.innerHTML = '';
        if (sessions.length === 0) {
            sessionList.innerHTML = '<div class="type-caption text-outline italic px-3 pt-4 text-center">No previous chats.</div>';
            return;
        }

        sessions.forEach(session => {
            const item = document.createElement('div');
            item.className = `w-full text-left px-3 pb-2 pt-2 rounded-lg type-ui truncate transition-colors flex items-center gap-2 group cursor-pointer ${session.id === currentSessionId ? 'bg-surface-container-high text-on-surface' : 'text-on-surface-variant font-medium hover:bg-surface-container'}`;

            // Limit title length
            const title = session.title || "New Chat";

            item.innerHTML = `
                <span class="material-symbols-outlined text-[16px] opacity-70" data-icon="chat_bubble">chat_bubble</span>
                <span class="flex-1 truncate">${title}</span>
                <button class="material-symbols-outlined text-[16px] opacity-0 group-hover:opacity-100 hover:text-error transition-all focus:outline-none" data-action="delete" title="Delete Chat" data-icon="delete">delete</button>
            `;

            item.addEventListener('click', (e) => {
                if (e.target.closest('button[data-action="delete"]') || e.target.dataset.action === 'delete') {
                    deleteSession(session.id);
                    e.stopPropagation();
                } else {
                    loadSession(session.id);
                }
            });

            sessionList.appendChild(item);
        });
    }

    // Delete Session
    function deleteSession(id) {
        sessions = sessions.filter(s => s.id !== id);
        if (currentSessionId === id) {
            startNewChat();
        } else {
            saveSessions();
        }
    }

    // Start New Chat
    function startNewChat() {
        currentSessionId = null;
        chatMessages.innerHTML = '';
        chatMessages.appendChild(emptyState);
        emptyState.classList.remove('hidden');

        contextEmptyState.classList.remove('hidden');
        contextContent.classList.add('hidden');

        chatInput.value = '';
        chatInput.style.height = '48px';
        chatSubmitBtn.disabled = true;
        renderSidebar();

        // On mobile, close sidebar when clicking new chat
        if (window.innerWidth < 768) {
            leftSidebarWrapper.classList.add('-translate-x-full');
        }
    }

    // Load Session
    function loadSession(id) {
        const session = sessions.find(s => s.id === id);
        if (!session) return;

        currentSessionId = id;
        emptyState.classList.add('hidden');
        chatMessages.innerHTML = '';

        session.messages.forEach(msg => {
            appendMessageToUI(msg.role, msg.content);
        });

        // Reset context panel
        contextEmptyState.classList.remove('hidden');
        contextContent.classList.add('hidden');

        renderSidebar();

        // On mobile, close sidebar when selecting a chat
        if (window.innerWidth < 768) {
            leftSidebarWrapper.classList.add('-translate-x-full');
        }
    }

    newChatBtn.addEventListener('click', startNewChat);

    function appendMessageToUI(role, content) {
        const div = document.createElement('div');
        div.className = `flex gap-4 w-full ${role === 'user' ? 'justify-end' : 'justify-start'}`;

        const innerDiv = document.createElement('div');
        innerDiv.className = `type-body max-w-[85%] lg:max-w-[75%] p-4 sm:p-5 rounded-xl shadow-sm border ${role === 'user' ? 'bg-surface-container text-on-surface rounded-tr-sm border-outline-variant/30' : 'bg-surface text-on-surface rounded-tl-sm border-outline-variant/50'}`;

        if (role === 'assistant') {
            innerDiv.innerHTML = `<div class="prose prose-sm dark:prose-invert max-w-none font-body">${marked.parse(content)}</div>`;
        } else {
            innerDiv.textContent = content; // pure text for user
        }

        div.appendChild(innerDiv);
        chatMessages.appendChild(div);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return innerDiv;
    }

    // Handle Chat Submit
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const input = chatInput.value.trim();
        if (!input) return;

        chatInput.value = '';
        chatInput.style.height = '48px';
        chatInput.disabled = true;
        chatSubmitBtn.disabled = true;

        await processChatInput(input);
    });

    async function processChatInput(input) {
        // If no session, create one
        if (!currentSessionId) {
            currentSessionId = generateUUID();
            sessions.unshift({
                id: currentSessionId,
                title: input.substring(0, 30) + (input.length > 30 ? '...' : ''),
                messages: []
            });
            emptyState.classList.add('hidden');
        }

        const session = sessions.find(s => s.id === currentSessionId);

        // Add to UI and State
        appendMessageToUI('user', input);
        session.messages.push({ role: 'user', content: input });
        saveSessions();

        // Loading state
        const loadingDiv = document.createElement('div');
        loadingDiv.className = `flex gap-4 w-full justify-start`;

        const loadingMessages = [
            "Analyzing clinical query...",
            "Searching National Guidelines...",
            "Synthesizing RAG context...",
            "Applying safety guardrails..."
        ];
        let msgIndex = 0;

        loadingDiv.innerHTML = `<div class="max-w-[85%] pl-6 pr-5 py-4 rounded-xl rounded-tl-sm bg-surface text-on-surface border border-outline-variant/50 flex items-center h-12"><span class="loading-msg-text type-caption tracking-wider uppercase transition-opacity duration-300 w-auto whitespace-nowrap overflow-hidden text-ellipsis">${loadingMessages[0]}</span></div>`;
        chatMessages.appendChild(loadingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        const loaderInterval = setInterval(() => {
            if (!loadingDiv.parentNode) {
                clearInterval(loaderInterval);
                return;
            }
            const msgSpan = loadingDiv.querySelector('.loading-msg-text');
            if (msgSpan) {
                msgSpan.style.opacity = '0';
                setTimeout(() => {
                    if (loadingDiv.parentNode && msgSpan) {
                        msgIndex = (msgIndex + 1) % loadingMessages.length;
                        msgSpan.textContent = loadingMessages[msgIndex];
                        msgSpan.style.opacity = '1';
                    }
                }, 300);
            }
        }, 1200);

        // Ensure all loading messages are shown before generating a response (4.2 seconds UX delay)
        await new Promise(resolve => setTimeout(resolve, 4200));

        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ messages: session.messages })
            });

            if (!response.ok) throw new Error('Chat API failed');

            let asstNode = null;
            let assistantMessage = "";

            const reader = response.body.getReader();
            const decoder = new TextDecoder('utf-8');
            let buffer = "";

            while (true) {
                const { done, value } = await reader.read();

                if (done) {
                    if (!asstNode) {
                        loadingDiv.remove();
                        asstNode = appendMessageToUI('assistant', '');
                    }
                    break;
                }

                buffer += decoder.decode(value, { stream: true });
                let lines = buffer.split('\n\n');

                buffer = lines.pop() || "";

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const dataStr = line.substring(6);
                        try {
                            const data = JSON.parse(dataStr);

                            // Handle Context Sources Payload
                            if (data.sources) {
                                contextEmptyState.classList.add('hidden');
                                contextContent.classList.remove('hidden');
                                contextSourcesList.innerHTML = '';
                                if (data.sources.length === 0) {
                                    contextSourcesList.innerHTML = '<li class="type-caption text-primary">Foundational LLM Knowledge</li>';
                                    contextSnippet.innerHTML = '<span class="type-body italic">Response generated using the pre-trained medical reasoning weights of the LLM. No localized clinical documents were required for this specific query.</span>';
                                } else {
                                    data.sources.forEach((src, idx) => {
                                        const li = document.createElement('li');
                                        li.textContent = `[${idx + 1}] ${src}`;
                                        contextSourcesList.appendChild(li);
                                    });
                                    contextSnippet.textContent = data.context_preview || '';
                                }
                            }

                            // Handle Error Payload
                            if (data.error) {
                                if (!asstNode) {
                                    loadingDiv.remove();
                                    asstNode = appendMessageToUI('assistant', '');
                                }
                                assistantMessage += `\n**Error:** ${data.error}`;
                                asstNode.innerHTML = `<div class="prose prose-sm dark:prose-invert max-w-none text-error">${marked.parse(assistantMessage)}</div>`;
                            }

                            // Handle Text Payload
                            if (data.text) {
                                if (!asstNode) {
                                    loadingDiv.remove();
                                    asstNode = appendMessageToUI('assistant', '');
                                }
                                assistantMessage += data.text;
                                asstNode.innerHTML = `<div class="prose prose-sm dark:prose-invert max-w-none font-body">${marked.parse(assistantMessage + ' ▍')}</div>`;
                            }

                            chatMessages.scrollTop = chatMessages.scrollHeight;
                        } catch (e) {
                            console.error("JSON parse error for SSE chunk", e);
                        }
                    }
                }
            }

            // Finalize message without cursor
            asstNode.innerHTML = `<div class="prose prose-sm dark:prose-invert max-w-none font-body">${marked.parse(assistantMessage)}</div>`;

            // Save finalized message
            session.messages.push({ role: 'assistant', content: assistantMessage });
            saveSessions();
        } catch (error) {
            loadingDiv.remove();
            appendMessageToUI('assistant', `**Error:** ${error.message}`);
        } finally {
            chatInput.disabled = false;
            chatInput.focus();
            if (chatInput.value.trim() !== '') chatSubmitBtn.disabled = false;
        }
    }

    // Initial render
    renderSidebar();
    chatInput.disabled = true;
    chatSubmitBtn.disabled = true;
    setTimeout(() => {
        chatInput.disabled = false;

        // Check for initial query from Classification bridge
        const urlParams = new URLSearchParams(window.location.search);
        const initialQuery = urlParams.get('initial_query');
        if (initialQuery) {
            // Clean up the URL so it doesn't re-trigger on refresh
            window.history.replaceState({}, document.title, window.location.pathname);

            // Disable input while processing the programmatic submission
            chatInput.disabled = true;
            chatSubmitBtn.disabled = true;

            // Directly process the query, bypassing DOM event simulations completely
            setTimeout(() => {
                processChatInput(initialQuery);
            }, 300);
        }
    }, 100);

});
