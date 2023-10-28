document.addEventListener('DOMContentLoaded', function() {
    // Задать исходный и целевой языки
    const sourceLanguage = "auto"; // Автоопределение исходного языка
    const targetLanguage = "ru"; // Замените на фактический язык перевода

    // Создаем объект, который будет хранить текущее состояние каждого поста
    const postStates = {};

    // Создаем объект, который будет хранить количество нажатий на каждую ссылку "Translate"
    const clickCount = {};

    // Делегирование событий на родительском элементе, который существует на момент загрузки страницы
    document.body.addEventListener('click', function(event) {
        const target = event.target;

        // Проверить, был ли клик на элементе с классом "translate-link"
        if (target.classList.contains('translate-link')) {
            event.preventDefault();

            // Найти соответствующий элемент с текстом поста
            const postId = target.id;
            const postTextElement = document.querySelector(`.post-text[data-postid="${postId}"]`);

            // Проверить, что элемент с текстом существует
            if (postTextElement) {
                // Переключить между оригинальным текстом и переводом
                toggleTranslation(postTextElement, target, sourceLanguage, targetLanguage, postStates, clickCount);
            }
        }
    });

    // Функция для переключения между оригинальным текстом и переводом
    function toggleTranslation(postTextElement, link, sourceLang, targetLang, postStates, clickCount) {
        const postId = postTextElement.dataset.postid;
        const currentState = postStates[postId] || "original";

        if (!clickCount[postId]) {
            clickCount[postId] = 0;
        }
        clickCount[postId]++;

        if (clickCount[postId] % 2 === 1) {
            // Нечетное нажатие, переключиться на перевод
            translateText(postTextElement, sourceLang, targetLang, link, postStates);
        } else {
            // Четное нажатие, переключиться на оригинал
            if (currentState === "original") {
                // Текущее состояние - оригинальный текст, ничего не меняем
                return;
            }
            postTextElement.textContent = postStates[postId].originalText;
            link.textContent = 'Translate'; // Измените текст ссылки на "Translate"
            postStates[postId] = { state: "original", originalText: postStates[postId].originalText };
        }
    }

    // Функция для выполнения перевода текста
    function translateText(postTextElement, sourceLang, targetLang, link, postStates) {
        const originalText = postTextElement.textContent;
        const postId = postTextElement.dataset.postid;

        const url = `https://translate.googleapis.com/translate_a/single?client=gtx&sl=${sourceLang}&tl=${targetLang}&dt=t&q=${encodeURIComponent(originalText)}`;

        $.ajax({
            url: url,
            type: 'GET',
            success: function (data) {
                var translation = data[0][0][0];
                postTextElement.textContent = translation;
                link.textContent = 'Original'; // Измените текст ссылки на "Original"

                // Сохраняем состояние поста
                postStates[postId] = { state: "translation", originalText: originalText };
            },
            error: function() {
                console.log("Translation request failed");
            }
        });
    }
});
