    const expLabels = JSON.parse(document.getElementById("exp-labels").textContent);
    const expValues = JSON.parse(document.getElementById("exp-values").textContent);
    const incLabels = JSON.parse(document.getElementById("inc-labels").textContent);
    const incValues = JSON.parse(document.getElementById("inc-values").textContent);

    const COLORS = [
      "#4e73df", "#1cc88a", "#36b9cc", "#f6c23e",
      "#e74a3b", "#858796", "#fd7e14", "#20c997",
      "#6f42c1", "#0dcaf0"
    ];

    function makeColors(values) {
      return values.map((_, i) => COLORS[i % COLORS.length]);
    }

    if (expValues.length) {
      new Chart(document.getElementById("expenseDonut"), {
        type: "doughnut",
        data: {
          labels: expLabels,
          datasets: [{
            data: expValues,
            backgroundColor: makeColors(expValues),
            borderColor: "#ffffff",
            borderWidth: 1
          }]
        },
        options: {
          cutoutPercentage: 60,
          responsive: true,
          maintainAspectRatio: false,
          legend: {
            position: "bottom"
          }
        }
      });
    }

    if (incValues.length) {
      new Chart(document.getElementById("incomeDonut"), {
        type: "doughnut",
        data: {
          labels: incLabels,
          datasets: [{
            data: incValues,
            backgroundColor: makeColors(incValues),
            borderColor: "#ffffff",
            borderWidth: 1
          }]
        },
        options: {
          cutoutPercentage: 60,
          responsive: true,
          maintainAspectRatio: false,
          legend: {
            position: "bottom"
          }
        }
      });
    }