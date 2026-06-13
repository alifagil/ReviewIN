document.addEventListener('DOMContentLoaded', () => {
    // 1. Inisialisasi Elemen
    const wrapper = document.getElementById('mainWrapper');
    const resultSection = document.getElementById('resultSection');
    const form = document.getElementById('analyzeForm');
    const btn = document.getElementById('submitBtn');
    const progressWrapper = document.getElementById('progressWrapper');
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    const targetInput = document.getElementById('targetInput');
    const radioInputs = document.querySelectorAll('input[name="input_type"]');

    // --- FITUR INTERAKTIF: Mengubah placeholder secara real-time ---
    function updatePlaceholder() {
        const selectedValue = document.querySelector('input[name="input_type"]:checked').value;
        if (selectedValue === 'text') {
            targetInput.placeholder = "Paste raw review text here...";
        } else {
            targetInput.placeholder = "Paste Amazon Product Link Here...";
        }
    }

    // Pasang event listener ke radio button
    radioInputs.forEach(radio => {
        radio.addEventListener('change', updatePlaceholder);
    });

    // Jalankan sekali saat load pertama kali untuk mencocokkan state dari Flask
    if (targetInput) {
        updatePlaceholder();
    }

    // 2. LOGIKA SAAT TOMBOL SCAN DIKLIK (Fase Loading di Tengah)
    if (form) {
        form.onsubmit = () => {
            btn.disabled = true;
            btn.innerText = "SCANNING...";
            progressWrapper.style.display = 'block';

            let width = 0;
            // Pesan loading disesuaikan secara dinamis tergantung tipe input
            const currentType = document.querySelector('input[name="input_type"]:checked').value;
            const messages = currentType === 'link' 
                ? ["Connecting Network...", "Bypassing Amazon Firewall...", "Fetching Data Live...", "AI Analysing Patterns...", "Almost Done..."]
                : ["Initializing NLP Pipeline...", "Tokenizing Text...", "Extracting TF-IDF Features...", "AI Analysing Sentiment...", "Finishing..."];
            
            const interval = setInterval(() => {
                if (width >= 98) {
                    clearInterval(interval);
                } else {
                    width += Math.random() * 12; // Sedikit dinaikkan kecepatannya biar gokil
                    if (width > 98) width = 98;
                    
                    progressBar.style.width = width + '%';
                    
                    let msgIndex = Math.floor((width / 100) * messages.length);
                    if (msgIndex >= messages.length) msgIndex = messages.length - 1;
                    progressText.innerText = `${Math.round(width)}% ${messages[msgIndex]}`;
                }
            }, 450);
        };
    }

    // 3. LOGIKA PAS HALAMAN RELOAD (Hasil Analisa Datang)
    const chartCanvas = document.getElementById('myChart');
    
    if (chartCanvas) {
        const percentageTarget = parseFloat(chartCanvas.dataset.percentage);
        const humanTarget = parseFloat(chartCanvas.dataset.human);

        // STEP A: Animasi "Terbang" ke Atas (Fly-up)
        setTimeout(() => {
            wrapper.classList.remove('centered-content');
            wrapper.classList.add('fly-up');
        }, 150);

        // STEP B: Munculin Section Hasil (Jeda 1.2 detik nunggu Fly-up selesai)
        setTimeout(() => {
            resultSection.classList.add('show');
            
            // --- Fitur 1: Digital Counter (Angka Skor Jalan) ---
            const scoreElement = document.querySelector('.stats-center h1');
            let currentScore = 0;
            
            if (percentageTarget === 0) {
                scoreElement.innerText = "0%";
            } else {
                const counter = setInterval(() => {
                    if (currentScore >= percentageTarget) {
                        scoreElement.innerText = percentageTarget + "%";
                        clearInterval(counter);
                    } else {
                        currentScore += 1;
                        if (currentScore > percentageTarget) currentScore = percentageTarget;
                        scoreElement.innerText = Math.round(currentScore) + "%";
                    }
                }, 20);
            }

            // --- Fitur 2: Inisialisasi Doughnut Chart ---
            new Chart(chartCanvas.getContext('2d'), {
                type: 'doughnut',
                data: {
                    datasets: [{
                        data: [percentageTarget, humanTarget],
                        backgroundColor: ['#ff073a', '#39ff14'],
                        borderWidth: 0,
                    }]
                },
                options: {
                    cutout: '82%',
                    plugins: { 
                        legend: { display: false },
                        tooltip: { enabled: false } 
                    },
                    animation: {
                        animateRotate: true,
                        duration: 1800,
                        easing: 'easeOutQuart'
                    }
                }
            });

            // --- Fitur 3: Animasi Baris Tabel (Fade-in satu-satu) ---
            const rows = document.querySelectorAll('tbody tr');
            rows.forEach((row, index) => {
                setTimeout(() => {
                    row.classList.add('reveal');
                }, index * 150);
            });

        }, 1300);
    }
});