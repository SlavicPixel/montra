(function () {
  const ratesEl = document.getElementById("fx-rates");
  const currenciesEl = document.getElementById("fx-currencies");
  if (!ratesEl || !currenciesEl) return;

  const rates = JSON.parse(ratesEl.textContent || "{}"); // base -> target mapping
  const currencies = JSON.parse(currenciesEl.textContent || "[]");

  const amountEl = document.getElementById("cc-amount");
  const fromEl = document.getElementById("cc-from");
  const toEl = document.getElementById("cc-to");
  const resultEl = document.getElementById("cc-result");
  const hintEl = document.getElementById("cc-hint");

  // Fill dropdowns
  function fillSelect(sel, values) {
    sel.innerHTML = "";
    values.forEach(v => {
      const opt = document.createElement("option");
      opt.value = v;
      opt.textContent = v;
      sel.appendChild(opt);
    });
  }

  fillSelect(fromEl, currencies);
  fillSelect(toEl, currencies);

  // Default: from=base, to=USD (if exists)
  fromEl.value = currencies[0] || "EUR";
  toEl.value = currencies.includes("USD") ? "USD" : (currencies[1] || currencies[0]);

  // Convert using base rates:
  // If base=EUR, we have rates[USD] = EUR->USD, rates[GBP] = EUR->GBP
  // For cross conversion X->Y:
  //   X->base = 1 / (base->X)  (if X != base)
  //   base->Y = rates[Y]       (if Y != base)
  //   X->Y = (X->base) * (base->Y)
  function getRate(from, to) {
    const base = currencies[0];
    if (from === to) return 1;

    if (from === base) {
      // base -> to
      return to === base ? 1 : Number(rates[to] || NaN);
    }
    if (to === base) {
      // from -> base
      const baseToFrom = Number(rates[from] || NaN);
      return 1 / baseToFrom;
    }

    // from -> base -> to
    const baseToFrom = Number(rates[from] || NaN);
    const baseToTo = Number(rates[to] || NaN);
    return (1 / baseToFrom) * baseToTo;
  }

  function recalc() {
    const amt = Number(amountEl.value || 0);
    const from = fromEl.value;
    const to = toEl.value;

    const r = getRate(from, to);
    if (!isFinite(r)) {
      resultEl.textContent = "—";
      hintEl.textContent = "Rate not available for selected currencies.";
      return;
    }

    const out = amt * r;
    resultEl.textContent = out.toFixed(4) + " " + to;
    hintEl.textContent = `${amt} ${from} ≈ ${out.toFixed(4)} ${to}`;
  }

  amountEl.addEventListener("input", recalc);
  fromEl.addEventListener("change", recalc);
  toEl.addEventListener("change", recalc);

  recalc();
})();