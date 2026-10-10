(function () {
  const root = document.documentElement;
  const savedTheme = localStorage.getItem("carepoint-theme");
  if (savedTheme === "dark") root.classList.add("dark-mode");
  const themeBtn = document.getElementById("themeToggle");
  function updateThemeIcon() {
    const dark = root.classList.contains("dark-mode");
    if (themeBtn) themeBtn.textContent = dark ? "☀" : "☾";
  }
  function toggleTheme() {
    root.classList.toggle("dark-mode");
    localStorage.setItem("carepoint-theme", root.classList.contains("dark-mode") ? "dark" : "light");
    updateThemeIcon();
  }
  if (themeBtn) themeBtn.addEventListener("click", toggleTheme);
  const settingsTheme = document.getElementById("settingsThemeToggle");
  if (settingsTheme) settingsTheme.addEventListener("click", toggleTheme);
  updateThemeIcon();
  const menuToggle = document.getElementById("menuToggle");
  const sidebar = document.getElementById("sidebar");
  if (menuToggle && sidebar) menuToggle.addEventListener("click", () => sidebar.classList.toggle("sidebar-open"));
  document.querySelectorAll(".modal-backdrop").forEach(modal => {
    modal.addEventListener("click", e => { if (e.target === modal) modal.classList.remove("show"); });
  });
  document.addEventListener("keydown", e => {
    if (e.key === "Escape") document.querySelectorAll(".modal-backdrop.show").forEach(m => m.classList.remove("show"));
  });
})();
function toggleModal(id) {
  const modal = document.getElementById(id);
  if (modal) modal.classList.toggle("show");
}
