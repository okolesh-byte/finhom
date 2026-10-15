function initializeFinhom() {
    if (window.lucide) {
        window.lucide.createIcons({ attrs: { 'aria-hidden': 'true' } });
    }

    const menuButton = document.getElementById('menuButton');
    const sidebar = document.getElementById('sidebar');
    if (menuButton && sidebar) {
        const setMenuOpen = (open) => {
            sidebar.classList.toggle('open', open);
            menuButton.setAttribute('aria-expanded', String(open));
        };
        menuButton.setAttribute('aria-expanded', 'false');
        menuButton.addEventListener('click', () => setMenuOpen(!sidebar.classList.contains('open')));
        document.addEventListener('click', (event) => {
            if (!sidebar.contains(event.target) && !menuButton.contains(event.target)) setMenuOpen(false);
        });
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape') setMenuOpen(false);
        });
    }

    document.querySelectorAll('[data-counter]').forEach((counter) => {
        const target = Number(counter.dataset.counter);
        const start = performance.now();
        const run = (now) => {
            const progress = Math.min((now - start) / 850, 1);
            counter.textContent = Math.round(target * progress).toLocaleString('ru-RU');
            if (progress < 1) requestAnimationFrame(run);
        };
        requestAnimationFrame(run);
    });

    const chartCanvas = document.getElementById('expenseChart');
    const chartDataElement = document.getElementById('expense-chart-data');
    if (chartCanvas && chartDataElement) {
        const chartData = JSON.parse(chartDataElement.textContent);
        const styles = getComputedStyle(document.documentElement);
        const colors = ['#176b4d', '#d8755a', '#e7ad35', '#54726a', '#8b7067', '#9aab7e'];
        const hasData = chartData.values.length > 0;
        const values = hasData ? chartData.values.map(Number) : [1];
        if (window.Chart) {
            new Chart(chartCanvas, {
                type: 'doughnut',
                data: {
                    labels: hasData ? chartData.labels : ['Пока нет расходов'],
                    datasets: [{ data: values, backgroundColor: hasData ? colors : [styles.getPropertyValue('--line')], borderWidth: 0 }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: '66%',
                    plugins: { legend: { position: 'bottom', labels: { usePointStyle: true, padding: 16 } }, tooltip: { enabled: hasData } }
                }
            });
        } else {
            const context = chartCanvas.getContext('2d');
            const ratio = window.devicePixelRatio || 1;
            const size = Math.min(chartCanvas.parentElement.clientWidth, 270);
            chartCanvas.width = size * ratio;
            chartCanvas.height = size * ratio;
            chartCanvas.style.width = `${size}px`;
            chartCanvas.style.height = `${size}px`;
            context.scale(ratio, ratio);
            const total = values.reduce((sum, value) => sum + value, 0);
            let angle = -Math.PI / 2;
            values.forEach((value, index) => {
                const next = angle + (value / total) * Math.PI * 2;
                context.beginPath();
                context.arc(size / 2, size / 2, size * .38, angle, next);
                context.strokeStyle = hasData ? colors[index % colors.length] : styles.getPropertyValue('--line');
                context.lineWidth = size * .13;
                context.stroke();
                angle = next;
            });
        }
    }

    window.setTimeout(() => {
        document.querySelectorAll('.message').forEach((message) => message.remove());
    }, 4500);
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeFinhom, { once: true });
} else {
    initializeFinhom();
}
