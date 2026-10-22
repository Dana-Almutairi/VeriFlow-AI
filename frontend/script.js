let currentReport = null;

const downloadPdfButton = document.getElementById(
    "download-pdf-button"
);
const API_URL = "/analyze/stream";

const form = document.getElementById("verification-form");
const claimInput = document.getElementById("claim-input");
const verifyButton = document.getElementById("verify-button");
const characterCount = document.getElementById("character-count");

const loadingSection = document.getElementById("loading-section");
const resultsSection = document.getElementById("results-section");
const errorSection = document.getElementById("error-section");

const verdictText = document.getElementById("verdict-text");
const verdictDescription = document.getElementById("verdict-description");

const supportCount = document.getElementById("support-count");
const contradictCount = document.getElementById("contradict-count");
const insufficientCount = document.getElementById("insufficient-count");

const evidenceList = document.getElementById("evidence-list");
const errorMessage = document.getElementById("error-message");

const agentNames = [
    "Planning Agent",
    "Research Agent",
    "Verification Agent",
    "Evidence Validator",
    "Decision Agent"
];

const agentList = document.querySelector(".agents-list");

const verdictLabels = {
    PRELIMINARY_SUPPORT: "Preliminary Support",
    PRELIMINARY_CONTRADICTION: "Preliminary Contradiction",
    CONFLICTING_EVIDENCE: "Conflicting Evidence",
    INSUFFICIENT_EVIDENCE: "Insufficient Evidence"
};

claimInput.addEventListener("input", () => {
    characterCount.textContent =
        `${claimInput.value.length} / 2000`;
});

function resetAgents() {
    agentList.replaceChildren();

    agentNames.forEach((name, index) => {
        const item = document.createElement("div");
        item.className = "agent-item";
        item.dataset.agent = name;

        const number = document.createElement("span");
        number.textContent = String(index + 1).padStart(2, "0");

        const label = document.createElement("strong");
        label.textContent = ` ${name}`;

        const status = document.createElement("small");
        status.className = "agent-status";
        status.textContent = "Waiting";

        item.append(number, label, status);
        agentList.appendChild(item);
    });
}

function updateAgent(name, status) {
    const item = [...agentList.querySelectorAll(".agent-item")]
        .find(element => element.dataset.agent === name);

    if (!item) return;

    const statusElement = item.querySelector(".agent-status");

    if (status === "running") {
        statusElement.textContent = "● Running";
        statusElement.style.color = "var(--primary)";
    } else if (status === "completed") {
        statusElement.textContent = "✓ Completed";
        statusElement.style.color = "var(--success)";
    } else if (status === "failed") {
        statusElement.textContent = "✕ Failed";
        statusElement.style.color = "var(--danger)";
    }
}

function handleStreamEvent(eventType, data) {
    switch (eventType) {
        case "pipeline_started":
            resetAgents();
            break;

        case "agent_started":
            updateAgent(data.agent, "running");
            break;

        case "agent_completed":
            updateAgent(data.agent, "completed");
            break;

        case "analysis_completed":
            displayResults(data);
            return true;

        case "analysis_error":
            throw new Error(
                data.message || "Analysis failed."
            );
    }

    return false;
}

async function readEventStream(response) {
    if (!response.body) {
        throw new Error("Streaming is not supported.");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    let buffer = "";
    let completed = false;

    try {
        while (true) {
            const { value, done } = await reader.read();

            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            buffer = buffer.replace(/\r\n/g, "\n");

            const events = buffer.split("\n\n");
            buffer = events.pop();

            for (const rawEvent of events) {
                let eventType = "message";
                const dataLines = [];

                for (const line of rawEvent.split("\n")) {
                    if (line.startsWith("event:")) {
                        eventType = line.slice(6).trim();
                    } else if (line.startsWith("data:")) {
                        dataLines.push(line.slice(5).trimStart());
                    }
                }

                if (!dataLines.length) continue;

                const data = JSON.parse(dataLines.join("\n"));

                if (handleStreamEvent(eventType, data)) {
    completed = true;
    await reader.cancel();
    return;
}
            }
        }

        if (!completed) {
            throw new Error(
                "The connection closed before analysis completed."
            );
        }
    } finally {
        reader.releaseLock();
    }
}

form.addEventListener("submit", async event => {
    event.preventDefault();

    const claim = claimInput.value.trim();

    if (!claim) {
        showError("Please enter a claim.");
        return;
    }

    verifyButton.disabled = true;
verifyButton.textContent = "Verifying...";

currentReport = null;
downloadPdfButton.disabled = true;

resetAgents();

    loadingSection.classList.remove("hidden");
    resultsSection.classList.add("hidden");
    errorSection.classList.add("hidden");

    loadingSection.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });

    try {
        const response = await fetch(API_URL, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ claim })
        });

        if (!response.ok) {
            let message = `Server error (${response.status})`;

            try {
                const errorData = await response.json();

                if (typeof errorData.detail === "string") {
                    message = errorData.detail;
                }
            } catch {
                // Keep the original error.
            }

            throw new Error(message);
        }

        await readEventStream(response);

    } catch (error) {
        showError(error.message || "Verification failed.");
    } finally {
        loadingSection.classList.add("hidden");

        verifyButton.disabled = false;
        verifyButton.textContent = "Verify Claim →";
    }
});

