
const API = "";

function formatMoney(value) {
    return Number(value).toLocaleString("bs-BA", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }) + " KM";
}

function formatDate(value) {
    if (!value) return "-";

    return new Date(value + "T00:00:00").toLocaleDateString("bs-BA");
}

function showNotification(message, type = "success") {
    const element = document.getElementById("notification");

    element.textContent = message;
    element.className = `notification ${type}`;

    window.scrollTo({ top: 0, behavior: "smooth" });
}

async function getData(endpoint) {
    const response = await fetch(`${API}${endpoint}`);

    if (!response.ok) {
        throw new Error(`Greška prilikom učitavanja: ${endpoint}`);
    }

    return response.json();
}

async function loadOverview() {
    const data = await getData("/finance/overview");

    document.getElementById("balance").textContent =
        formatMoney(data.current_balance);

    const incomeTotal = data.expected_incomes.reduce(
        (sum, income) => sum + income.expected_amount,
        0
    );

    document.getElementById("income-total").textContent =
        formatMoney(incomeTotal);

    document.getElementById("income-count").textContent =
        `${data.expected_incomes.length} evidentiranih uplata`;

    const obligationTotal = data.pending_obligations.reduce(
        (sum, obligation) => sum + obligation.amount,
        0
    );

    document.getElementById("obligation-total").textContent =
        formatMoney(obligationTotal);

    document.getElementById("obligation-count").textContent =
        `${data.pending_obligations.length} aktivnih obaveza`;

    document.getElementById("alert-count").textContent =
        data.active_alerts_count;

    renderIncomes(data.expected_incomes);
    renderObligations(data.pending_obligations);
}

function renderIncomes(incomes) {
    const table = document.getElementById("income-table");

    if (incomes.length === 0) {
        table.innerHTML =
            '<tr><td colspan="4" class="no-data">Nema evidentiranih budućih prihoda.</td></tr>';
        return;
    }

    table.innerHTML = incomes.map(income => {
        const statusText = income.status === "Expected"
            ? "Očekivan"
            : "Zakazan";

        const statusClass = income.status === "Expected"
            ? "status-expected"
            : "status-scheduled";

        return `
            <tr>
                <td><strong>${escapeHTML(income.source)}</strong></td>
                <td>${formatDate(income.expected_date)}</td>
                <td>${formatMoney(income.expected_amount)}</td>
                <td><span class="status ${statusClass}">${statusText}</span></td>
            </tr>
        `;
    }).join("");
}

function renderObligations(obligations) {
    const table = document.getElementById("obligation-table");

    if (obligations.length === 0) {
        table.innerHTML =
            '<tr><td colspan="3" class="no-data">Nema neplaćenih obaveza.</td></tr>';
        return;
    }

    table.innerHTML = obligations.map(obligation => `
        <tr>
            <td><strong>${escapeHTML(obligation.title)}</strong></td>
            <td>${formatDate(obligation.due_date)}</td>
            <td>${formatMoney(obligation.amount)}</td>
        </tr>
    `).join("");
}

async function loadForecast() {
    const data = await getData("/finance/forecast");

    const summary = document.getElementById("forecast-summary");

    if (data.has_shortage) {
        summary.innerHTML = `
            <strong style="color:#df5656">Predviđen finansijski manjak</strong><br>
            Prvi manjak: ${formatDate(data.first_shortage_date)}<br>
            Najveći manjak: ${formatMoney(data.maximum_shortage)}
        `;
    } else {
        summary.innerHTML = `
            <strong style="color:#16a675">Nije predviđen manjak novca</strong><br>
            Početno stanje: ${formatMoney(data.starting_balance)}<br>
            Predviđeno završno stanje: ${formatMoney(data.final_balance)}
        `;
    }

    const timeline = document.getElementById("timeline");

    if (data.timeline.length === 0) {
        timeline.innerHTML =
            '<div class="no-data">Nema događaja za prognozu.</div>';
        return;
    }

    timeline.innerHTML = data.timeline.map(event => {
        const isIncome = event.type === "PRIHOD";

        return `
            <div class="timeline-item">
                <span class="timeline-date">${formatDate(event.date)}</span>
                <span class="${isIncome ? "income-text" : "obligation-text"}">
                    ${isIncome ? "↗" : "↘"} ${escapeHTML(event.description)}
                </span>
                <span class="timeline-amount ${isIncome ? "income-text" : "obligation-text"}">
                    ${isIncome ? "+" : "-"}${formatMoney(event.amount)}
                </span>
            </div>
        `;
    }).join("");
}

async function loadAlerts() {
    const data = await getData("/alerts");

    const container = document.getElementById("alerts-list");

    if (data.alerts.length === 0) {
        container.innerHTML =
            '<div class="no-data">Trenutno nema aktivnih upozorenja.</div>';
        return;
    }

    container.innerHTML = data.alerts.map(alert => `
        <div class="alert-card">
            <strong>Finansijsko upozorenje</strong>
            <p>${escapeHTML(alert.message)}</p>
            <small>
                Pouzdanost indeksa: ${(alert.confidence * 100).toFixed(0)}%
            </small>
        </div>
    `).join("");
}

function escapeHTML(value) {
    return String(value).replace(/[&<>"']/g, character => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
    })[character]);
}

async function refreshDashboard() {
    try {
        await Promise.all([
            loadOverview(),
            loadForecast(),
            loadAlerts()
        ]);
    } catch (error) {
        showNotification(error.message, "error");
    }
}

async function runAgent() {
    const button = document.getElementById("run-agent");

    button.disabled = true;
    button.textContent = "Analiza u toku...";

    try {
        const response = await fetch("/agent/run", {
            method: "POST"
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.detail || "Agent nije mogao izvršiti analizu.");
        }

        showNotification(
            result.message + " " + result.decision.message,
            "success"
        );

        await refreshDashboard();

    } catch (error) {
        showNotification(error.message, "error");
    } finally {
        button.disabled = false;
        button.textContent = "Pokreni analizu →";
    }
}

document.getElementById("run-agent").addEventListener(
    "click",
    runAgent
);

refreshDashboard();
