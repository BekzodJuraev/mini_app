(function() {
    'use strict';

    function initToggle() {
        var $ = django.jQuery;

        // --- 1. СКРЫТИЕ ПОЛЯ ЖИВОТНЫХ ПРИ ЗАГРУЗКЕ ---
        // Добавляем стиль в head документа, чтобы скрыть поле мгновенно
        var style = document.createElement('style');
        style.innerHTML = '.field-which_animal { display: none; }';
        document.head.appendChild(style);

        function toggleAnimalField() {
            var $roleSelect = $('select[name="role"]');
            var $animalRow = $('.field-which_animal');

            if ($roleSelect.val() === 'animal') {
                $animalRow.show();
            } else {
                $animalRow.hide();
            }
        }

        // Слушаем изменение роли
        $(document).on('change', 'select[name="role"]', function() {
            toggleAnimalField();
        });

        // Сразу проверяем состояние (если страница открыта на редактирование животного)
        toggleAnimalField();

        // --- 2. ЛОГИКА ТИПОВ ВОПРОСОВ (Твой код) ---
        function fillChoices(selectedValue, $choicesGroup) {
            var $rows = $choicesGroup.find('.djn-inline-form');

            function setRow(index, text, points) {
                var $row = $rows.eq(index);
                if ($row.length) {
                    var $textInput = $row.find('input[name*="-text"]');
                    var $pointsInput = $row.find('input[name*="-points"]');

                    $textInput.val(text);
                    $pointsInput.val(points);

                    $textInput.css('background-color', '#fff9c4');
                    setTimeout(function() { $textInput.css('background-color', ''); }, 500);
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

        setTimeout(function() {
            $('select[name*="question_type"]').each(function() {
                toggleChoices(this, false);
            });
        }, 300);

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