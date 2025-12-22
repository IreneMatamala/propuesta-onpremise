function loadMessage() {
  fetch("/api/message")
    .then(res => res.json())
    .then(data => {
      document.getElementById("msg").innerText = data.message;
    });
}
