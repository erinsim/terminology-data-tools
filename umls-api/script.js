// Wait for the page to fully load before running the script
window.addEventListener("DOMContentLoaded", function () {
    // Get the parameters from the URL (e.g., API key, search term, etc.)
    const params = new URLSearchParams(window.location.search);
    const apiKey = params.get("apiKey"); // API key for authentication
    const searchString = params.get("string"); // Search term entered by the user
    const returnIdType = params.get("returnIdType"); // Type of ID to return (e.g., concept or code)
    const sabs = params.get("sabs"); // Selected vocabularies (if any)

    // If an API key is provided in the URL, set it in the input field
    if (apiKey) {
        document.getElementById("api-key").value = apiKey;
    }

    // If a search term is provided in the URL, set it in the search input field
    if (searchString) {
        document.getElementById("query").value = searchString;
    }

    // If a return ID type is provided, set it in the dropdown and trigger a change event
    if (returnIdType) {
        document.getElementById("return-id-type").value = returnIdType;
        document.getElementById("return-id-type").dispatchEvent(new Event("change"));
    }

    // If vocabularies are provided, check the corresponding checkboxes
    if (sabs) {
        const vocabArray = sabs.split(","); // Split the vocabularies into an array
        document.querySelectorAll("#vocab-container input").forEach(checkbox => {
            if (vocabArray.includes(checkbox.value)) {
                checkbox.checked = true; // Check the box if it matches
            }
        });
    }
});

// A helper function to extract the last part of a URL (e.g., the ID or endpoint)
function stripBaseUrl(fullUrl) {
    if (!fullUrl) return ""; // Return an empty string if the URL is missing
    const parts = fullUrl.split("/"); // Split the URL into parts
    return parts.length ? parts[parts.length - 1] : fullUrl; // Return the last part
}

// Store the current data for the modal (e.g., selected CUI and vocabulary)
let modalCurrentData = { ui: null, sab: null };

// Open a modal window to show options for a selected CUI
function openCuiOptionsModal(ui, sab) {
    modalCurrentData.ui = ui; // Store the selected CUI
    modalCurrentData.sab = sab || null; // Store the vocabulary if provided

    const returnIdType = document.getElementById("return-id-type").value; // Get the return ID type
    const modalDiv = document.getElementById("cui-options-modal"); // Get the modal element

    // Update the modal content based on the return ID type
    if (returnIdType === "concept") {
        modalDiv.innerHTML = `
            <h3>Select an action for <span id="selected-cui">${ui}</span></h3>
            <button onclick="fetchConceptDetails(modalCurrentData.ui, 'atoms')">Atoms</button>
            <button onclick="fetchConceptDetails(modalCurrentData.ui, 'relations')">Relations</button>
            <button onclick="fetchConceptDetails(modalCurrentData.ui, 'definitions')">Definitions</button>
            <hr>
            <button onclick="closeCuiOptionsModal()">Close</button>
        `;
    } else if (returnIdType === "code") {
        modalDiv.innerHTML = `
            <h3>Select an action for <span id="selected-cui">${ui}</span></h3>
            <button onclick="fetchConceptDetails(modalCurrentData.ui, 'atoms')">Atoms</button>
            <button onclick="fetchConceptDetails(modalCurrentData.ui, 'relations')">Relations</button>
            <hr>
            <button onclick="closeCuiOptionsModal()">Close</button>
        `;
    }

    // Show the modal and its backdrop
    document.getElementById("modal-backdrop").style.display = "block";
    modalDiv.style.display = "block";
}

// Close the modal window and reset its data
function closeCuiOptionsModal() {
    modalCurrentData = { ui: null, sab: null }; // Reset the modal data
    document.getElementById("selected-cui").textContent = ""; // Clear the selected CUI
    document.getElementById("modal-backdrop").style.display = "none"; // Hide the backdrop
    document.getElementById("cui-options-modal").style.display = "none"; // Hide the modal
}

// Show or hide the vocabularies section based on the selected return ID type
document.getElementById("return-id-type").addEventListener("change", function () {
    const vocabContainer = document.getElementById("vocab-container"); // Get the vocabularies container
    const rootSourceHeader = document.getElementById("root-source-header"); // Get the root source header

    if (this.value === "code") {
        vocabContainer.style.display = "block"; // Show vocabularies for "code"
        rootSourceHeader.style.display = ""; // Show the root source header
    } else {
        vocabContainer.style.display = "none"; // Hide vocabularies for "concept"
        rootSourceHeader.style.display = "none"; // Hide the root source header
    }
});

