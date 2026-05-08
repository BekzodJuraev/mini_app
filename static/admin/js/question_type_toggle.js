(function() {
    'use strict';

    // Сразу проверяем работоспособность
    alert("JS Loaded!");

    function initToggle() {
        var $ = django.jQuery;

        // --- 1. ЛОГИКА СКРЫТИЯ ЖИВОТНЫХ ---
        function toggleAnimalField() {
            var $roleSelect = $('select[name="role"]');
            var $animalRow = $('.field-which_animal');

            if ($roleSelect.val() === 'animal') {
                $animalRow.show();
            } else {
                $animalRow.hide();
            }
        }

        $(document).on('change', 'select[name="role"]', toggleAnimalField);
        toggleAnimalField();

        // --- 2. ЛОГИКА ТИПОВ ВОПРОСОВ ---
        function fillChoices(selectedValue, $choicesGroup) {
            // Твое условие: если radio, ничего не заполняем автоматически
            if (selectedValue === 'radio') {
                return;
            }

            var $rows = $choicesGroup.find('.djn-inline-form');
            function setRow(index, text, points) {
                var $row = $rows.eq(index);
                if ($row.length) {
                    $row.find('input[name*="-text"]').val(text);
                    $row.find('input[name*="-points"]').val(points);
                }
            }

            // Пример для других типов (если нужно)
            if (selectedValue === 'boolean') {
                setRow(0, "Да", 10);
                setRow(1, "Нет", 0);
            }
        }

        function toggleChoices(selectElement, isManualChange) {
            var $el = $(selectElement);
            var selectedValue = $el.val();
            var $questionContainer = $el.closest('.djn-inline-form');
            var $choicesGroup = $questionContainer.find('.djn-group').filter(function() {
                return $(this).attr('id') && $(this).attr('id').includes('choices');
            });

            if (selectedValue === 'text') {
                $choicesGroup.hide();
            } else {
                $choicesGroup.show();
            }

            if (isManualChange) {
                fillChoices(selectedValue, $choicesGroup);
            }
        }

        $(document).on('change', 'select[name*="question_type"]', function() {
            toggleChoices(this, true);
        });

        // Инициализация существующих полей
        $('select[name*="question_type"]').each(function() {
            toggleChoices(this, false);
        });
    }

    // Ждем загрузку jQuery от Django
    var checkInterval = setInterval(function() {
        if (window.django && django.jQuery) {
            clearInterval(checkInterval);
            initToggle();
        }
    }, 100);
})();