
(function () {
const el = document.getElementById("report-rows");
if (!el) return;

const rows = JSON.parse(el.textContent || "[]");

const labels = rows.map(r => r.category_name);
const values = rows.map(r => Number(r.total_amount));

const canvas = document.getElementById("spendPie");
if (!canvas) return;

const sum = values.reduce((a, b) => a + b, 0);
if (!sum) return;

// Nice distinct colors (will repeat if more categories)
const COLORS = [
    "#4e73df", "#1cc88a", "#36b9cc", "#f6c23e",
    "#e74a3b", "#858796", "#fd7e14", "#20c997",
    "#6f42c1", "#0dcaf0"
];

const bgColors = values.map((_, i) => COLORS[i % COLORS.length]);

new Chart(canvas, {
    type: "doughnut",
    data: {
    labels: labels,
    datasets: [{
        data: values,
        backgroundColor: bgColors,
        borderColor: "#ffffff",
        borderWidth: 1
    }]
    },
    options: {
    cutout: "60%",
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: {
        position: "bottom"
        },
        tooltip: {
        callbacks: {
            label: function(ctx) {
            const label = ctx.label || "";
            const val = ctx.parsed || 0;
            return `${label}: ${val}`;
            }
        }
        }
    }
    }
});
})();
