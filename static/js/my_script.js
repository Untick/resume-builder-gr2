$('input[type="checkbox"]').on('change',
    function() {
        console.log('check');
        if ($(this).is(':checked')) {
            $(this).val('1');
            } else {
            $(this).val('');
        }
    });
