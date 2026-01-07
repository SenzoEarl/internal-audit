/**
 * Framework-safe JavaScript
 * - No globals
 * - No DOM hijacking
 * - No framework assumptions
 */

document.addEventListener("DOMContentLoaded", () => {
    const appRoot = document.querySelector(".app");
    if (!appRoot) return;

    initApp(appRoot);
});

const initApp = (root) => {
    // Bind actions globally so elements outside the .app container (e.g. navbar) are handled
    bindActions(document);
    bindForms(root);
    bindActivityListeners();
};

/**
 * Bind actions using data attributes
 */
const bindActions = (root) => {
    const triggers = root.querySelectorAll("[data-app-action]");

    triggers.forEach((el) => {
        el.addEventListener("click", (ev) => {
            // Prevent native navigation or form submit; JS handles the action.
            try { ev.preventDefault(); } catch (e) { /* ignore */ }
            const action = el.dataset.appAction;
            handleAction(action, el);
        });
    });
};

/**
 * Bind forms marked with data-app-form
 */
const bindForms = (root) => {
    const forms = root.querySelectorAll("[data-app-form]");
    forms.forEach((form) => {
        // Prevent multiple bindings
        if (form.__appBound) return;
        form.__appBound = true;

        form.addEventListener("submit", (ev) => {
            ev.preventDefault();
            const name = form.dataset.appForm;
            handleFormSubmit(name, form);
        });
    });
};

/**
 * Centralized action handler
 */
const handleAction = (action, element) => {
    switch (action) {
        case "toggle":
            toggleTarget(element);
            break;
        case "login-submit":
            // If a submit button is used, find the closest form and submit
            const form = element.closest("form[data-app-form]");
            if (form) form.requestSubmit();
            break;
        case "logout":
            triggerLogout();
            break;
        case "client-view":
            return openClientModal(element.dataset.clientId);
        case "client-save":
            return saveClientFromModal();
        case "report-create":
            return openReportCreateFlow();
        case "report-share":
            return openShareModal(element.dataset.auditId);
        case "share-send":
            return sendShare();
        default:
            console.warn(`Unknown app action: ${action}`);
    }
};

/**
 * Handle form submission for named forms
 */
const handleFormSubmit = (name, form) => {
    switch (name) {
        case "login":
            submitLoginForm(form);
            break;
        default:
            console.warn(`Unknown form submit: ${name}`);
    }
};

/**
 * Submit login form via fetch as JSON. Uses CSRF token from the form input named 'csrfmiddlewaretoken'.
 */
const submitLoginForm = async (form) => {
    clearFormErrors(form);

    const usernameEl = form.querySelector('[name="username"]');
    const passwordEl = form.querySelector('[name="password"]');
    const submitBtn = form.querySelector('[type="submit"]');

    const username = usernameEl ? usernameEl.value.trim() : "";
    const password = passwordEl ? passwordEl.value : "";

    const errors = {};
    if (!username) errors.username = "Please enter your username.";
    if (!password) errors.password = "Please enter your password.";
    if (Object.keys(errors).length) {
        showFormErrors(form, errors);
        return;
    }

    // Obtain CSRF token from the form (Django's csrf_token renders an input)
    const csrfInput = form.querySelector('[name="csrfmiddlewaretoken"]');
    const csrfToken = csrfInput ? csrfInput.value : null;

    // Prepare request
    const url = form.getAttribute('action') || window.location.href;

    // UI: disable submit
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.dataset.prevText = submitBtn.textContent;
        submitBtn.textContent = 'Logging in...';
    }

    try {
        const resp = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                // Include CSRF token header if available
                ...(csrfToken && { 'X-CSRFToken': csrfToken }),
            },
            credentials: 'same-origin',
            body: JSON.stringify({ username, password }),
        });

        const data = await parseJsonSafe(resp);

        if (!resp.ok) {
            // Expecting {success: False, errors: {...}}
            if (data?.errors) {
                showFormErrors(form, data.errors);
            } else if (data?.detail) {
                showFormErrors(form, { '__all__': data.detail });
            } else {
                showFormErrors(form, { '__all__': 'An unexpected error occurred. Please try again.' });
            }
            return;
        }

        // Success: {success: True, redirect: "...}
        if (data?.success) {
            window.location.href = (data.redirect || '/');
            return;
        }

        // Fallback error
        showFormErrors(form, { '__all__': 'An unexpected server response was returned.' });
    } catch (err) {
        console.error(err);
        showFormErrors(form, { '__all__': 'Network error. Please check your connection and try again.' });
    } finally {
        if (submitBtn) {
            submitBtn.disabled = false;
            if (submitBtn.dataset.prevText) {
                submitBtn.textContent = submitBtn.dataset.prevText;
            }
            delete submitBtn.dataset.prevText;
        }
    }
};

