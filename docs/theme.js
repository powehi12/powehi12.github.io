/* Two manual themes. Keep the existing dark appearance until a reader chooses light. */
(function () {
  "use strict";
  var root = document.documentElement;
  var storageKey = "qbyang-color-mode";
  var button;
  var icons = {
    sun: '<circle cx="12" cy="12" r="4"></circle><path d="M12 2v2m0 16v2M2 12h2m16 0h2M4.93 4.93l1.42 1.42m11.3 11.3 1.42 1.42M4.93 19.07l1.42-1.42m11.3-11.3 1.42-1.42"></path>',
    moon: '<path d="M20.9 13A9 9 0 0 1 11 3.1 9 9 0 1 0 20.9 13Z"></path>'
  };

  function applyTheme(mode) {
    mode = mode === "light" ? "light" : "dark";
    root.setAttribute("data-color-mode", mode);
    root.setAttribute("data-light-theme", "light");
    root.setAttribute("data-dark-theme", "dark");
    var themeColor = document.querySelector('meta[name="theme-color"]');
    var colorScheme = document.querySelector('meta[name="color-scheme"]');
    if (themeColor) themeColor.setAttribute("content", mode === "light" ? "#ffffff" : "#262624");
    if (colorScheme) colorScheme.setAttribute("content", mode);
    if (button) {
      var label = mode === "dark" ? "切换到白天模式" : "切换到黑夜模式";
      button.setAttribute("aria-label", label);
      button.setAttribute("title", label);
      button.innerHTML = '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + icons[mode === "dark" ? "sun" : "moon"] + '</svg>';
    }
  }

  var savedMode;
  try { savedMode = window.localStorage.getItem(storageKey); } catch (error) {}
  applyTheme(savedMode);

  function initThemeButton() {
    if (document.getElementById("theme-toggle")) return;
    var header = document.getElementById("header");
    if (!header) return;
    var controls = header.querySelector(".title-right");
    if (!controls) {
      controls = document.createElement("div");
      controls.className = "title-right";
      header.appendChild(controls);
    }
    var legacy = header.querySelector('[onclick="modeSwitch()"]');
    button = document.createElement("button");
    button.id = "theme-toggle";
    button.type = "button";
    button.className = "btn btn-invisible circle";
    if (legacy) {
      legacy.parentNode.replaceChild(button, legacy);
    } else {
      controls.appendChild(button);
    }
    button.addEventListener("click", function () {
      var mode = root.getAttribute("data-color-mode") === "dark" ? "light" : "dark";
      applyTheme(mode);
      try { window.localStorage.setItem(storageKey, mode); } catch (error) {}
    });
    applyTheme(root.getAttribute("data-color-mode"));
  }

  window.addEventListener("storage", function (event) {
    if (event.key === storageKey || event.key === null) applyTheme(event.newValue);
  });
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initThemeButton);
  } else {
    initThemeButton();
  }
})();
