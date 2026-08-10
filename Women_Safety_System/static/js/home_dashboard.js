document.addEventListener("DOMContentLoaded", function () {

  let hrData = [], stressData = [], labels = [];

  const panel    = document.getElementById("riskPanel");
  const riskText = document.getElementById("riskText");
  const riskIcon = document.getElementById("riskIcon");
  const alertBox = document.getElementById("dangerAlert");

  // ── Charts ──────────────────────────────────────────────
  const hrCanvas     = document.getElementById("hrChart");
  const stressCanvas = document.getElementById("stressChart");
  let hrChart, stressChart;

  if (hrCanvas) {
    hrChart = new Chart(hrCanvas, {
      type: "line",
      data: { labels, datasets: [{ data: hrData,
        borderColor: "#e05c8a",
        backgroundColor: ctx => {
          const g = ctx.chart.ctx.createLinearGradient(0, 0, 0, 220);
          g.addColorStop(0, "rgba(224,92,138,0.18)");
          g.addColorStop(1, "rgba(224,92,138,0.01)");
          return g;
        },
        tension: 0.42, fill: true,
        pointRadius: 4, pointHoverRadius: 6,
        pointBackgroundColor: "#e05c8a",
        pointBorderColor: "#fff", pointBorderWidth: 2, borderWidth: 2.5
      }]},
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        layout: { padding: { bottom: 4 } },
        scales: {
          x: {
            grid: { color: "rgba(0,0,0,0.05)", drawBorder: false },
            ticks: {
              display: true,
              color: "#9ca3af",
              font: { size: 10, family: "Calibri, Carlito, sans-serif" },
              maxTicksLimit: 8,
              maxRotation: 0
            },
            border: { display: false }
          },
          y: {
            min: 40, max: 180,
            grid: { color: "rgba(0,0,0,0.06)", drawBorder: false },
            ticks: {
              color: "#6b7280",
              font: { size: 11, family: "Calibri, Carlito, sans-serif" },
              callback: v => v + " bpm",
              maxTicksLimit: 6
            },
            border: { display: false }
          }
        },
        animation: { duration: 500 }
      }
    });
  }

  if (stressCanvas) {
    stressChart = new Chart(stressCanvas, {
      type: "bar",
      data: { labels, datasets: [{ data: stressData,
        backgroundColor: ctx => {
          const v = ctx.raw;
          if (v >= 2) return "rgba(239,68,68,0.78)";
          if (v >= 1) return "rgba(245,158,11,0.78)";
          return "rgba(16,185,129,0.78)";
        },
        borderRadius: 7, borderSkipped: false,
        hoverBackgroundColor: ctx => {
          const v = ctx.raw;
          if (v >= 2) return "rgba(239,68,68,0.95)";
          if (v >= 1) return "rgba(245,158,11,0.95)";
          return "rgba(16,185,129,0.95)";
        }
      }]},
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        layout: { padding: { bottom: 4 } },
        scales: {
          x: {
            grid: { display: false },
            ticks: {
              display: true,
              color: "#9ca3af",
              font: { size: 10, family: "Calibri, Carlito, sans-serif" },
              maxTicksLimit: 8,
              maxRotation: 0
            },
            border: { display: false }
          },
          y: {
            min: 0, max: 3,
            grid: { color: "rgba(0,0,0,0.06)", drawBorder: false },
            ticks: {
              stepSize: 1,
              color: "#6b7280",
              font: { size: 11, family: "Calibri, Carlito, sans-serif" },
              callback: v => (["Low", "Medium", "High", "Critical"][v] || "")
            },
            border: { display: false }
          }
        },
        animation: { duration: 500 }
      }
    });
  }

  // ── Helpers ─────────────────────────────────────────────
  function el(id) { return document.getElementById(id); }
  function setText(id, val) { const e = el(id); if (e) e.textContent = val; }

  function mapStress(val) {
    if (typeof val === "number") return val;
    if (val === "High")   return 2;
    if (val === "Medium") return 1;
    return 0;
  }

  function hrInfo(hr) {
    if (hr < 60)  return { label: "Low — Below Normal", color: "#60a5fa" };
    if (hr < 100) return { label: "✓ Normal",           color: "#34d399" };
    if (hr < 140) return { label: "⚠ Elevated",         color: "#fbbf24" };
    return               { label: "✕ Danger",           color: "#f87171" };
  }

  function spo2Info(v) {
    if (v >= 95) return { label: "✓ Normal",   color: "#34d399" };
    if (v >= 90) return { label: "⚠ Low",      color: "#fbbf24" };
    return               { label: "✕ Critical", color: "#f87171" };
  }

  function stressInfo(s) {
    if (s === "High")   return { label: "⚠ High — Alert Mode", color: "#f87171" };
    if (s === "Medium") return { label: "→ Moderate",          color: "#fbbf24" };
    return                     { label: "✓ Calm — Normal",     color: "#34d399" };
  }

  function riskInfo(r) {
    if (r === "Emergency") return { label: "Emergency!", score: 95, color: "#ef4444" };
    if (r === "Warning")   return { label: "Warning",    score: 60, color: "#f59e0b" };
    return                        { label: "Safe",        score: 10, color: "#10b981" };
  }

  // ── Main update ──────────────────────────────────────────
  function updateDashboard() {
    fetch("/watch-data")
      .then(r => r.json())
      .then(data => {
        if (!data || !data.heart_rate) return;

        const hr     = parseInt(data.heart_rate) || 0;
        const spo2   = parseInt(data.spo2) || 0;
        const stress = data.stress || "Low";
        const bp     = data.bp    || "-- / --";
        const risk   = data.risk  || "Safe";

        // 1 ── Heart Rate
        if (el("hr")) el("hr").innerHTML = `${hr}&thinsp;<span class="mc-unit">bpm</span>`;
        const hrPct = Math.min(100, Math.max(0, ((hr - 40) / 140) * 100));
        if (el("hrBar")) el("hrBar").style.width = hrPct + "%";
        const hrI = hrInfo(hr);
        const hrSt = el("hrStatus");
        if (hrSt) { hrSt.textContent = hrI.label; hrSt.style.color = hrI.color; }

        // 2 ── Blood Pressure
        setText("bp", bp);

        // 3 ── SpO2
        if (el("spo2")) el("spo2").innerHTML = `${spo2}&thinsp;<span class="mc-unit">%</span>`;
        if (el("spo2Bar")) el("spo2Bar").style.width = Math.min(100, spo2) + "%";
        const spo2I = spo2Info(spo2);
        const spo2St = el("spo2Status");
        if (spo2St) { spo2St.textContent = spo2I.label; spo2St.style.color = spo2I.color; }

        // 4 ── Stress
        setText("stress", stress);
        const stI = stressInfo(stress);
        const stSub = el("stressSub");
        if (stSub) { stSub.textContent = stI.label; stSub.style.color = stI.color; }

        // 5 ── Risk Score
        const rI = riskInfo(risk);
        const rEl = el("risk");
        if (rEl) { rEl.textContent = rI.label; rEl.style.color = rI.color; }
        if (el("riskBar")) {
          el("riskBar").style.width      = rI.score + "%";
          el("riskBar").style.background = rI.color;
        }
        setText("riskScore", rI.score + "%");

        // ── Status bar ──────────────────────────────────────
        if (panel) {
          panel.classList.remove("safe", "warning", "danger");
          document.body.classList.remove("full-danger");
          if (risk === "Emergency") {
            if (alertBox) alertBox.style.display = "flex";
            panel.classList.add("danger");
            if (riskText) riskText.textContent = "EMERGENCY";
            if (riskIcon) riskIcon.textContent = "🔴";
            document.body.classList.add("full-danger");
            /* ── Show emergency popup ── */
            if (typeof window.showEmergencyPopup === "function") {
              window.showEmergencyPopup();
            }
          } else if (risk === "Warning") {
            if (alertBox) alertBox.style.display = "none";
            panel.classList.add("warning");
            if (riskText) riskText.textContent = "WARNING";
            if (riskIcon) riskIcon.textContent = "🟡";
            /* Reset popup so it can re-trigger on next Emergency */
            if (typeof window.resetEmergencyPopup === "function") {
              window.resetEmergencyPopup();
            }
          } else {
            if (alertBox) alertBox.style.display = "none";
            panel.classList.add("safe");
            if (riskText) riskText.textContent = "SAFE";
            if (riskIcon) riskIcon.textContent = "🟢";
            /* Reset popup so it can re-trigger on next Emergency */
            if (typeof window.resetEmergencyPopup === "function") {
              window.resetEmergencyPopup();
            }
          }
        }

        // ── Charts ──────────────────────────────────────────
        if (labels.length > 10) { labels.shift(); hrData.shift(); stressData.shift(); }
        const t = new Date();
        labels.push(t.getMinutes() + ":" + String(t.getSeconds()).padStart(2,"0"));
        hrData.push(hr);
        stressData.push(mapStress(stress));
        if (hrChart)     hrChart.update();
        if (stressChart) stressChart.update();

      }).catch(e => console.warn("Dashboard:", e));
  }

  setInterval(updateDashboard, 5000);
  updateDashboard();
});
