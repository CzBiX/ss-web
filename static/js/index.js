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
            // TODO: show as n days ago.
            var time = data.startTime * 1000;
            var date = new Date(time);
            str = (date.getMonth() + 1) + '-' + (date.getDate() + 1);
        } else {
            str = 'Not run yet';
        }
        $time.val(str);
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
    }

    function showPwd(password) {
        $pwd.val(password);
    }
});
