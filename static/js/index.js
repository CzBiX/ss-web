$(function(){
    var qrcode_api = '/qrcode?chl=';

    var $time = $('#time');
    var $start = $('#start');
    var $stop = $('#stop');
    var $status = $('#status');
    var $pwd = $('#password');
    var $newPwdBtn = $('#new_password');
    var $qrcodeUri = $('#qrcode_uri');
    var $qrcodeInfo = $('#qrcode_info');
    var $ssLink = $('#ss_link');

    updateStatus(data);

    $start.click(function(){
        disableBtn($start);
        sendAction('start');
    });

    $stop.click(function(){
        disableBtn($stop);
        sendAction('stop');
    });

    $newPwdBtn.click(function(){
        sendAction('new_password');
    });

    function sendAction(action) {
        $status.text('...');
        $pwd.val('...');

        return $.post('/', {action: action, id: sid}).success(function(data){
            updateStatus(data);
        }).error(function(){
            $status.text('Error');
        });
    }

    function updateStatus(data) {
        showTime(data);

        $status.text(data.running);
        if (data.running) {
            enableBtn($stop);
        } else {
            enableBtn($start);
        }

        showQrCode(data.qrcode);
        showPwd(data.password);
    }

    function showTime(data) {
        var str = null;
        if (data.running) {
            str = calcLeftTime(data.nextTime);
        } else {
            str = 'Not run yet';
        }
        $time.val(str);
    }

    function calcLeftTime(nextTime) {
        var diffTime = nextTime - (Date.now() / 1000);

        var diffMinutes = diffTime / 60;
        if (diffMinutes < 60) {
            return parseInt(diffMinutes) + ' minutes left';
        }

        var diffHours = diffMinutes / 60;
        if (diffHours < 24) {
            return parseInt(diffHours) + ' hours left';
        }

        var diffDays = diffHours / 24;
        return parseInt(diffDays) + ' days left';
    }

    function enableBtn($el) {
        $el.prop('disabled', false);
    }

    function disableBtn($el) {
        $el.prop('disabled', true);
    }

    function showQrCode(qrcode) {
        var url = qrcode_api + encodeURIComponent(qrcode);
        $qrcodeInfo.attr('src', url);
        $qrcodeUri.val('ss://' + qrcode);
        $ssLink.attr('href', 'ss://' + qrcode);
    }

    function showPwd(password) {
        $pwd.val(password);
    }
});