function displayResults(data) {
    const report = data.report;
    const verdict = report.verdict || "UNKNOWN";
    currentReport = report;
    downloadPdfButton.disabled = false;

    verdictText.textContent =
        verdictLabels[verdict] ||
        verdict.replaceAll("_", " ");

    verdictDescription.textContent =
        report.summary || "No summary available.";

    const counts = report.evidence_counts || {};

    supportCount.textContent = counts.supports ?? 0;
    contradictCount.textContent = counts.contradicts ?? 0;
    insufficientCount.textContent = counts.insufficient ?? 0;

    const verdictCard = document.querySelector(".verdict-card");

    verdictCard.style.borderLeftColor =
        verdict === "PRELIMINARY_SUPPORT"
            ? "var(--success)"
            : verdict === "PRELIMINARY_CONTRADICTION"
                ? "var(--danger)"
                : "var(--warning)";

    renderEvidence(report.evidence || []);

    resultsSection.classList.remove("hidden");

    resultsSection.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });
}

function renderEvidence(evidence) {
    evidenceList.replaceChildren();

    if (!evidence.length) {
        const message = document.createElement("p");
        message.textContent = "No evidence was retrieved.";
        evidenceList.appendChild(message);
        return;
    }

    for (const item of evidence) {
        const card = document.createElement("article");
        card.className = "evidence-item";

        const stance = item.stance || "INSUFFICIENT";

        const badge = document.createElement("span");
        badge.className = "evidence-stance";

        if (stance === "SUPPORTS") {
            badge.classList.add("stance-supports");
        } else if (stance === "CONTRADICTS") {
            badge.classList.add("stance-contradicts");
        } else {
            badge.classList.add("stance-insufficient");
        }

        badge.textContent = stance;

        const title = document.createElement("h4");
        title.textContent = item.title || "Untitled Source";

        const reason = document.createElement("p");
        reason.textContent =
            item.reason || "No explanation provided.";

        card.append(badge, title, reason);

        if (item.quote) {
            const quote = document.createElement("p");
            quote.textContent = `Evidence: "${item.quote}"`;
            card.appendChild(quote);
        }

        const verification = document.createElement("p");

        verification.textContent = item.quote_verified
            ? "✓ Exact quotation found in retrieved content"
            : "Quotation not verified";

        card.appendChild(verification);

        if (item.url) {
            try {
                const url = new URL(item.url);

                if (["https:", "http:"].includes(url.protocol)) {
                    const link = document.createElement("a");
                    link.href = url.href;
                    link.target = "_blank";
                    link.rel = "noopener noreferrer";
                    link.textContent = "View Original Source ↗";
                    card.appendChild(link);
                }
            } catch {
                // Ignore invalid URLs.
            }
        }

        evidenceList.appendChild(card);
    }
}

function showError(message) {
    loadingSection.classList.add("hidden");
    resultsSection.classList.add("hidden");

    errorMessage.textContent = message;
    errorSection.classList.remove("hidden");
}

resetAgents();


downloadPdfButton.addEventListener("click", async () => {
    if (!currentReport) return;

    downloadPdfButton.disabled = true;
    downloadPdfButton.textContent = "Generating PDF...";

    try {
        const response = await fetch("/report/pdf", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                report: currentReport
            })
        });

        if (!response.ok) {
            throw new Error(
                `PDF generation failed (${response.status})`
            );
        }

        const blob = await response.blob();
        const url = URL.createObjectURL(blob);

        const link = document.createElement("a");
        link.href = url;
        link.download = "VeriFlow_AI_Report.pdf";

        document.body.appendChild(link);
        link.click();
        link.remove();

        setTimeout(() => {
            URL.revokeObjectURL(url);
        }, 1000);

    } catch (error) {
        alert(error.message || "Could not download PDF.");
    } finally {
        downloadPdfButton.disabled = false;
        downloadPdfButton.textContent = "Download PDF ↓";
    }
});
