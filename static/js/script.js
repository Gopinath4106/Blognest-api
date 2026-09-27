// AI Blog Nest — small client-side interactions (no external dependencies)

document.addEventListener("DOMContentLoaded", function () {
  // Mobile nav toggle
  var toggle = document.getElementById("navToggle");
  var links = document.getElementById("navLinks");
  if (toggle && links) {
    toggle.addEventListener("click", function () {
      links.classList.toggle("open");
    });
  }

  // Auto-dismiss flash messages after a few seconds
  document.querySelectorAll(".flash").forEach(function (el) {
    setTimeout(function () {
      el.style.transition = "opacity 0.4s ease";
      el.style.opacity = "0";
      setTimeout(function () { el.remove(); }, 400);
    }, 5000);
  });
});
