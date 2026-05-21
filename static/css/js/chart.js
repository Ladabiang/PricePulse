<!-- ===================================================== -->
<!-- File: templates/includes/chart_js.html -->
<!-- Professional Industry Level Chart.js Setup -->
<!-- ===================================================== -->

<!-- Chart.js CDN -->
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

<script>
document.addEventListener("DOMContentLoaded", function () {

    // =====================================================
    // COMMON DEFAULT STYLE
    // =====================================================
    Chart.defaults.font.family = "Inter, Arial, sans-serif";
    Chart.defaults.font.size = 13;
    Chart.defaults.color = "#6c757d";
    Chart.defaults.plugins.legend.labels.usePointStyle = true;
    Chart.defaults.plugins.legend.position = "bottom";

    // =====================================================
    // PRICE TREND LINE CHART
    // Canvas ID = priceChart
    // =====================================================
    const priceCanvas = document.getElementById("priceChart");

    if (priceCanvas) {
        new Chart(priceCanvas, {
            type: "line",
            data: {
                labels: {{ chart_labels|tojson }},
                datasets: [{
                    label: "Price ₹",
                    data: {{ chart_prices|tojson }},
                    tension: 0.4,
                    fill: true,
                    borderWidth: 3,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    backgroundColor: "rgba(13,110,253,0.08)",
                    borderColor: "#0d6efd",
                    pointBackgroundColor: "#0d6efd"
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,

                plugins: {
                    tooltip: {
                        mode: "index",
                        intersect: false,
                        callbacks: {
                            label: function(context) {
                                return " ₹" + context.raw;
                            }
                        }
                    }
                },

                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: "rgba(0,0,0,0.05)"
                        },
                        ticks: {
                            callback: function(value) {
                                return "₹" + value;
                            }
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
    }


    // =====================================================
    // SITE DISTRIBUTION DOUGHNUT
    // Canvas ID = siteChart
    // =====================================================
    const siteCanvas = document.getElementById("siteChart");

    if (siteCanvas) {
        new Chart(siteCanvas, {
            type: "doughnut",
            data: {
                labels: {{ site_labels|tojson }},
                datasets: [{
                    data: {{ site_counts|tojson }},
                    backgroundColor: [
                        "#0d6efd",
                        "#198754",
                        "#ffc107",
                        "#dc3545",
                        "#6f42c1"
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                cutout: "72%",
                maintainAspectRatio: false
            }
        });
    }


    // =====================================================
    // USERS BAR CHART
    // Canvas ID = userChart
    // =====================================================
    const userCanvas = document.getElementById("userChart");

    if (userCanvas) {
        new Chart(userCanvas, {
            type: "bar",
            data: {
                labels: {{ user_labels|tojson }},
                datasets: [{
                    label: "Registrations",
                    data: {{ user_counts|tojson }},
                    borderRadius: 8,
                    backgroundColor: "#6610f2"
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,

                plugins: {
                    legend: { display: false }
                },

                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: "rgba(0,0,0,0.05)"
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
    }

});
</script>