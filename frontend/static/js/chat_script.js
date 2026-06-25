document.addEventListener("DOMContentLoaded", () => {
    // UI Elements
    const htmlElement = document.documentElement;
    
    const sidebar = document.getElementById('sidebar');
    const sidebarToggleBtn = document.getElementById('sidebar-toggle-btn');
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



    // Sidebar Toggle (Mobile)
    if (sidebarToggleBtn) {
        sidebarToggleBtn.addEventListener('click', () => {
            sidebar.classList.toggle('-translate-x-full');
        });
    }

    // Auto-resize textarea
    chatInput.addEventListener('input', function() {
        this.style.height = '48px';
        this.style.height = (this.scrollHeight) + 'px';
        if (this.value.trim() === '') {
            chatSubmitBtn.disabled = true;
        } else {
            chatSubmitBtn.disabled = false;
        }
    });

    // Enter to submit (Shift+Enter for newline)
    chatInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if (this.value.trim() !== '') {
                chatForm.dispatchEvent(new Event('submit'));
            }
        }
    });

    // Generate UUID
    function generateUUID() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
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
            sessionList.innerHTML = '<div class="text-xs text-outline italic px-3">No previous chats.</div>';
            return;
        }

        sessions.forEach(session => {
            const btn = document.createElement('button');
            btn.className = `w-full text-left px-3 py-2 rounded-lg text-sm truncate transition-colors flex items-center gap-2 group ${session.id === currentSessionId ? 'bg-surface-container-high text-on-surface font-bold' : 'text-on-surface-variant hover:bg-surface-container'}`;
            
            // Limit title length
            const title = session.title || "New Chat";
            
            btn.innerHTML = `
                <span class="material-symbols-outlined text-[16px] opacity-70" data-icon="chat_bubble">chat_bubble</span>
                <span class="flex-1 truncate">${title}</span>
                <span class="material-symbols-outlined text-[16px] opacity-0 group-hover:opacity-100 hover:text-error transition-all" data-action="delete" title="Delete Chat" data-icon="delete">delete</span>
            `;

            btn.addEventListener('click', (e) => {
                if (e.target.dataset.action === 'delete') {
                    deleteSession(session.id);
                    e.stopPropagation();
                } else {
                    loadSession(session.id);
                }
            });

            sessionList.appendChild(btn);
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
            sidebar.classList.add('-translate-x-full');
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
            sidebar.classList.add('-translate-x-full');
        }
    }

    newChatBtn.addEventListener('click', startNewChat);

    function appendMessageToUI(role, content) {
        const div = document.createElement('div');
        div.className = `flex gap-4 w-full ${role === 'user' ? 'justify-end' : 'justify-start'}`;
        
        const innerDiv = document.createElement('div');
        innerDiv.className = `max-w-[85%] lg:max-w-[75%] p-4 sm:p-5 rounded-xl shadow-sm border leading-relaxed ${role === 'user' ? 'bg-surface-container text-on-surface rounded-tr-sm border-outline-variant/30' : 'bg-surface text-on-surface rounded-tl-sm border-outline-variant/50'}`;
        
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

        chatInput.value = '';
        chatInput.style.height = '48px';
        chatInput.disabled = true;
        chatSubmitBtn.disabled = true;

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
        
        loadingDiv.innerHTML = `<div class="max-w-[85%] p-4 rounded-xl rounded-tl-sm bg-surface text-on-surface border border-outline-variant/50 flex items-center h-14 gap-4"><div class="flex gap-1 items-center shrink-0"><div class="w-2 h-2 bg-primary/70 rounded-full animate-bounce"></div><div class="w-2 h-2 bg-primary/70 rounded-full animate-bounce" style="animation-delay: 0.1s"></div><div class="w-2 h-2 bg-primary/70 rounded-full animate-bounce" style="animation-delay: 0.2s"></div></div><span class="loading-msg-text text-xs font-label text-outline tracking-wider uppercase transition-opacity duration-300 w-48">${loadingMessages[0]}</span></div>`;
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
                    if(loadingDiv.parentNode && msgSpan) {
                        msgIndex = (msgIndex + 1) % loadingMessages.length;
                        msgSpan.textContent = loadingMessages[msgIndex];
                        msgSpan.style.opacity = '1';
                    }
                }, 300);
            }
        }, 2000);

        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ messages: session.messages })
            });

            if (!response.ok) throw new Error('Chat API failed');
            
            loadingDiv.remove();
            
            // Create Assistant Message container
            const asstNode = appendMessageToUI('assistant', '');
            let assistantMessage = "";
            
            const reader = response.body.getReader();
            const decoder = new TextDecoder('utf-8');
            let buffer = "";
            
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                
                buffer += decoder.decode(value, {stream: true});
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
                                    contextSourcesList.innerHTML = '<li class="text-xs text-primary font-bold">Foundational LLM Knowledge</li>';
                                    contextSnippet.innerHTML = '<span class="italic text-on-surface-variant leading-relaxed text-sm">Response generated using the pre-trained medical reasoning weights of the LLM. No localized clinical documents were required for this specific query.</span>';
                                } else {
                                    data.sources.forEach(src => {
                                        const li = document.createElement('li');
                                        li.textContent = src;
                                        contextSourcesList.appendChild(li);
                                    });
                                    contextSnippet.textContent = data.context_preview || '';
                                }
                            }
                            
                            // Handle Error Payload
                            if (data.error) {
                                assistantMessage += `\n**Error:** ${data.error}`;
                                asstNode.innerHTML = `<div class="prose prose-sm dark:prose-invert max-w-none text-error">${marked.parse(assistantMessage)}</div>`;
                            } 
                            
                            // Handle Text Payload
                            if (data.text) {
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
    });

    // Initial render
    renderSidebar();
    chatInput.disabled = true;
    chatSubmitBtn.disabled = true;
    setTimeout(() => {
        chatInput.disabled = false;
    }, 100);

});
