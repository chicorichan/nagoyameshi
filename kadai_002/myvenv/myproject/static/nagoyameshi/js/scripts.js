  // このままだと、script.jsは読み込まれてすぐに実行される。
// ページがすべて読み込まれない限り、 .notify_message_delete は読み込みできない。

window.addEventListener("load", () => {

    //DjangoMessageFrameWorkの削除機能 (素のJavaScriptに書き換え。)
    const notify_deletes    = document.querySelectorAll(".notify_message_delete");
    for (let notify_delete of notify_deletes ){
        // クリックされたとき、その要素の親要素.notify_messageを削除する。
        notify_delete.addEventListener("click", (event) => {
            event.currentTarget.closest(".notify_message").remove();
        });
    }

    //5秒経ったら自動的に消す

    setTimeout( () => {
        const messages  = document.querySelectorAll(".notify_message");
        for (let message of messages){
            message.remove();
        }
    }, 5000);


  //  flatpickrを発動させるためのscript
  window.addEventListener("load" , function (){ 

    let config_date = { 
        locale: "ja"
    }   
    let config_time = { 
        enableTime: true,
        noCalendar: true,
        dateFormat: "H:i",
        time_24hr: true,
        locale: "ja"
    }   
    let config_dt = { 
        enableTime: true,
        dateFormat: "Y-m-d H:i",
        locale: "ja"
    }

    flatpickr("#date", config_date);
    flatpickr("#time", config_time);
    flatpickr("#dt", config_dt);

});


});

