$(document).ready(function() {

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
    $(".followButton").click(function() {
        var button = $(this);
        var isSubscribed = button.data("follow") === true;
        var comicId = button.data("comic-id");
        var resultMessage = button.siblings(".resultMessage_1");

        $.ajax({
            type: "POST",
            url: "/follow",
            data: JSON.stringify({"Follow": !isSubscribed, "comicId": comicId}),
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            success: function(data) {
                resultMessage.text(data.message);
                if (!isSubscribed) {
                    button.text("UnFollow");
                } else {
                    button.text("Follow");
                }
                button.data("follow", !isSubscribed);
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