// Get a list of selected vocabularies from the checkboxes
function getSelectedVocabularies() {
    return Array.from(document.querySelectorAll("#vocab-container input:checked")).map(
        checkbox => checkbox.value // Return the value of each checked box
    );
}

// Format a URL with color-coded parts for display
function colorizeUrl(urlObject) {
    const base = urlObject.origin + urlObject.pathname; // Get the base URL
    let colorized = `<span style="color:blue">${base}</span>`; // Color the base URL in blue
    const params = [];
    for (let [key, value] of urlObject.searchParams.entries()) {
        params.push(
            `<span style="color:green">${encodeURIComponent(key)}</span>=<span style="color:red">${encodeURIComponent(value)}</span>`
        ); // Color the keys in green and the values in red
    }
    if (params.length > 0) {
        colorized += `?${params.join("&")}`; // Add the parameters to the URL
    }
    return colorized; // Return the formatted URL
}

async function searchUMLS() {
    const apiKey = document.getElementById("api-key").value.trim();
    const searchString = document.getElementById("query").value.trim();
    const returnIdType = document.getElementById("return-id-type").value;
    const selectedVocabularies =
        returnIdType === "code" ? getSelectedVocabularies() : [];

    if (!apiKey || !searchString) {
        alert("Please enter both an API key and a search term.");
        return;
    }

    const params = new URLSearchParams();
    params.set("string", searchString);
    params.set("returnIdType", returnIdType);
    if (selectedVocabularies.length > 0) {
        params.set("sabs", selectedVocabularies.join(","));
    }
    window.history.pushState({}, "", "?" + params.toString());

    const resultsContainer = document.getElementById("output");
    const infoTableBody = document.querySelector("#info-table tbody");
    const recentRequestContainer = document.getElementById("recent-request-output");
    const tableHead = document.querySelector("#info-table thead");

    resultsContainer.textContent = "Loading...";
    tableHead.innerHTML = `<tr>
        <th>UI</th>
        <th>Name</th>
        <th id="root-source-header" style="display: none;">Root Source</th>
    </tr>`;
    infoTableBody.innerHTML = '<tr><td colspan="3">No information yet...</td></tr>';

    const url = new URL("https://uts-ws.nlm.nih.gov/rest/search/current");
    url.searchParams.append("string", searchString);
    url.searchParams.append("returnIdType", returnIdType);
    url.searchParams.append("apiKey", apiKey);
    if (selectedVocabularies.length > 0) {
        url.searchParams.append("sabs", selectedVocabularies.join(","));
    }
    const displayUrl = new URL(url);
    displayUrl.searchParams.set("apiKey", "***");
    recentRequestContainer.innerHTML = colorizeUrl(displayUrl);

    try {
        const response = await fetch(url, {
            method: "GET",
            headers: { Accept: "application/json" }
        });
        const data = await response.json();

        resultsContainer.textContent = JSON.stringify(data, null, 2);

        // Add a toggle button for raw data
        const toggleButton = document.createElement("button");
        toggleButton.textContent = "Hide Raw Data";
        toggleButton.addEventListener("click", function () {
            if (resultsContainer.style.display === "none") {
                resultsContainer.style.display = "block";
                toggleButton.textContent = "Hide Raw Data";
            } else {
                resultsContainer.style.display = "none";
                toggleButton.textContent = "Show Raw Data";
            }
        });

        // Insert the toggle button before the raw data container
        resultsContainer.parentNode.insertBefore(toggleButton, resultsContainer);

        infoTableBody.innerHTML = "";

        const results = data.result && data.result.results ? data.result.results : [];
        if (results.length === 0) {
            infoTableBody.innerHTML = '<tr><td colspan="3">No results found.</td></tr>';
            return;
        }

        results.forEach(item => {
            const tr = document.createElement("tr");

            const uiTd = document.createElement("td");
            if (returnIdType === "concept") {
                uiTd.style.color = "blue";
                uiTd.style.textDecoration = "underline";
                uiTd.style.cursor = "pointer";
                uiTd.textContent = item.ui || "N/A";
                uiTd.addEventListener("click", () => {
                    openCuiOptionsModal(item.ui);
                });
            } else {
                uiTd.textContent = item.ui || "N/A";
            }
            tr.appendChild(uiTd);

            const nameTd = document.createElement("td");
            nameTd.textContent = item.name || "N/A";
            tr.appendChild(nameTd);

            const rootSourceHeader = document.getElementById("root-source-header");
            if (rootSourceHeader.style.display !== "none") {
                const rootSourceTd = document.createElement("td");
                rootSourceTd.textContent = item.rootSource || "N/A";
                tr.appendChild(rootSourceTd);
            }
            infoTableBody.appendChild(tr);
        });
    } catch (error) {
        resultsContainer.textContent = "Error fetching data: " + error;
        infoTableBody.innerHTML = '<tr><td colspan="3">Error loading data.</td></tr>';
    }
}

