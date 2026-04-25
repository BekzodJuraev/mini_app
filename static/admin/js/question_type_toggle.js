(function() {
    'use strict';

    function initToggle() {
        var $ = django.jQuery;

        function fillChoices(selectedValue, $choicesGroup) {
            var $rows = $choicesGroup.find('.djn-inline-form');

            // Внутренняя функция для очистки и заполнения
            function setRow(index, text, points) {
                var $row = $rows.eq(index);
                if ($row.length) {
                    var $textInput = $row.find('input[name*="-text"]');
                    var $pointsInput = $row.find('input[name*="-points"]');

                    // Обновляем значения
                    $textInput.val(text);
                    $pointsInput.val(points);

                    // Подсвечиваем поле, чтобы было видно, что оно изменилось
                    $textInput.css('background-color', '#fff9c4');
                    setTimeout(function() { $textInput.css('background-color', ''); }, 500);
                }
            }

            if (selectedValue === 'text') {
                    // Для текста нам не нужны варианты, можно их очистить
                    setRow(0, "", 0);
                    setRow(1, "", 0);
                }

                // ... внутри функции toggleChoices ...
                if (selectedValue === 'text') {
                    $choicesGroup.hide(); // Скрываем блок Choices, так как это просто поле ввода
                } else {
                    $choicesGroup.show(); // Для остальных показываем
                }

            // Логика замены текста
            if (selectedValue === 'slider') {
                setRow(0, "Плохо", 0);
                setRow(1, "Нормально", 5);
                setRow(2, "Хорошо", 10);
            } else if (selectedValue === 'binary') {
                setRow(0, "Да", 10);
                setRow(1, "Нет", 0);
                setRow(2, "", 0); // Очищаем третье поле, если оно было
            } else if (selectedValue === 'emoji') {
                setRow(0, "😊 Хорошо", 10);
                setRow(1, "😐 Средне", 5);
                setRow(2, "😡 Плохо", 0);
            } else if (selectedValue === 'radio') {
                // Если обычный выбор — просто очищаем всё для ручного ввода
                setRow(0, "", 0);
                setRow(1, "", 0);
                setRow(2, "", 0);
            }
        }

        function toggleChoices(selectElement, isManualChange) {
            var $el = $(selectElement);
            var selectedValue = $el.val();
            var $questionContainer = $el.closest('.djn-inline-form');
            var $choicesGroup = $questionContainer.find('.djn-group').filter(function() {
                return $(this).attr('id') && $(this).attr('id').includes('choices');
            });

            if (!$choicesGroup.length) return;

            $choicesGroup.show();

            // Если это ручное изменение (клик в селекте), то обновляем данные всегда
            if (isManualChange) {
                fillChoices(selectedValue, $choicesGroup);
            }
        }

        // 1. Слушаем ручные изменения (isManualChange = true)
        $(document).on('change', 'select[name*="question_type"]', function() {
            toggleChoices(this, true);
        });

        // 2. Первичная инициализация (isManualChange = false, чтобы не затереть сохраненное в БД)
        setTimeout(function() {
            $('select[name*="question_type"]').each(function() {
                toggleChoices(this, false);
            });
        }, 300);

        // 3. Для новых вопросов
        $(document).on('djnesting:init', function(e, $inline) {
            if ($inline && $inline.length) {
                $inline.find('select[name*="question_type"]').each(function() {
                    toggleChoices(this, true);
                });
            }
        });
    }

    var checkInterval = setInterval(function() {
        if (typeof django !== 'undefined' && django.jQuery) {
            clearInterval(checkInterval);
            initToggle();
        }
    }, 100);
})();