/**
 * Parse JSON safely from a Response object.
 */
const parseJsonSafe = async (resp) => {
    try {
        return await resp.json();
    } catch (e) {
        return null;
    }
};

/**
 * Show form-level and field-level errors. Expects errors object with keys matching field names or '__all__'.
 */
const showFormErrors = (form, errors) => {
    // Field-specific
    Object.entries(errors).forEach(([key, message]) => {
        if (key === '__all__') {
            const el = form.querySelector('[data-field-error="__all__"]');
            if (el) el.textContent = message;
        } else {
            const fieldEl = form.querySelector(`[name="${key}"]`);
            const feedback = form.querySelector(`[data-field-error="${key}"]`);
            if (fieldEl) fieldEl.classList.add('is-invalid');
            if (feedback) feedback.textContent = message;
        }
    });
};

/**
 * Clear existing form errors
 */
const clearFormErrors = (form) => {
    // Clear invalid class
    const invalids = form.querySelectorAll('.is-invalid');
    invalids.forEach((el) => el.classList.remove('is-invalid'));

    // Clear feedback text
    const feedbacks = form.querySelectorAll('[data-field-error]');
    feedbacks.forEach((el) => el.textContent = '');
};

/**
 * Example behavior
 */
const toggleTarget = (trigger) => {
    const targetId = trigger.dataset.appTarget;
    if (!targetId) return;

    const target = document.getElementById(targetId);
    if (!target) return;

    target.classList.toggle("app--hidden");
};

// Add logout handling and inactivity timer
const INACTIVITY_TIMEOUT_MS = 10 * 60 * 1000; // 10 minutes
let __inactivityTimer = null;

const triggerLogout = async () => {
    // Find CSRF token in the page (from any form that includes csrfmiddlewaretoken)
    const csrfInput = document.querySelector('[name="csrfmiddlewaretoken"]');
    const csrfToken = csrfInput?.value;

    try {
        const resp = await fetch('/logout-ajax/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...(csrfToken && { 'X-CSRFToken': csrfToken }),
            },
            credentials: 'same-origin',
            body: JSON.stringify({}),
        });
        const data = await parseJsonSafe(resp);
        // On success redirect to root
        if (resp.ok && data?.success) {
            window.location.href = data.redirect || '/';
            return;
        }
        // Fallback: reload page to ensure logged out state
        window.location.reload();
    } catch (e) {
        console.error('Logout failed', e);
        window.location.reload();
    }
};

const startInactivityTimer = () => {
    stopInactivityTimer();
    __inactivityTimer = setTimeout(() => {
        // Auto-logout on inactivity
        triggerLogout();
    }, INACTIVITY_TIMEOUT_MS);
};

const stopInactivityTimer = () => {
    if (__inactivityTimer) {
        clearTimeout(__inactivityTimer);
        __inactivityTimer = null;
    }
};

const resetInactivityTimer = () => {
    startInactivityTimer();
};

// Hook activity events globally
const bindActivityListeners = () => {
    const events = ['mousemove', 'mousedown', 'keypress', 'scroll', 'touchstart'];
    events.forEach((ev) => {
        window.addEventListener(ev, resetInactivityTimer, { passive: true });
    });
    // Start timer initially
    startInactivityTimer();
};

// Helper to get CSRF token from DOM
const getCSRFCookie = () => {
    const el = document.querySelector('[name="csrfmiddlewaretoken"]');
    return el?.value;
};