async function fetchConceptDetails(cui, detailType) {
    const apiKey = document.getElementById("api-key").value.trim();
    const returnIdType = document.getElementById("return-id-type").value;
    const resultsContainer = document.getElementById("output");
    const infoTableBody = document.querySelector("#info-table tbody");
    const recentRequestContainer = document.getElementById("recent-request-output");
    const tableHead = document.querySelector("#info-table thead");

    closeCuiOptionsModal();

    if (!apiKey) {
        alert("Please enter an API key first.");
        return;
    }

    let baseUrl;
    if (returnIdType === "code") {
        baseUrl = modalCurrentData.uri + "/" + detailType;
    } else {
        baseUrl = `https://uts-ws.nlm.nih.gov/rest/content/current/CUI/${cui}/${detailType}`;
    }
    const apiUrlObj = new URL(baseUrl);
    apiUrlObj.searchParams.append("apiKey", apiKey);

    const displayApiUrl = new URL(apiUrlObj);
    displayApiUrl.searchParams.set("apiKey", "***");

    recentRequestContainer.innerHTML = colorizeUrl(displayApiUrl);

    const addressUrl = new URL(window.location.href);
    addressUrl.searchParams.set("endpoint", detailType);
    window.history.pushState({}, "", addressUrl.toString());

    resultsContainer.textContent = `Loading ${detailType} for ${cui}...`;
    infoTableBody.innerHTML = '<tr><td colspan="3">Loading...</td></tr>';

    try {
        const response = await fetch(apiUrlObj, {
            method: "GET",
            headers: { Accept: "application/json" }
        });
        const data = await response.json();

        resultsContainer.textContent = JSON.stringify(data, null, 2);

        infoTableBody.innerHTML = "";

        if (detailType === "atoms") {
            tableHead.innerHTML = `<tr><th>Atom</th><th>Root Source</th></tr>`;
        } else if (detailType === "definitions") {
            tableHead.innerHTML = `<tr><th>Definition</th><th>Root Source</th></tr>`;
        } else if (detailType === "relations") {
            tableHead.innerHTML = `<tr>
              <th>From Name</th>
              <th>Relation Label</th>
              <th>To Name</th>
              <th>Root Source</th>
            </tr>`;
        }

        const detailArray = Array.isArray(data.result) ? data.result : [];
        if (!Array.isArray(detailArray) || detailArray.length === 0) {
            infoTableBody.innerHTML = `<tr><td colspan="3">No ${detailType} found for this ${cui}.</td></tr>`;
            return;
        }

        if (detailType === "atoms") {
            detailArray.forEach((atom, index) => {
                const tr = document.createElement("tr");
                const col1 = document.createElement("td");
                col1.textContent = atom.name || `(Atom #${index + 1})`;
                tr.appendChild(col1);
                const col2 = document.createElement("td");
                col2.textContent = atom.rootSource || "(no rootSource)";
                tr.appendChild(col2);
                infoTableBody.appendChild(tr);
            });
        } else if (detailType === "definitions") {
            detailArray.forEach((definition, index) => {
                const tr = document.createElement("tr");
                const col1 = document.createElement("td");
                col1.textContent = definition.value || `(Definition #${index + 1})`;
                tr.appendChild(col1);
                const col2 = document.createElement("td");
                col2.textContent = definition.rootSource || "(no rootSource)";
                tr.appendChild(col2);
                infoTableBody.appendChild(tr);
            });
        } else if (detailType === "relations") {
            detailArray.forEach((relation) => {
                const tr = document.createElement("tr");

                const col1 = document.createElement("td");
                col1.style.color = "blue";
                col1.style.textDecoration = "underline";
                col1.style.cursor = "pointer";
                col1.textContent = relation.relatedFromIdName || "(no relatedFromIdName)";
                col1.addEventListener("click", function () {
                    if (returnIdType === "code") {
                        fetchRelatedDetail(relation.relatedFromId, "from", relation.rootSource);
                    } else {
                        fetchRelatedDetail(relation.relatedFromId, "from");
                    }
                });
                tr.appendChild(col1);

                const col2 = document.createElement("td");
                col2.textContent = relation.additionalRelationLabel || "(no relation label)";
                tr.appendChild(col2);

                const col3 = document.createElement("td");
                col3.style.color = "blue";
                col3.style.textDecoration = "underline";
                col3.style.cursor = "pointer";
                col3.textContent = relation.relatedIdName || "(no relatedIdName)";
                col3.addEventListener("click", function () {
                    if (returnIdType === "code") {
                        fetchRelatedDetail(relation.relatedId, "to", relation.rootSource);
                    } else {
                        fetchRelatedDetail(relation.relatedId, "to");
                    }
                });
                tr.appendChild(col3);

                const col4 = document.createElement("td");
                col4.textContent = relation.rootSource || "(no rootSource)";
                tr.appendChild(col4);

                infoTableBody.appendChild(tr);
            });
        }
    } catch (error) {
        resultsContainer.textContent = `Error fetching ${detailType}: ${error}`;
        infoTableBody.innerHTML = `<tr><td colspan="3">Error loading ${detailType}.</td></tr>`;
    }
}

