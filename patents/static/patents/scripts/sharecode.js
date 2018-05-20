var suggestions = [];
var xhr;

function download(id) {
    var temp = $('#download-temp-' + id).attr('value');
    var uuid = $('#download-uuid-' + id).attr('value');
    var win = window.open('/download?uuid=' + uuid + '&temp=' + temp, '_blank');
}

function no_accent_vietnamese(str) {
    str = str.replace(/à|á|ạ|ả|ã|â|ầ|ấ|ậ|ẩ|ẫ|ă|ằ|ắ|ặ|ẳ|ẵ/g, "a");
    str = str.replace(/è|é|ẹ|ẻ|ẽ|ê|ề|ế|ệ|ể|ễ/g, "e");
    str = str.replace(/ì|í|ị|ỉ|ĩ/g, "i");
    str = str.replace(/ò|ó|ọ|ỏ|õ|ô|ồ|ố|ộ|ổ|ỗ|ơ|ờ|ớ|ợ|ở|ỡ/g, "o");
    str = str.replace(/ù|ú|ụ|ủ|ũ|ư|ừ|ứ|ự|ử|ữ/g, "u");
    str = str.replace(/ỳ|ý|ỵ|ỷ|ỹ/g, "y");
    str = str.replace(/đ/g, "d");
    str = str.replace(/À|Á|Ạ|Ả|Ã|Â|Ầ|Ấ|Ậ|Ẩ|Ẫ|Ă|Ằ|Ắ|Ặ|Ẳ|Ẵ/g, "A");
    str = str.replace(/È|É|Ẹ|Ẻ|Ẽ|Ê|Ề|Ế|Ệ|Ể|Ễ/g, "E");
    str = str.replace(/Ì|Í|Ị|Ỉ|Ĩ/g, "I");
    str = str.replace(/Ò|Ó|Ọ|Ỏ|Õ|Ô|Ồ|Ố|Ộ|Ổ|Ỗ|Ơ|Ờ|Ớ|Ợ|Ở|Ỡ/g, "O");
    str = str.replace(/Ù|Ú|Ụ|Ủ|Ũ|Ư|Ừ|Ứ|Ự|Ử|Ữ/g, "U");
    str = str.replace(/Ỳ|Ý|Ỵ|Ỷ|Ỹ/g, "Y");
    str = str.replace(/Đ/g, "D");
    return str;
}

function highlight_search_complete(parent, search) {
    var parent_no_accent_vn = no_accent_vietnamese(parent);
    var search_no_accent_vn = no_accent_vietnamese(search);

    var n = [];
    var pos = parent_no_accent_vn.indexOf(search_no_accent_vn);
    while (pos > -1) {
        n.push(pos);
        pos = parent_no_accent_vn.indexOf(search_no_accent_vn, pos + 1);
    }

    if (n.length == 0)
        return parent;
    else {
        var result = "";
        var iFirst = 0;
        for (i = 0; i < n.length; i++) {
            result += parent.slice(iFirst, n[i]) + "<b>" + parent.slice(n[i], n[i] + search_no_accent_vn.length) + "</b>"
            iFirst = n[i] + search_no_accent_vn.length;
        }

        result += parent.slice(iFirst)
        return result;
    }
}


$('#search-term').autoComplete({
    minChars: 1,
    delay: 0,
    cache: 0,
    renderItem: function (item, search) {
        var title = item.title;
        var language = item.language;

        search = search.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&');
        var re = new RegExp("(" + search.split(' ').join('|') + ")", "gi");
        return '<div class="autocomplete-suggestion" data-val="' + title + '">' + "<span class='badge badge-primary'>" + language + "</span>" + highlight_search_complete(title, search) + '</div>';
    },
    source: function (term, response) {
        try {
            xhr.abort();
        } catch (e) {
        }
        xhr = $.getJSON(
            "/searchengine/get_suggestions", {
                q: term
            },
            function (data) {
                suggestions = data;
                response(data);
            });
    },
    onSelect: function (e, term, item) {
        var suggestion = _.find(suggestions, function (s) {
            if (s.title == term)
                return s.id
        });
        window.location = "/project?id=" + suggestion.id;
    }
});
