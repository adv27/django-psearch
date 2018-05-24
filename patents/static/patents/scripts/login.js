'use_strict';

$(document).ready(function () {
    // openlogin-form();
});


/*
 *
 * login-register modal
 * Autor: Creative Tim
 * Web-autor: creative.tim
 * Web script: http://creative-tim.com
 *
 */
function showRegisterForm() {
    $('.loginBox').fadeOut('fast', function () {
        $('.registerBox').fadeIn('fast');
        $('.login-footer').fadeOut('fast', function () {
            $('.register-footer').fadeIn('fast');
        });
        $('.modal-title').html('Đăng kí');
    });
    $('.error').removeClass('alert alert-danger').html('');

}

function showLoginForm() {
    $('#login-form .registerBox').fadeOut('fast', function () {
        $('.loginBox').fadeIn('fast');
        $('.register-footer').fadeOut('fast', function () {
            $('.login-footer').fadeIn('fast');
        });

        $('.modal-title').html('Đăng nhập');
    });
    $('.error').removeClass('alert alert-danger').html('');
}

function loginAjax() {
    var $form = $("div[class='form loginBox']:visible").find("form").first();
    var url = $form.attr("action");

    $.post({
        url: url,
        data: $form.serialize(),
        success: function (data) {
            if (data.success) {
                window.location.replace("/");
            } else {
                shakeModal(data.message);
            }
        }
    });
}

function registerAjax() {
    var $form = $("div[class='content registerBox']:visible").find("form").first();
    var url = $form.attr("action");

    $.post({
        url: url,
        data: $form.serialize(),
        success: function (data) {
            // if (data.success) {
            //     window.location.replace("/");
            // } else {
            //     shakeModal(data.message);
            // }
            shakeModal(data.message, data.success)
        }
    });
}

function shakeModal(mess, isSuccess = false) {
    $('#login-form').find('.modal-dialog').addClass('shake');
    $('.error').removeClass().addClass(`alert alert-${isSuccess ? 'success' : 'danger'}`).html(mess);
    $('input[type="password"]').val('');
    setTimeout(function () {
        $('#login-form .modal-dialog').removeClass('shake');
    }, 1000);
}

