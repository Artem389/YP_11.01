// static/js/main.js
// Основной JavaScript файл

document.addEventListener('DOMContentLoaded', function() {
    // Автоматическое закрытие алертов через 5 секунд
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            const closeButton = alert.querySelector('.btn-close');
            if (closeButton) {
                closeButton.click();
            }
        });
    }, 5000);

    // Добавление класса fade-in к основному контенту
    const mainContent = document.querySelector('.container');
    if (mainContent) {
        mainContent.classList.add('fade-in');
    }
});