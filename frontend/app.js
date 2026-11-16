
const API = "";

// ==========================================
// POMOCNE FUNKCIJE
// ==========================================

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

function todayString() {
    const now = new Date();
    const localDate = new Date(
        now.getTime() - now.getTimezoneOffset() * 60000
    );

    return localDate.toISOString().split("T")[0];
}

function showNotification(message, type = "success") {
    const element = document.getElementById("notification");

    element.textContent = message;
    element.className = `notification ${type}`;

    window.scrollTo({ top: 0, behavior: "smooth" });
}

async function requestData(endpoint, options = {}) {
    const response = await fetch(`${API}${endpoint}`, options);

    const result = await response.json();

    if (!response.ok) {
        throw new Error(
            result.detail || "Došlo je do greške prilikom komunikacije s backendom."
        );
    }

    return result;
}

async function getData(endpoint) {
    return requestData(endpoint);
}

async function postData(endpoint, data) {
    return requestData(endpoint, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(data)
    });
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


// ==========================================
// FINANSIJSKI PREGLED
// ==========================================

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
    renderReceiveIncomeOptions(data.expected_incomes);
}


// ==========================================
// PRIKAZ PRIHODA
// ==========================================

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
                <td>
                    <span class="status ${statusClass}">
                        ${statusText}
                    </span>
                </td>
            </tr>
        `;
    }).join("");
}


// ==========================================
// PRIKAZ OBAVEZA
// ==========================================

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


// ==========================================
// IZBOR PRIHODA ZA EVIDENTIRANJE UPLATE
// ==========================================

function renderReceiveIncomeOptions(incomes) {
    const select = document.getElementById("receive-income-select");

    const previousValue = select.value;

    const availableIncomes = incomes.filter(
        income => income.status === "Expected"
    );

    select.innerHTML = `
        <option value="">Odaberite prihod...</option>
        ${availableIncomes.map(income => `
            <option
                value="${income.id}"
                data-amount="${income.expected_amount}"
            >
                ${escapeHTML(income.source)}
                - ${formatMoney(income.expected_amount)}
                (${formatDate(income.expected_date)})
            </option>
        `).join("")}
    `;

    if (
        previousValue &&
        availableIncomes.some(
            income => String(income.id) === previousValue
        )
    ) {
        select.value = previousValue;
    }

    updateActualAmount();
}

function updateActualAmount() {
    const select = document.getElementById("receive-income-select");
    const amountInput = document.getElementById("actual-amount");

    const selectedOption = select.options[select.selectedIndex];

    if (selectedOption && selectedOption.dataset.amount) {
        amountInput.value = selectedOption.dataset.amount;
    }
}


// ==========================================
// FINANSIJSKA PROGNOZA
// ==========================================

async function loadForecast() {
    const data = await getData("/finance/forecast");

    const summary = document.getElementById("forecast-summary");

    if (data.has_shortage) {
        summary.innerHTML = `
            <strong style="color:#df5656">
                Predviđen finansijski manjak
            </strong><br>
            Prvi manjak: ${formatDate(data.first_shortage_date)}<br>
            Najveći manjak: ${formatMoney(data.maximum_shortage)}
        `;
    } else {
        summary.innerHTML = `
            <strong style="color:#16a675">
                Nije predviđen manjak novca
            </strong><br>
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
                <span class="timeline-date">
                    ${formatDate(event.date)}
                </span>

                <span class="${isIncome ? "income-text" : "obligation-text"}">
                    ${isIncome ? "↗" : "↘"}
                    ${escapeHTML(event.description)}
                </span>

                <span class="timeline-amount ${isIncome ? "income-text" : "obligation-text"}">
                    ${isIncome ? "+" : "-"}${formatMoney(event.amount)}
                </span>
            </div>
        `;
    }).join("");
}


// ==========================================
// UPOZORENJA AGENTA
// ==========================================

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


// ==========================================
// OSVJEZAVANJE DASHBOARD-A
// ==========================================

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


// ==========================================
// DODAVANJE OCEKIVANOG PRIHODA
// ==========================================

async function createIncome(event) {
    event.preventDefault();

    const button = event.submitter;
    button.disabled = true;
    button.textContent = "Dodavanje...";

    try {
        const request = {
            source_name: document.getElementById("income-source").value.trim(),
            expected_date: document.getElementById("income-date").value,
            expected_amount: Number(
                document.getElementById("income-amount").value
            )
        };

        const result = await postData("/incomes", request);

        document.getElementById("income-form").reset();

        await refreshDashboard();

        showNotification(
            result.message + " Agent je ponovo izvršio analizu.",
            "success"
        );

    } catch (error) {
        showNotification(error.message, "error");
    } finally {
        button.disabled = false;
        button.textContent = "Dodaj prihod";
    }
}


// ==========================================
// DODAVANJE FINANSIJSKE OBAVEZE
// ==========================================

async function createObligation(event) {
    event.preventDefault();

    const button = event.submitter;
    button.disabled = true;
    button.textContent = "Dodavanje...";

    try {
        const request = {
            title: document.getElementById("obligation-title").value.trim(),
            amount: Number(
                document.getElementById("obligation-amount").value
            ),
            due_date: document.getElementById("obligation-date").value
        };

        const result = await postData("/obligations", request);

        document.getElementById("obligation-form").reset();

        await refreshDashboard();

        showNotification(
            result.message + " Agent je ponovo izvršio analizu.",
            "success"
        );

    } catch (error) {
        showNotification(error.message, "error");
    } finally {
        button.disabled = false;
        button.textContent = "Dodaj obavezu";
    }
}


// ==========================================
// EVIDENTIRANJE PRIMLJENOG PRIHODA
// ==========================================

async function receiveIncome(event) {
    event.preventDefault();

    const button = event.submitter;
    button.disabled = true;
    button.textContent = "Evidentiranje...";

    try {
        const incomeId = document.getElementById(
            "receive-income-select"
        ).value;

        if (!incomeId) {
            throw new Error("Prvo odaberite prihod.");
        }

        const request = {
            actual_date: document.getElementById("actual-date").value,
            actual_amount: Number(
                document.getElementById("actual-amount").value
            )
        };

        const result = await postData(
            `/incomes/${incomeId}/receive`,
            request
        );

        document.getElementById("receive-income-form").reset();

        await refreshDashboard();

        showNotification(
            result.message +
            ` Kašnjenje uplate: ${result.income.delay_days} dana.`,
            "success"
        );

    } catch (error) {
        showNotification(error.message, "error");
    } finally {
        button.disabled = false;
        button.textContent = "Evidentiraj uplatu";
    }
}


// ==========================================
// RUCNO POKRETANJE AGENTA
// ==========================================

async function runAgent() {
    const button = document.getElementById("run-agent");

    button.disabled = true;
    button.textContent = "Analiza u toku...";

    try {
        const result = await postData("/agent/run", {});

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


// ==========================================
// POVEZIVANJE DOGADJAJA
// ==========================================

document.getElementById("run-agent").addEventListener(
    "click",
    runAgent
);

document.getElementById("income-form").addEventListener(
    "submit",
    createIncome
);

document.getElementById("obligation-form").addEventListener(
    "submit",
    createObligation
);

document.getElementById("receive-income-form").addEventListener(
    "submit",
    receiveIncome
);

document.getElementById("receive-income-select").addEventListener(
    "change",
    updateActualAmount
);


// ==========================================
// POCETNO UCITAVANJE
// ==========================================

document.getElementById("income-date").min = todayString();
document.getElementById("obligation-date").min = todayString();
document.getElementById("actual-date").max = todayString();
document.getElementById("actual-date").value = todayString();

refreshDashboard();
