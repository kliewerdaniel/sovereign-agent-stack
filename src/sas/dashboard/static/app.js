// Sovereign Agent Stack — Dashboard JavaScript

document.addEventListener('DOMContentLoaded', () => {
    // ── State ──────────────────────────────────────────────────────────────────
    let sessionId = null;
    let runCount = 0;
    let sseConnected = false;
    const pipelineResults = [];

    // ── DOM References ─────────────────────────────────────────────────────────
    const statusDot = document.getElementById('status-dot');
    const statusText = document.getElementById('status-text');
    const scoreDisplay = document.getElementById('score-display');
    const scoreVerdict = document.getElementById('score-verdict');
    const worldCount = document.getElementById('world-count');
    const runCountEl = document.getElementById('run-count');
    const worldsList = document.getElementById('worlds-list');
    const worldSelect = document.getElementById('world-select');
    const progressStepper = document.getElementById('progress-stepper');
    const pipelineConsole = document.getElementById('pipeline-console');
    const resultsCard = document.getElementById('results-card');
    const resultsGrid = document.getElementById('results-grid');
    const provenanceCard = document.getElementById('provenance-card');
    const provenanceContent = document.getElementById('provenance-content');
    const layersList = document.getElementById('layers-list');
    const chatMessages = document.getElementById('chat-messages');
    const knowledgeResults = document.getElementById('knowledge-results');

    // ── Tab Navigation ─────────────────────────────────────────────────────────
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
            btn.classList.add('active');
            document.getElementById(`tab-${btn.dataset.tab}`).classList.add('active');
        });
    });

    // ── API Helpers ────────────────────────────────────────────────────────────
    async function apiGet(url) {
        const resp = await fetch(url);
        return resp.json();
    }

    async function apiPost(url, data = {}) {
        const resp = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        return resp.json();
    }

    // ── Console Logging ────────────────────────────────────────────────────────
    function logToConsole(message, type = 'info') {
        const line = document.createElement('div');
        line.className = `console-line ${type}`;
        line.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
        pipelineConsole.appendChild(line);
        pipelineConsole.scrollTop = pipelineConsole.scrollHeight;
    }

    function clearConsole() {
        pipelineConsole.innerHTML = '';
    }

    // ── Progress Stepper ───────────────────────────────────────────────────────
    function updateStepper(stages, currentStage) {
        progressStepper.innerHTML = '';
        stages.forEach(stage => {
            const step = document.createElement('div');
            step.className = 'step';
            step.textContent = stage.name;
            if (stage.status === 'complete') step.classList.add('complete');
            else if (stage.status === 'active') step.classList.add('active');
            else if (stage.status === 'error') step.classList.add('error');
            progressStepper.appendChild(step);
        });
    }

    // ── SSE Connection ─────────────────────────────────────────────────────────
    function connectSSE() {
        const evtSource = new EventSource('/api/pipeline/stream');

        evtSource.onopen = () => {
            sseConnected = true;
            statusDot.className = 'status-dot connected';
            statusText.textContent = 'Connected';
            document.getElementById('sse-status').textContent = 'Connected';
        };

        evtSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                handleSSEEvent(data);
            } catch (e) {
                // Keepalive or parse error
            }
        };

        evtSource.onerror = () => {
            sseConnected = false;
            statusDot.className = 'status-dot error';
            statusText.textContent = 'Disconnected';
            document.getElementById('sse-status').textContent = 'Disconnected';
            // Reconnect after delay
            setTimeout(connectSSE, 3000);
        };
    }

    function handleSSEEvent(data) {
        if (data.type === 'progress') {
            logToConsole(`${data.stage}: ${data.message}`);
            updateStepper([
                { name: 'start', status: 'complete' },
                { name: 'world', status: data.stage === 'world' ? 'active' : 'complete' },
                { name: 'task', status: data.stage === 'task' ? 'active' : (data.stage === 'world' ? 'pending' : 'complete') },
                { name: 'pipeline', status: data.stage === 'pipeline' ? 'active' : (['start', 'world', 'task'].includes(data.stage) ? 'pending' : 'complete') },
                { name: 'evaluation', status: data.stage === 'evaluation' ? 'active' : (data.stage === 'complete' ? 'complete' : 'pending') },
                { name: 'complete', status: data.stage === 'complete' ? 'complete' : 'pending' },
            ], data.stage);

            if (data.stage === 'evaluation' && data.data) {
                displayResults(data.data);
            }
        } else if (data.type === 'keepalive') {
            // Ignore
        }
    }

    // ── Display Results ─────────────────────────────────────────────────────────
    function displayResults(data) {
        resultsCard.style.display = 'block';
        resultsGrid.innerHTML = '';

        const metrics = [
            { label: 'Pass@1', value: (data.pass_at_1 * 100).toFixed(1) + '%' },
            { label: 'Mean Score', value: (data.mean_score * 100).toFixed(1) + '%' },
            { label: 'Passed', value: data.passed ? '✓ Yes' : '✗ No' },
            { label: 'Sovereignty', value: data.sovereignty_passed ? '✓ Pass' : '✗ Fail' },
            { label: 'Artifacts', value: data.artifacts?.length || 0 },
            { label: 'Tool Calls', value: data.tool_calls || 0 },
        ];

        metrics.forEach(m => {
            const item = document.createElement('div');
            item.className = 'result-item';
            item.innerHTML = `<div class="result-value">${m.value}</div><div class="result-label">${m.label}</div>`;
            resultsGrid.appendChild(item);
        });

        // Criterion results
        if (data.criterion_results) {
            data.criterion_results.forEach(cr => {
                const item = document.createElement('div');
                item.className = 'result-item';
                item.style.borderLeft = cr.passed ? '3px solid var(--success)' : '3px solid var(--error)';
                item.innerHTML = `<div class="result-value">${cr.score.toFixed(1)}</div><div class="result-label">${cr.criterion_name}</div>`;
                resultsGrid.appendChild(item);
            });
        }

        // Provenance / Audit Trail
        renderProvenance(data);
    }

    // ── Render Provenance Trail ─────────────────────────────────────────────────
    function renderProvenance(data) {
        provenanceCard.style.display = 'block';
        provenanceContent.innerHTML = '';

        // Pipeline chain
        const chainSection = document.createElement('div');
        chainSection.className = 'provenance-section';
        chainSection.innerHTML = '<h4>Pipeline Chain</h4>';
        const chain = document.createElement('div');
        chain.className = 'provenance-chain';
        const stages = ['dataset', 'strategy', 'backtest', 'evaluation', 'report'];
        stages.forEach((stage, i) => {
            const node = document.createElement('div');
            node.className = 'chain-node';
            node.innerHTML = `<span class="chain-dot"></span><span class="chain-label">${stage}</span>`;
            chain.appendChild(node);
            if (i < stages.length - 1) {
                const arrow = document.createElement('span');
                arrow.className = 'chain-arrow';
                arrow.textContent = '→';
                chain.appendChild(arrow);
            }
        });
        chainSection.appendChild(chain);
        provenanceContent.appendChild(chainSection);

        // Artifacts
        const artifactsSection = document.createElement('div');
        artifactsSection.className = 'provenance-section';
        artifactsSection.innerHTML = '<h4>Artifacts</h4>';
        const artifactList = document.createElement('div');
        artifactList.className = 'provenance-artifacts';
        if (data.artifacts && data.artifacts.length > 0) {
            data.artifacts.forEach(a => {
                const tag = document.createElement('span');
                tag.className = 'artifact-tag';
                tag.textContent = a;
                artifactList.appendChild(tag);
            });
        } else {
            artifactList.innerHTML = '<span class="provenance-empty">No artifacts</span>';
        }
        artifactsSection.appendChild(artifactList);
        provenanceContent.appendChild(artifactsSection);

        // Tool calls
        const toolsSection = document.createElement('div');
        toolsSection.className = 'provenance-section';
        toolsSection.innerHTML = '<h4>Tool Calls</h4>';
        const toolsInfo = document.createElement('div');
        toolsInfo.className = 'provenance-tools';
        const toolCount = data.tool_calls || 0;
        toolsInfo.innerHTML = `<span class="tool-count">${toolCount}</span> tool call${toolCount !== 1 ? 's' : ''} executed`;
        toolsSection.appendChild(toolsInfo);
        provenanceContent.appendChild(toolsSection);

        // Criterion results with pass/fail
        const criteriaSection = document.createElement('div');
        criteriaSection.className = 'provenance-section';
        criteriaSection.innerHTML = '<h4>Criteria</h4>';
        const criteriaList = document.createElement('div');
        criteriaList.className = 'provenance-criteria';
        if (data.criterion_results && data.criterion_results.length > 0) {
            data.criterion_results.forEach(cr => {
                const row = document.createElement('div');
                row.className = 'criterion-row';
                const statusClass = cr.passed ? 'criterion-pass' : 'criterion-fail';
                const statusIcon = cr.passed ? '✓' : '✗';
                row.innerHTML = `
                    <span class="criterion-status ${statusClass}">${statusIcon}</span>
                    <span class="criterion-name">${cr.criterion_name}</span>
                    <span class="criterion-score">${cr.score.toFixed(2)}</span>
                `;
                criteriaList.appendChild(row);
            });
        } else {
            criteriaList.innerHTML = '<span class="provenance-empty">No criteria evaluated</span>';
        }
        criteriaSection.appendChild(criteriaList);
        provenanceContent.appendChild(criteriaSection);
    }

    // ── Load Layers ────────────────────────────────────────────────────────────
    async function loadLayers() {
        try {
            const data = await apiGet('/api/layers');
            if (data.error) {
                scoreVerdict.textContent = 'Error loading layers';
                return;
            }

            scoreDisplay.textContent = `${data.owned}/${data.total}`;
            scoreVerdict.textContent = data.verdict;

            layersList.innerHTML = '';
            data.layers.forEach(layer => {
                const item = document.createElement('div');
                item.className = 'layer-item';
                const statusClass = layer.status === 'owned' ? 'status-owned' :
                                   layer.status === 'rented' ? 'status-rented' : 'status-unscored';
                item.innerHTML = `
                    <div>
                        <div class="layer-name">${layer.name}</div>
                        <div class="layer-reasoning">${layer.reasoning}</div>
                    </div>
                    <span class="layer-status ${statusClass}">${layer.status}</span>
                `;
                layersList.appendChild(item);
            });

            document.getElementById('api-status').textContent = 'OK';
        } catch (e) {
            scoreVerdict.textContent = 'API unavailable';
            document.getElementById('api-status').textContent = 'Error';
        }
    }

    // ── Load Worlds ────────────────────────────────────────────────────────────
    async function loadWorlds() {
        try {
            const data = await apiGet('/api/worlds');
            if (data.error) {
                worldsList.innerHTML = `<p>Error: ${data.error}</p>`;
                return;
            }

            worldCount.textContent = data.worlds.length;
            worldsList.innerHTML = '';
            worldSelect.innerHTML = '';

            data.worlds.forEach(world => {
                // Add to worlds list
                const item = document.createElement('div');
                item.className = 'world-item';
                const badgeClass = world.adversarial ? 'badge-adversarial' :
                                  world.difficulty === 'easy' ? 'badge-eadge-easy' :
                                  world.difficulty === 'medium' ? 'badge-medium' : 'badge-hard';
                const badgeText = world.adversarial ? 'Adversarial' : world.difficulty;
                item.innerHTML = `
                    <div class="world-info">
                        <h4>${world.customer}</h4>
                        <div class="world-meta">${world.universe.length} symbols · ${world.estimated_minutes}min · ${world.id}</div>
                    </div>
                    <div class="world-actions">
                        <span class="badge ${badgeClass}">${badgeText}</span>
                        <button class="btn btn-primary" onclick="runWorld('${world.id}')">Run</button>
                    </div>
                `;
                worldsList.appendChild(item);

                // Add to pipeline select
                const option = document.createElement('option');
                option.value = world.id;
                option.textContent = `${world.customer} (${world.id})`;
                worldSelect.appendChild(option);
            });
        } catch (e) {
            worldsList.innerHTML = '<p>API unavailable</p>';
        }
    }

    // ── Run Pipeline ───────────────────────────────────────────────────────────
    async function runPipeline(worldId) {
        clearConsole();
        resultsCard.style.display = 'none';
        provenanceCard.style.display = 'none';
        logToConsole(`Starting pipeline for ${worldId}...`);

        try {
            const result = await apiPost('/api/pipeline/run', { world_id: worldId });
            if (result.error) {
                logToConsole(`Error: ${result.error}`, 'error');
                return;
            }
            logToConsole(`Pipeline accepted. Run ID: ${result.run_id}`);
            runCount++;
            runCountEl.textContent = runCount;
            document.getElementById('run-status').textContent = 'Running';
        } catch (e) {
            logToConsole(`Failed to start: ${e.message}`, 'error');
        }
    }

    // Expose to global scope for onclick handlers
    window.runWorld = runPipeline;

    // ── Knowledge Query ────────────────────────────────────────────────────────
    async function queryKnowledge() {
        const query = document.getElementById('knowledge-query').value;
        knowledgeResults.innerHTML = '<p>Querying...</p>';

        try {
            const data = await apiGet(`/api/knowledge?query=${encodeURIComponent(query)}`);
            if (data.error) {
                knowledgeResults.innerHTML = `<p>Error: ${data.error}</p>`;
                return;
            }

            knowledgeResults.innerHTML = '';
            if (data.results.length === 0) {
                knowledgeResults.innerHTML = '<p>No results found.</p>';
            } else {
                data.results.forEach(r => {
                    const item = document.createElement('div');
                    item.className = 'knowledge-item';
                    item.innerHTML = `<h4>${r.label}</h4><p>${r.content}</p>`;
                    knowledgeResults.appendChild(item);
                });
            }
        } catch (e) {
            knowledgeResults.innerHTML = '<p>API unavailable</p>';
        }
    }

    // ── Chat ───────────────────────────────────────────────────────────────────
    async function sendChat() {
        const input = document.getElementById('chat-input');
        const message = input.value.trim();
        if (!message) return;

        // Add user message
        const userMsg = document.createElement('div');
        userMsg.className = 'chat-message user';
        userMsg.textContent = message;
        chatMessages.appendChild(userMsg);
        input.value = '';
        chatMessages.scrollTop = chatMessages.scrollHeight;

        try {
            const result = await apiPost('/api/agent/chat', {
                message,
                session_id: sessionId,
            });

            if (result.error) {
                const errMsg = document.createElement('div');
                errMsg.className = 'chat-message assistant';
                errMsg.textContent = `Error: ${result.error}`;
                chatMessages.appendChild(errMsg);
            } else {
                sessionId = result.session_id;
                const assistantMsg = document.createElement('div');
                assistantMsg.className = 'chat-message assistant';
                assistantMsg.textContent = result.response;
                chatMessages.appendChild(assistantMsg);
            }
        } catch (e) {
            const errMsg = document.createElement('div');
            errMsg.className = 'chat-message assistant';
            errMsg.textContent = `API unavailable: ${e.message}`;
            chatMessages.appendChild(errMsg);
        }

        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // ── Event Listeners ────────────────────────────────────────────────────────
    document.getElementById('btn-run-portfolio').addEventListener('click', () => runPipeline('qw-portfolio-intel-001'));
    document.getElementById('btn-run-risk-parity').addEventListener('click', () => runPipeline('qw-risk-parity-001'));
    document.getElementById('btn-run-momentum').addEventListener('click', () => runPipeline('qw-momentum-001'));
    document.getElementById('btn-run-pipeline').addEventListener('click', () => runPipeline(worldSelect.value));
    document.getElementById('btn-refresh-layers').addEventListener('click', loadLayers);
    document.getElementById('btn-query-knowledge').addEventListener('click', queryKnowledge);
    document.getElementById('btn-send-chat').addEventListener('click', sendChat);

    document.getElementById('chat-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendChat();
    });

    document.getElementById('knowledge-query').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') queryKnowledge();
    });

    // ── Initialization ─────────────────────────────────────────────────────────
    connectSSE();
    loadLayers();
    loadWorlds();

    // Refresh layers every 30 seconds
    setInterval(loadLayers, 30000);
});
