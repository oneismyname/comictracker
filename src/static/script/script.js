$(document).ready(function() {
    const currentDate = new Date();
    const currentMonth = (currentDate.getMonth() + 1).toString().padStart(2, '0');
    const currentYear = currentDate.getFullYear().toString();

    document.getElementById('month-select').value = currentMonth;
    document.getElementById('year-select').value = currentYear;


    $(".subscribeButton").click(function() {
        var button = $(this);
        var isSubscribed = button.data("check") === true;
        var comicId = button.data("comic-id");
        var resultMessage = button.siblings(".resultMessage");

        $.ajax({
            type: "POST",
            url: "/check",
            data: JSON.stringify({"Check": !isSubscribed, "comicId": comicId}),
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            success: function(data) {
                resultMessage.text(data.message);
                if (!isSubscribed) {
                    button.text("UnCheck");
                } else {
                    button.text("Check");
                }
                button.data("check", !isSubscribed);
            },
            error: function(error) {
                console.log(error);
            }
        });
    });
});

document.addEventListener("DOMContentLoaded", () => {
            const inputField = document.getElementById("autocomplete-input1");
            const suggestionsDatalist = document.getElementById("list-comic");

            if (inputField && suggestionsDatalist) {
                inputField.addEventListener("input", async (event) => {
                    const text = event.target.value;
                    try {
                        const response = await fetch(`/autocomplete?text=${text}`);
                        if (!response.ok) {
                            throw new Error("Network response was not ok");
                        }
                        const suggestions = await response.json();

                        suggestionsDatalist.innerHTML = "";
                        suggestions.forEach(suggestion => {
                            const optionElement = document.createElement("option");
                            optionElement.value = suggestion;
                            suggestionsDatalist.appendChild(optionElement);
                        });
                    } catch (error) {
                        console.error("Error fetching autocomplete suggestions:", error);
                    }
                    });
                }
            });

$(".followButton").click(function() {
    var button = $(this);
    var isFollow = button.data("follow") === true;
    var comicId = button.data("comic-id");
    var resultMessage_1 = button.siblings(".resultMessage_1");

    $.ajax({
        type: "POST",
        url: "/follow",
        data: JSON.stringify({"Follow": !isFollow, "comicId": comicId}),
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function(data) {
            resultMessage_1.text(data.message);
            if (!isFollow) {
                button.text("UnFollow");
            } else {
                button.text("Follow");
            }
            button.data("follow", !isFollow);
        },
        error: function(error) {
            console.log(error);
        }
    });
});

