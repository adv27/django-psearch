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
        }).done(function (result) {
            console.log(result);
            console.log(result["rating"]);
            $("#rate-avg").text(result["rate_avg"]);
            $("#rate-times").text(`${result['rate_times']} total`);

            $('[role="progressbar"]').each(function (index) {
                let rev_index = 5 - index;
                var percent = 0;
                if (result["rate_count"].hasOwnProperty(rev_index)) {
                    var percent = result["rate_count"][rev_index];
                }
                $(this).width(`${percent}%`);
                $(this).find("span").text(`${percent}%`);
            })
        });
    });
});