// Open client modal and load client data
const openClientModal = async (clientId) => {
    const modalEl = document.getElementById('clientModal');
    if (!modalEl) return;
    const form = document.getElementById('client-modal-form');
    clearFormErrors(form);
    
    try {
        const resp = await fetch(`/clients/${clientId}/`, { credentials: 'same-origin' });
        if (!resp.ok) throw new Error('Failed to fetch client');
        const data = await resp.json();
        
        // populate fields
        form.dataset.clientId = data.id;
        form.querySelector('[name="name"]').value = data.name || '';
        form.querySelector('[name="contact_name"]').value = data.contact_name || '';
        form.querySelector('[name="contact_email"]').value = data.contact_email || '';
        form.querySelector('[name="contact_phone"]').value = data.contact_phone || '';
        form.querySelector('[name="address"]').value = data.address || '';
        
        // ensure any previous validation state is cleared
        clearFormErrors(form);

        // show modal using bootstrap's JS API
        const bsModal = new bootstrap.Modal(modalEl);
        bsModal.show();
    } catch (e) {
        console.error(e);
        alert('Could not load client details.');
    }
};

// Save client from modal via AJAX
const saveClientFromModal = async () => {
    const form = document.getElementById('client-modal-form');
    if (!form) return;
    clearFormErrors(form);
    const clientId = form.dataset.clientId;
    
    if (!clientId) {
        showFormErrors(form, { '__all__': 'Missing client id' });
        return;
    }
    
    const payload = {
        contact_name: form.querySelector('[name="contact_name"]').value.trim(),
        contact_email: form.querySelector('[name="contact_email"]').value.trim(),
        contact_phone: form.querySelector('[name="contact_phone"]').value.trim(),
        address: form.querySelector('[name="address"]').value.trim(),
    };

    const csrf = getCSRFCookie();
    const submitBtn = document.querySelector('#clientModal [data-app-action="client-save"]');
    
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.dataset.prevText = submitBtn.textContent;
        submitBtn.textContent = 'Saving...';
    }

    try {
        const resp = await fetch(`/clients/${clientId}/update/`, {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/json',
                ...(csrf && { 'X-CSRFToken': csrf }),
            },
            body: JSON.stringify(payload),
        });
        
        const data = await parseJsonSafe(resp);
        
        if (!resp.ok) {
            if (data?.errors) {
                showFormErrors(form, data.errors);
            } else {
                showFormErrors(form, { '__all__': 'Failed to save. Please try again.' });
            }
            return;
        }
        
        // success: refresh the table row by fetching latest client data
        try {
            const refreshed = await fetch(`/clients/${clientId}/`, { credentials: 'same-origin' });
            if (refreshed.ok) {
                const cd = await refreshed.json();
                const row = document.querySelector(`tr[data-client-id="${clientId}"]`);
                if (row) {
                    const nameEl = row.querySelector('.client-name');
                    if (nameEl) nameEl.textContent = cd.name || nameEl.textContent;
                }
            }
        } catch (e) {
            // non-fatal: ignore
            console.warn('Could not refresh client row after save', e);
        }

        // hide modal
        const modalEl = document.getElementById('clientModal');
        const bsModal = bootstrap.Modal.getInstance(modalEl);
        if (bsModal) bsModal.hide();
    } catch (e) {
        console.error(e);
        showFormErrors(form, { '__all__': 'Network error. Please try again.' });
    } finally {
        if (submitBtn) {
            submitBtn.disabled = false;
            if (submitBtn.dataset.prevText) {
                submitBtn.textContent = submitBtn.dataset.prevText;
            }
            delete submitBtn.dataset.prevText;
        }
    }
};

