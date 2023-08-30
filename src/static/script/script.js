$(document).ready(function() {
    const currentDate = new Date();
    const currentMonth = (currentDate.getMonth() + 1).toString().padStart(2, '0');
    const currentYear = currentDate.getFullYear().toString();

    document.getElementById('month-select').value = currentMonth;
    document.getElementById('year-select').value = currentYear;

    $(".subscribeButton").click(function() {
        var button = $(this);
        var isSubscribed = button.data("subscribed") === true;
        var comicId = button.data("comic-id");
        var resultMessage = button.siblings(".resultMessage");

        $.ajax({
            type: "POST",
            url: "/check",
            data: JSON.stringify({"subscribed": !isSubscribed, "comicId": comicId}),
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            success: function(data) {
                resultMessage.text(data.message);
                if (!isSubscribed) {
                    button.text("Unsubscribe");
                } else {
                    button.text("Subscribe");
                }
                button.data("subscribed", !isSubscribed);
            },
            error: function(error) {
                console.log(error);
            }
        });
    });
});
