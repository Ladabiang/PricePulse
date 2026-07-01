document.addEventListener("DOMContentLoaded", function () {
    initLoader();
    initSearchValidation();
    initTooltips();
    initAnimations();
    initScrollTop();
});

/* ========================================
   Loader While Searching
======================================== */
function initLoader() {
    const searchForm = document.querySelector("#searchForm");
    const loader = document.querySelector("#loader");
    const searchBtn = document.querySelector("#searchBtn");

    if (searchForm) {
        searchForm.addEventListener("submit", function () {
            if (loader) loader.style.display = "block";

            if (searchBtn) {
                searchBtn.disabled = true;
                searchBtn.innerHTML = `
                    <span class="spinner-border spinner-border-sm me-2"></span>
                    Searching...
                `;
            }
        });
    }
}

/* ========================================
   Search Input Validation
======================================== */
function initSearchValidation() {
    const input = document.querySelector("#searchInput");
    const form = document.querySelector("#searchForm");

    if (form && input) {
        form.addEventListener("submit", function (e) {
            const value = input.value.trim();

            if (value.length < 2) {
                e.preventDefault();
                showToast("Please enter at least 2 characters", "danger");
                input.focus();
            }
        });
    }
}

/* ========================================
   Bootstrap Tooltips
======================================== */
function initTooltips() {
    const tooltipTriggerList = [].slice.call(
        document.querySelectorAll('[data-bs-toggle="tooltip"]')
    );

    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/* ========================================
   Fade-in Card Animation
======================================== */
function initAnimations() {
    const cards = document.querySelectorAll(".card");

    cards.forEach((card, index) => {
        card.style.opacity = "0";
        card.style.transform = "translateY(20px)";

        setTimeout(() => {
            card.style.transition = "all 0.5s ease";
            card.style.opacity = "1";
            card.style.transform = "translateY(0)";
        }, index * 100);
    });
}

/* ========================================
   Scroll to Top Button
======================================== */
function initScrollTop() {
    const btn = document.querySelector("#scrollTopBtn");

    if (!btn) return;

    window.addEventListener("scroll", () => {
        if (window.scrollY > 300) {
            btn.style.display = "block";
        } else {
            btn.style.display = "none";
        }
    });

    btn.addEventListener("click", () => {
        window.scrollTo({
            top: 0,
            behavior: "smooth"
        });
    });
}

/* ========================================
   Toast Notification
======================================== */
function showToast(message, type = "success") {
    const toastContainer = document.querySelector("#toastContainer");

    if (!toastContainer) return;

    const toast = document.createElement("div");

    toast.className = `toast align-items-center text-bg-${type} border-0 show mb-2`;
    toast.role = "alert";

    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto"></button>
        </div>
    `;

    toastContainer.appendChild(toast);

    toast.querySelector(".btn-close").addEventListener("click", () => {
        toast.remove();
    });

    setTimeout(() => {
        toast.remove();
    }, 4000);
}