// Report create flow: multi-step wizard modal
const openReportCreateFlow = async () => {
    try {
        const resp = await fetch('/reports/create/', { credentials: 'same-origin' });
        if (!resp.ok) throw new Error('Failed to fetch create metadata');
        const data = await parseJsonSafe(resp);

        // Build modal HTML shell with steps area
        const modalHtml = `
        <div class="modal fade" id="createReportModal" tabindex="-1" aria-hidden="true">
          <div class="modal-dialog modal-lg">
            <div class="modal-content">
              <div class="modal-header">
                <h5 class="modal-title">Create Report</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
              </div>
              <div class="modal-body">
                <div id="create-report-wizard">
                  <div id="create-steps"></div>
                  <div class="mt-3 text-danger" data-field-error="__all__"></div>
                </div>
              </div>
              <div class="modal-footer">
                <button type="button" class="btn btn-secondary" id="create-prev">Back</button>
                <button type="button" class="btn btn-secondary" id="create-next">Next</button>
                <button type="button" class="btn btn-primary d-none" id="create-submit">Create</button>
              </div>
            </div>
          </div>
        </div>`;

        const wrapper = document.createElement('div');
        wrapper.innerHTML = modalHtml;
        document.body.appendChild(wrapper);
        const modalEl = document.getElementById('createReportModal');

        // Helper to render a single field based on metadata
        const renderField = (meta) => {
            const { name, type = 'text', choices = null } = meta;
            const id = `create_${name}`;
            const row = document.createElement('div');
            row.className = 'mb-3';

            const labelText = name.replace(/_/g, ' ');

            if (choices) {
                // render select
                let html = `<label class="form-label" for="${id}">${labelText}</label>`;
                html += `<select class="form-select" id="${id}" name="${name}">`;
                html += `<option value="">-- select --</option>`;
                choices.forEach((c) => {
                    const val = c.value;
                    const lab = c.label || c.value;
                    html += `<option value="${val}">${lab}</option>`;
                });
                html += `</select>`;
                html += `<div class="invalid-feedback" data-field-error="${name}"></div>`;
                row.innerHTML = html;
                return row;
            }

            if (type === 'date') {
                row.innerHTML = `<label class="form-label" for="${id}">${labelText}</label><input type="date" class="form-control" id="${id}" name="${name}" /><div class="invalid-feedback" data-field-error="${name}"></div>`;
                return row;
            }

            if (type === 'number') {
                row.innerHTML = `<label class="form-label" for="${id}">${labelText}</label><input type="number" class="form-control" id="${id}" name="${name}" /><div class="invalid-feedback" data-field-error="${name}"></div>`;
                return row;
            }

            // default text
            row.innerHTML = `<label class="form-label" for="${id}">${labelText}</label><input type="text" class="form-control" id="${id}" name="${name}" /><div class="invalid-feedback" data-field-error="${name}"></div>`;
            return row;
        };

        // Build three step containers
        const stepsContainer = modalEl.querySelector('#create-steps');
        const stepDefs = [
            { id: 'step-main', title: 'Basic Info', fields: data.fields || [] },
            { id: 'step-score', title: 'Scores', fields: data.score_fields || [] },
            { id: 'step-notices', title: 'Notices', fields: data.notice_fields || [] },
        ];

        stepDefs.forEach((s, idx) => {
            const sec = document.createElement('div');
            sec.id = s.id;
            sec.className = 'create-step';
            if (idx !== 0) sec.style.display = 'none';
            const header = document.createElement('h6');
            header.textContent = s.title;
            sec.appendChild(header);
            const formDiv = document.createElement('div');
            formDiv.className = 'create-step-fields';
            s.fields.forEach((meta) => {
                formDiv.appendChild(renderField(meta));
            });
            sec.appendChild(formDiv);
            stepsContainer.appendChild(sec);
        });

        // Required fields list (basic client-side presence checks)
        const requiredCore = ['project', 'audit_date', 'audit_number', 'performed_by', 'report_number'];

        // Step navigation
        let currentStep = 0;
        const totalSteps = stepDefs.length;
        const prevBtn = modalEl.querySelector('#create-prev');
        const nextBtn = modalEl.querySelector('#create-next');
        const submitBtn = modalEl.querySelector('#create-submit');
        const errorArea = modalEl.querySelector('[data-field-error="__all__"]');

        const showStep = (index) => {
            // hide all, show index
            stepDefs.forEach((s, i) => {
                const el = modalEl.querySelector(`#${s.id}`);
                if (!el) return;
                el.style.display = i === index ? '' : 'none';
            });
            // buttons
            prevBtn.disabled = index === 0;
            nextBtn.classList.toggle('d-none', index === totalSteps - 1);
            submitBtn.classList.toggle('d-none', index !== totalSteps - 1);
            // clear generic errors
            if (errorArea) errorArea.textContent = '';
        };

        const collectPayload = () => {
            const payload = {};
            // collect all inputs by name
            const inputs = modalEl.querySelectorAll('#create-steps [name]');
            inputs.forEach((inp) => {
                const name = inp.name;
                let val = inp.value;
                // convert number inputs
                if (inp.type === 'number') {
                    val = val === '' ? null : Number(val);
                }
                payload[name] = val;
            });
            return payload;
        };

        const validateCurrentStep = () => {
            // basic validation for core required fields when on first step
            if (currentStep === 0) {
                const missing = [];
                requiredCore.forEach((fn) => {
                    const el = modalEl.querySelector(`[name="${fn}"]`);
                    if (el) {
                        const v = el.value?.toString().trim();
                        if (!v) missing.push(fn);
                    }
                });
                if (missing.length) {
                    const m = `Please fill required fields: ${missing.join(', ').replace(/_/g, ' ')}`;
                    if (errorArea) errorArea.textContent = m;
                    return false;
                }
            }
            return true;
        };

        nextBtn.addEventListener('click', () => {
            if (!validateCurrentStep()) return;
            currentStep = Math.min(totalSteps - 1, currentStep + 1);
            showStep(currentStep);
        });

        prevBtn.addEventListener('click', () => {
            currentStep = Math.max(0, currentStep - 1);
            showStep(currentStep);
        });

        submitBtn.addEventListener('click', async () => {
            // final validation (basic)
            if (!validateCurrentStep()) return;
            const payload = collectPayload();
            // send to server
            const csrf = getCSRFCookie();
            submitBtn.disabled = true;
            submitBtn.dataset.prevText = submitBtn.textContent;
            submitBtn.textContent = 'Creating...';
            
            try {
                const resp2 = await fetch('/reports/create/', {
                    method: 'POST',
                    credentials: 'same-origin',
                    headers: {
                        'Content-Type': 'application/json',
                        ...(csrf && { 'X-CSRFToken': csrf }),
                    },
                    body: JSON.stringify(payload),
                });
                
                const data2 = await parseJsonSafe(resp2);
                
                if (!resp2.ok) {
                    const formArea = modalEl.querySelector('#create-steps');
                    if (data2?.errors) {
                        // map errors to fields
                        showFormErrors(formArea, data2.errors);
                        if (data2.errors.__all__ && errorArea) {
                            errorArea.textContent = data2.errors.__all__;
                        }
                    } else {
                        if (errorArea) errorArea.textContent = 'Failed to create report';
                    }
                    return;
                }
                
                if (data2?.success && data2.id) {
                    // redirect to new report detail
                    window.location.href = `/reports/${data2.id}/`;
                } else {
                    window.location.reload();
                }
            } catch (e) {
                console.error(e);
                if (errorArea) errorArea.textContent = 'Network error while creating report';
            } finally {
                submitBtn.disabled = false;
                if (submitBtn.dataset.prevText) {
                    submitBtn.textContent = submitBtn.dataset.prevText;
                }
                delete submitBtn.dataset.prevText;
            }
        });

        // show modal
        const bsModal = new bootstrap.Modal(modalEl);
        bsModal.show();

        // cleanup when hidden
        modalEl.addEventListener('hidden.bs.modal', () => {
            wrapper.remove();
        });

    } catch (e) {
        console.error(e);
        alert('Could not start create flow');
    }
};

