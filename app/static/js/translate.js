document.addEventListener('DOMContentLoaded', function() {
    // ����� ��� �������� � ������� "translate-link"
    const translateLinks = document.querySelectorAll('.translate-link');

    // ������ �� ������ ������ � �������� ���������� ������� "click"
    translateLinks.forEach(function(link) {
        link.addEventListener('click', function(event) {
            // ���������� �������� �� ��������� (������������� ������� �� ������)
            event.preventDefault();
            translatePost(link);
        });
    });

    // ������� ��� ���������� �������� �����
    function translatePost(link) {
        // �������� ���������� ������������� ����� �� ID ������
        const postId = link.id;

        // ����� ��������������� ������� � ������� �����
        const postTextElement = document.querySelector(`.post-text[data-postid="${postId}"]`);

        // ���������, ��� ������� � ������� ����������
        if (postTextElement) {
            // �������� ����� �����
            const postText = postTextElement.textContent;

            // ������ �������� � ������� �����
            const sourceLanguage = "auto"; // ��������������� ��������� �����
            const targetLanguage = "ru"; // �������� �� ����������� ���� ��������

            // ������������ URL-������ ��� Google Translate API
            const url = `https://translate.googleapis.com/translate_a/single?client=gtx&sl=${sourceLanguage}&tl=${targetLanguage}&dt=t&q=${encodeURIComponent(postText)}`;

            // ��������� ������ � Google Translate API
            $.ajax({
                url: url,
                type: 'GET',
                success: function (data) {
                    // ������� ������� �� ������
                    var translation = data[0][0][0];

                    // �������� ������� � ������� � ������� �����
                    postTextElement.textContent = translation;
                }
            });
        }
    }
});
