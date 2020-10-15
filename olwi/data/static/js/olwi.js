"use strict";

var deice = function() {
	var text = $("#text-config").val();
	$.post({
		url: API_URL+"/deice", 
		data: {},
		dataType: "json"
	}).done(function(json) {
		if (json.error != null)
			alert(json.error);
		else
			alert("De-icing started");
	}).fail(function() {
		alert("POST request error");
	});
};