// Share modal handling
const openShareModal = (auditId) => {
    const modalEl = document.getElementById('shareModal');
    if (!modalEl) return;
    const form = document.getElementById('share-form');
    form.dataset.auditId = auditId;
    clearFormErrors(form);

    // Clear previous manual input and message to avoid stale values
    const manualInput = modalEl.querySelector('#share-to');
    if (manualInput) manualInput.value = '';
    const messageArea = modalEl.querySelector('[name="message"]');
    if (messageArea) messageArea.value = '';

    // Show modal
    const bsModal = new bootstrap.Modal(modalEl);
    bsModal.show();
};

// Send share functionality (to be implemented)
const sendShare = async () => {
    // Implementation for sending share goes here
    console.log('Send share functionality to be implemented');
};

// Export functions if needed for testing or modular use
export {
    initApp,
    bindActions,
    bindForms,
    handleAction,
    handleFormSubmit,
    submitLoginForm,
    parseJsonSafe,
    showFormErrors,
    clearFormErrors,
    toggleTarget,
    triggerLogout,
    startInactivityTimer,
    stopInactivityTimer,
    resetInactivityTimer,
    bindActivityListeners,
    getCSRFCookie,
    openClientModal,
    saveClientFromModal,
    openReportCreateFlow,
    openShareModal,
    sendShare
};