async function fetchRelatedDetail(apiUrl, relatedType, rootSource) {
    const apiKey = document.getElementById("api-key").value.trim();
    if (!apiKey) {
        alert("Please enter an API key first.");
        return;
    }

    const urlObj = new URL(apiUrl);
    urlObj.searchParams.append("apiKey", apiKey);

    const displayUrlObj = new URL(urlObj);
    displayUrlObj.searchParams.set("apiKey", "***");

    document.getElementById("recent-request-output").innerHTML = colorizeUrl(displayUrlObj);

    const currentUrl = new URL(window.location.href);
    currentUrl.searchParams.set("related", relatedType);
    currentUrl.searchParams.set("relatedId", stripBaseUrl(apiUrl));
    window.history.pushState({}, "", currentUrl.toString());

    const resultsContainer = document.getElementById("output");
    const infoTableBody = document.querySelector("#info-table tbody");
    const tableHead = document.querySelector("#info-table thead");

    resultsContainer.textContent = `Loading related ${relatedType} information...`;
    infoTableBody.innerHTML = '<tr><td colspan="3">Loading...</td></tr>';
    tableHead.innerHTML = `<tr>
      <th>Name</th>
      <th>Root Source</th>
      <th>UI</th>
    </tr>`;

    try {
        const response = await fetch(urlObj, {
            method: "GET",
            headers: { Accept: "application/json" }
        });
        const data = await response.json();

        resultsContainer.textContent = JSON.stringify(data, null, 2);
        infoTableBody.innerHTML = "";

        if (data && typeof data === "object" && data.result && Array.isArray(data.result.results)) {
            data.result.results.forEach((item) => {
                const name = item.name || "N/A";
                const rootSource = item.rootSource || "N/A";
                const ui = item.ui || "N/A";

                const tr = document.createElement("tr");

                const nameTd = document.createElement("td");
                nameTd.textContent = name;
                tr.appendChild(nameTd);

                const rootSourceTd = document.createElement("td");
                rootSourceTd.textContent = rootSource;
                tr.appendChild(rootSourceTd);

                const uiTd = document.createElement("td");
                uiTd.textContent = ui;
                tr.appendChild(uiTd);

                infoTableBody.appendChild(tr);
            });
        } else {
            infoTableBody.innerHTML = '<tr><td colspan="3">No data found for the selected concept.</td></tr>';
        }
    } catch (error) {
        resultsContainer.textContent = `Error fetching related ${relatedType}: ${error}`;
        infoTableBody.innerHTML = `<tr><td colspan="3">Error loading related ${relatedType}.</td></tr>`;
    }
}

// Function to toggle the visibility of raw data
function toggleRawData() {
  const rawDataContainer = document.getElementById("raw-data-container");
  const results = document.getElementById("results");
  const showButton = document.getElementById("show-raw-data-button");

  if (rawDataContainer.classList.contains("raw-data-hidden")) {
    rawDataContainer.classList.remove("raw-data-hidden");
    results.classList.remove("results-centered");
    showButton.textContent = "Hide Raw Data"; // Update button text
  } else {
    rawDataContainer.classList.add("raw-data-hidden");
    results.classList.add("results-centered");
    showButton.textContent = "Show Raw Data"; // Update button text
  }
}
