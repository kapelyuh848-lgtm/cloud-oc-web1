function updateCode() {
    fetch('/api/get_code')
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                window.location.href = "/";
                return;
            }

            // Обновляем цифры
            document.getElementById('authCode').innerText = data.code;

            // Обновляем полоску (data.time_remaining - это сколько секунд осталось из 30)
            const percentage = (data.time_remaining / 30) * 100;
            document.getElementById('progressBar').style.width = percentage + "%";

            // Меняем цвет полоски, если времени мало
            const bar = document.getElementById('progressBar');
            if (data.time_remaining < 5) {
                bar.style.backgroundColor = "red";
            } else {
                bar.style.backgroundColor = "#00ff00";
            }
        });
}

// Запускать сразу и потом каждую секунду
updateCode();
setInterval(updateCode, 1000);