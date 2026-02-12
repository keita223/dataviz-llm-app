// State
let csvFile = null;
let csvData = null;
let proposals = [];
let dataSummary = null;

// DOM
const sections = {
    1: document.getElementById('step-1'),
    2: document.getElementById('step-2'),
    3: document.getElementById('step-3')
};

const stepIndicators = {
    1: document.getElementById('step-ind-1'),
    2: document.getElementById('step-ind-2'),
    3: document.getElementById('step-ind-3')
};

// Navigation
function goToStep(n) {
    Object.values(sections).forEach(s => s.classList.remove('active'));
    sections[n].classList.add('active');

    Object.entries(stepIndicators).forEach(([key, el]) => {
        el.classList.remove('active', 'done');
        if (parseInt(key) < n) el.classList.add('done');
        if (parseInt(key) === n) el.classList.add('active');
    });
}

// Loading
function showLoading(text) {
    document.getElementById('loading-text').textContent = text;
    document.getElementById('loading-overlay').classList.add('active');
}

function hideLoading() {
    document.getElementById('loading-overlay').classList.remove('active');
}

// Error
function showError(msg) {
    const toast = document.getElementById('error-toast');
    document.getElementById('error-message').textContent = msg;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 5000);
}

// File upload
const fileInput = document.getElementById('csv-file');
const dropZone = document.getElementById('drop-zone');
const fileNameEl = document.getElementById('file-name');

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        csvFile = e.target.files[0];
        fileNameEl.textContent = csvFile.name;
    }
});

dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('dragover');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('dragover');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    if (e.dataTransfer.files.length > 0) {
        csvFile = e.dataTransfer.files[0];
        fileInput.files = e.dataTransfer.files;
        fileNameEl.textContent = csvFile.name;
    }
});

// Form submit -> /api/analyze
document.getElementById('upload-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const problem = document.getElementById('problem').value.trim();
    if (!csvFile || !problem) return;

    // Read CSV content for later use
    csvData = await csvFile.text();

    const formData = new FormData();
    formData.append('problem', problem);
    formData.append('file', csvFile);

    showLoading('Analyse des donnees en cours...');

    try {
        const res = await fetch('/api/analyze', {
            method: 'POST',
            body: formData
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Erreur serveur');
        }

        const data = await res.json();
        dataSummary = data.data_summary;
        proposals = data.proposals;

        renderSummary(dataSummary);
        renderProposals(proposals);
        goToStep(2);
    } catch (err) {
        showError(err.message);
    } finally {
        hideLoading();
    }
});

// Render data summary
function renderSummary(summary) {
    document.getElementById('insights').textContent = summary.insights || 'Aucun insight disponible.';

    const colsEl = document.getElementById('columns-info');
    colsEl.innerHTML = '';
    const cols = summary.relevant_columns || [];
    cols.forEach(col => {
        const tag = document.createElement('span');
        tag.className = 'column-tag';
        tag.textContent = col;
        colsEl.appendChild(tag);
    });
}

// Render proposals
function renderProposals(proposals) {
    const grid = document.getElementById('proposals-grid');
    grid.innerHTML = '';

    proposals.forEach((p, i) => {
        const card = document.createElement('div');
        card.className = 'proposal-card';
        card.innerHTML = `
            <span class="card-type">${p.chart_type}</span>
            <h4>${p.title}</h4>
            <div class="card-variables">Variables : ${p.variables.join(', ')}</div>
            <div class="card-justification">${p.justification}</div>
        `;
        card.addEventListener('click', () => selectProposal(i, card));
        grid.appendChild(card);
    });
}

// Select proposal -> /api/generate
async function selectProposal(index, cardEl) {
    // Highlight
    document.querySelectorAll('.proposal-card').forEach(c => c.classList.remove('selected'));
    cardEl.classList.add('selected');

    const proposal = proposals[index];

    showLoading('Generation de la visualisation...');

    try {
        const res = await fetch('/api/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                proposal: proposal,
                csv_data: csvData
            })
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Erreur serveur');
        }

        const data = await res.json();
        renderVisualization(data.plotly_json);
        renderCode(data.code);
        goToStep(3);
    } catch (err) {
        showError(err.message);
    } finally {
        hideLoading();
    }
}

// Render Plotly chart
function renderVisualization(plotlyJson) {
    const chartDiv = document.getElementById('plotly-chart');
    chartDiv.innerHTML = '';

    const layout = plotlyJson.layout || {};
    layout.autosize = true;
    layout.margin = layout.margin || { l: 60, r: 30, t: 60, b: 60 };

    Plotly.newPlot(chartDiv, plotlyJson.data, layout, {
        responsive: true,
        displayModeBar: true,
        displaylogo: false
    });
}

// Render code
function renderCode(code) {
    document.getElementById('generated-code').textContent = code;
}

// Back buttons
document.getElementById('btn-back-1').addEventListener('click', () => goToStep(1));
document.getElementById('btn-back-2').addEventListener('click', () => goToStep(2));
document.getElementById('btn-restart').addEventListener('click', () => {
    csvFile = null;
    csvData = null;
    proposals = [];
    dataSummary = null;
    document.getElementById('upload-form').reset();
    fileNameEl.textContent = '';
    goToStep(1);
});
