document.addEventListener('DOMContentLoaded', function() {
    // ������ �������� � ������� �����
    const sourceLanguage = "auto"; // ��������������� ��������� �����
    const targetLanguage = "ru"; // �������� �� ����������� ���� ��������

    // ������� ������, ������� ����� ������� ������� ��������� ������� �����
    const postStates = {};

    // ������� ������, ������� ����� ������� ���������� ������� �� ������ ������ "Translate"
    const clickCount = {};

    // ������������� ������� �� ������������ ��������, ������� ���������� �� ������ �������� ��������
    document.body.addEventListener('click', function(event) {
        const target = event.target;

        // ���������, ��� �� ���� �� �������� � ������� "translate-link"
        if (target.classList.contains('translate-link')) {
            event.preventDefault();

            // ����� ��������������� ������� � ������� �����
            const postId = target.id;
            const postTextElement = document.querySelector(`.post-text[data-postid="${postId}"]`);

            // ���������, ��� ������� � ������� ����������
            if (postTextElement) {
                // ����������� ����� ������������ ������� � ���������
                toggleTranslation(postTextElement, target, sourceLanguage, targetLanguage, postStates, clickCount);
            }
        }
    });

    // ������� ��� ������������ ����� ������������ ������� � ���������
    function toggleTranslation(postTextElement, link, sourceLang, targetLang, postStates, clickCount) {
        const postId = postTextElement.dataset.postid;
        const currentState = postStates[postId] || "original";

        if (!clickCount[postId]) {
            clickCount[postId] = 0;
        }
        clickCount[postId]++;

        if (clickCount[postId] % 2 === 1) {
            // �������� �������, ������������� �� �������
            translateText(postTextElement, sourceLang, targetLang, link, postStates);
        } else {
            // ������ �������, ������������� �� ��������
            if (currentState === "original") {
                // ������� ��������� - ������������ �����, ������ �� ������
                return;
            }
            postTextElement.textContent = postStates[postId].originalText;
            link.textContent = 'Translate'; // �������� ����� ������ �� "Translate"
            postStates[postId] = { state: "original", originalText: postStates[postId].originalText };
        }
    }

    // ������� ��� ���������� �������� ������
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
                link.textContent = 'Original'; // �������� ����� ������ �� "Original"

                // ��������� ��������� �����
                postStates[postId] = { state: "translation", originalText: originalText };
            },
            error: function() {
                console.log("Translation request failed");
            }
        });
    }
});
