document.addEventListener('DOMContentLoaded', function() {
    // Найти все элементы с классом "translate-link"
    const translateLinks = document.querySelectorAll('.translate-link');

    // Пройти по каждой ссылке и добавить обработчик события "click"
    translateLinks.forEach(function(link) {
        link.addEventListener('click', function(event) {
            // Остановить действие по умолчанию (предотвратить переход по ссылке)
            event.preventDefault();
            translatePost(link);
        });
    });

    // Функция для выполнения перевода поста
    function translatePost(link) {
        // Получить уникальный идентификатор поста из ID ссылки
        const postId = link.id;

        // Найти соответствующий элемент с текстом поста
        const postTextElement = document.querySelector(`.post-text[data-postid="${postId}"]`);

        // Проверить, что элемент с текстом существует
        if (postTextElement) {
            // Получить текст поста
            const postText = postTextElement.textContent;

            // Задать исходный и целевой языки
            const sourceLanguage = "auto"; // Автоопределение исходного языка
            const targetLanguage = "ru"; // Замените на фактический язык перевода

            // Сформировать URL-запрос для Google Translate API
            const url = `https://translate.googleapis.com/translate_a/single?client=gtx&sl=${sourceLanguage}&tl=${targetLanguage}&dt=t&q=${encodeURIComponent(postText)}`;

            // Выполнить запрос к Google Translate API
            $.ajax({
                url: url,
                type: 'GET',
                success: function (data) {
                    // Извлечь перевод из ответа
                    var translation = data[0][0][0];

                    // Вставить перевод в элемент с текстом поста
                    postTextElement.textContent = translation;
                }
            });
        }
    }
});
