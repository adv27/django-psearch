jQuery(document).ready(function ($) {
    $("input[name='reviewStars']").on('click', function () {
        let pid = $("input[name='pid']").attr('value');
        let rating = $(this).attr('value');
        console.log(pid, rating);
        $.ajax({
            url: '/rate',
            data: {
                pid: pid,
                rating: rating
            },
        }).done(function (msg) {
            console.log(msg);
        });
    });
});