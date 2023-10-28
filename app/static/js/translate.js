document.addEventListener('DOMContentLoaded', function() {
    const sourceLanguage = "auto";
    const targetLanguage = "ru";
    const postStates = {};
    const clickCount = {};

    document.body.addEventListener('click', handleTranslationClick);

    function handleTranslationClick(event) {
        const target = event.target;

        if (target.classList.contains('translate-link')) {
            event.preventDefault();

            const postId = target.id;
            const postTextElement = document.querySelector(`.post-text[data-postid="${postId}"]`);

            if (postTextElement) {
                toggleTranslation(postTextElement, target);
            }
        }
    }

    function toggleTranslation(postTextElement, link) {
        const postId = postTextElement.dataset.postid;
        const currentState = postStates[postId] || "original";

        if (!clickCount[postId]) {
            clickCount[postId] = 0;
        }
        clickCount[postId]++;

        if (clickCount[postId] % 2 === 1) {
            translateText(postTextElement, link);
        } else {
            if (currentState === "original") {
                return;
            }
            postTextElement.textContent = postStates[postId].originalText;
            link.textContent = 'Translate';
            postStates[postId] = { state: "original", originalText: postStates[postId].originalText };
        }
    }

    function translateText(postTextElement, link) {
        const originalText = postTextElement.textContent;
        const postId = postTextElement.dataset.postid;
        const url = `https://translate.googleapis.com/translate_a/single?client=gtx&sl=${sourceLanguage}&tl=${targetLanguage}&dt=t&q=${encodeURIComponent(originalText)}`;

        $.ajax({
            url: url,
            type: 'GET',
            success: function (data) {
                var translation = data[0][0][0];
                postTextElement.textContent = translation;
                link.textContent = 'Original';
                postStates[postId] = { state: "translation", originalText: originalText };
            },
            error: function() {
                console.log("Translation request failed");
            }
        });
    }
});
