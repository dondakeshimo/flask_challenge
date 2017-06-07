// Support TLS-specific URLs, when appropriate.
if (window.location.protocol == "https:") {
  var ws_scheme = "wss://";
} else {
  var ws_scheme = "ws://"
};

var inbox  = new ReconnectingWebSocket(ws_scheme + location.host + "/index/receive");
var outbox = new ReconnectingWebSocket(ws_scheme + location.host + "/index/submit");

inbox.onmessage = function(message) {
  var data = JSON.parse(message.data);
  if(data.handle){
    $("#chat-text").append("<div class='panel panel-default'><div class='panel-heading'>" + $('<span/>').text(data.handle).html() + "</div><div class='panel-body'>" + $('<span/>').text(data.text).html() + "</div></div>");
    $("#chat-text").stop().animate({
    scrollTop: $('#chat-text')[0].scrollHeight
  }, 800);
  }else{
  $("#chat-member").html("<h4>" + $('<span/>').text(data.member).html() + "</h4>");
  }
};

inbox.onclose = function(){
    console.log('inbox closed');
};

outbox.onclose = function(){
    console.log('outbox closed');
};

$("#input-form").on("submit", function(event) {
  event.preventDefault();
  var text    = $("#input-text")[0].value;
  outbox.send(JSON.stringify({ handle: handle, roomnum: roomnum, text: text }));
  $("#input-text")[0].value = "";
});

var keep_ws = function(){
  outbox.send("please keep me");
  inbox.send("keep me please");
  console.log("I keep ws");
}

setInterval(keep_ws, 15000);
