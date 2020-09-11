"use strict";

var setConfig = function(text) {
	$.post({
		url: API_URL+"/settings/set", 
		data: {text: text},
		dataType: "json"
	}).done(function(json) {
		if (json.error != null)
			alert(json.error);
		else
			alert("Success! Restarting in 5 seconds...");
	}).fail(function() {
		alert("POST request error");
	});
};

var configAccept = function() {
	var text = $("#text-config").val();
	$.post({
		url: API_URL+"/settings/check", 
		data: {text: text},
		dataType: "json"
	}).done(function(json) {
		if (json.error != null)
			alert(json.error);
		else
			if (confirm("Load new settings and restart?"))
				setConfig(text);
	}).fail(function() {
		alert("POST request error");
	});
};

var configReset = function() {
	$("#text-config").val(configText);
};

var configDefault = function() {
	$("#text-config").val(configTextDefault);
};
