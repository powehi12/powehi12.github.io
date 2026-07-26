(function () {
  function initCollapsibleTOC() {
    var content = document.getElementById("content") || document.getElementById("postBody");
    if (!content) return;

    document.querySelectorAll(".toc").forEach(function (element) {
      element.remove();
    });

    var headings = Array.from(content.querySelectorAll("h1, h2, h3, h4")).filter(function (heading) {
      return heading.textContent.trim();
    });
    if (!headings.length) return;

    var usedIds = new Map();
    function makeId(text) {
      var base = text.trim().toLowerCase()
        .replace(/\s+/g, "-")
        .replace(/[^\w\u4e00-\u9fff\-+.：？！()（）]/g, "") || "section";
      var count = usedIds.get(base) || 0;
      usedIds.set(base, count + 1);
      return count ? base + "-" + (count + 1) : base;
    }

    headings.forEach(function (heading) {
      heading.id = makeId(heading.textContent);
    });

    var roots = [];
    var stack = [];
    headings.forEach(function (heading) {
      var node = {
        heading: heading,
        level: Number(heading.tagName.slice(1)),
        children: []
      };
      while (stack.length && stack[stack.length - 1].level >= node.level) {
        stack.pop();
      }
      if (stack.length) {
        stack[stack.length - 1].children.push(node);
      } else {
        roots.push(node);
      }
      stack.push(node);
    });

    var toc = document.createElement("nav");
    toc.className = "toc collapsible-toc";
    toc.setAttribute("aria-label", "文章目录");

    var title = document.createElement("div");
    title.className = "toc-title";
    title.textContent = "文章目录";
    toc.appendChild(title);

    function renderList(nodes) {
      var list = document.createElement("ul");
      list.className = "toc-list";

      nodes.forEach(function (node) {
        var item = document.createElement("li");
        item.className = "toc-item";

        var row = document.createElement("div");
        row.className = "toc-row";

        var toggle = document.createElement("button");
        toggle.type = "button";
        toggle.className = "toc-toggle";
        toggle.setAttribute("aria-expanded", "false");
        toggle.textContent = node.children.length ? "▸" : "";
        if (!node.children.length) {
          toggle.disabled = true;
          toggle.setAttribute("aria-hidden", "true");
        }

        var link = document.createElement("a");
        link.className = "toc-link";
        link.href = "#" + node.heading.id;
        link.textContent = node.heading.textContent.trim();
        link.addEventListener("click", function (event) {
          if (
            event.defaultPrevented ||
            event.button !== 0 ||
            event.metaKey ||
            event.ctrlKey ||
            event.shiftKey ||
            event.altKey
          ) {
            return;
          }

          event.preventDefault();
          node.heading.scrollIntoView({ behavior: "smooth", block: "start" });
          window.history.replaceState(null, "", link.href);
        });

        row.appendChild(toggle);
        row.appendChild(link);
        item.appendChild(row);

        if (node.children.length) {
          var children = renderList(node.children);
          children.classList.add("toc-children");
          children.hidden = true;
          item.appendChild(children);

          function setExpanded(expanded) {
            children.hidden = !expanded;
            toggle.setAttribute("aria-expanded", String(expanded));
            toggle.setAttribute("aria-label", expanded ? "收起子目录" : "展开子目录");
            toggle.textContent = expanded ? "▾" : "▸";
          }

          toggle.setAttribute("aria-label", "展开子目录");
          toggle.addEventListener("click", function () {
            setExpanded(toggle.getAttribute("aria-expanded") !== "true");
          });
          link.addEventListener("click", function () {
            setExpanded(toggle.getAttribute("aria-expanded") !== "true");
          });
        }

        list.appendChild(item);
      });

      return list;
    }

    toc.appendChild(renderList(roots));
    content.prepend(toc);

    var style = document.createElement("style");
    style.textContent = [
      ".collapsible-toc { position: fixed; top: 110px; left: calc(50% + 350px); width: 280px; max-height: 72vh; overflow-y: auto; border: 1px solid var(--borderColor-default, rgba(31,30,29,.15)); border-radius: 12px; padding: 15px; background: var(--bgColor-muted, #f5f4ed); box-shadow: 0 1px 2px rgba(0,0,0,.05); z-index: 20; }",
      ".collapsible-toc .toc-title { font-size: 13px; font-weight: 600; text-align: left; padding-bottom: 10px; margin-bottom: 8px; border-bottom: 1px solid var(--borderColor-default, rgba(31,30,29,.15)); }",
      ".collapsible-toc .toc-list { list-style: none; margin: 0; padding: 0; }",
      ".collapsible-toc .toc-children { padding-left: 16px; }",
      ".collapsible-toc .toc-children[hidden] { display: none !important; }",
      ".collapsible-toc .toc-row { display: flex; align-items: flex-start; gap: 4px; padding: 4px 0; }",
      ".collapsible-toc .toc-toggle { width: 22px; min-width: 22px; padding: 1px 0; border: 0; background: transparent; color: var(--fgColor-muted, #73726c); cursor: pointer; font-size: 14px; line-height: 1.5; }",
      ".collapsible-toc .toc-toggle:disabled { cursor: default; }",
      ".collapsible-toc .toc-link { color: var(--fgColor-muted, #73726c); text-decoration: none; font-size: 13px; line-height: 1.55; flex: 1; overflow-wrap: anywhere; }",
      ".collapsible-toc .toc-link:hover { color: var(--fgColor-default, #141413); text-decoration: underline; }",
      "@media (max-width: 1249px) { .collapsible-toc { position: static; width: auto; max-height: none; margin-bottom: 20px; } }"
    ].join("\n");
    document.head.appendChild(style);
  }

  function initCommentSection() {
    var button = document.getElementById("cmButton");
    var comments = document.getElementById("comments");
    if (!button || !comments || document.getElementById("comment-shell")) return;

    var counter = button.querySelector(".Counter");
    button.textContent = "打开评论区";
    if (counter) button.appendChild(counter);
    button.setAttribute("aria-label", "打开评论区");

    var shell = document.createElement("section");
    shell.id = "comment-shell";
    shell.className = "comment-shell";
    shell.setAttribute("aria-labelledby", "comment-shell-title");

    var header = document.createElement("div");
    header.className = "comment-shell-header";
    header.innerHTML = [
      '<div class="comment-shell-icon" aria-hidden="true">',
      '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">',
      '<path d="M21 15a4 4 0 0 1-4 4H8l-5 3 1.6-4.8A7.8 7.8 0 0 1 3 12a7 7 0 0 1 7-7h7a4 4 0 0 1 4 4z"></path>',
      '<path d="M8 11h8M8 15h5"></path>',
      '</svg></div>',
      '<div class="comment-shell-copy">',
      '<h2 id="comment-shell-title">讨论区</h2>',
      '<p>欢迎分享想法、补充资料或提出问题。</p>',
      '</div>',
      '<span class="comment-shell-badge">GitHub Issues</span>'
    ].join("");

    var note = document.createElement("p");
    note.className = "comment-shell-note";
    note.textContent = "评论公开可见，首次使用需要登录 GitHub。";

    var parent = button.parentNode;
    parent.insertBefore(shell, button);
    shell.appendChild(header);
    shell.appendChild(note);
    shell.appendChild(button);
    shell.appendChild(comments);

    var observer = new MutationObserver(function () {
      if (comments.querySelector("iframe.utterances")) {
        shell.classList.add("is-open");
        observer.disconnect();
      }
    });
    observer.observe(comments, { childList: true, subtree: true });

    var style = document.createElement("style");
    style.id = "comment-shell-style";
    style.textContent = [
      ".comment-shell { margin: 56px 0 12px; padding: 22px; border: 1px solid var(--borderColor-default, rgba(31,30,29,.15)); border-radius: 12px; background: var(--bgColor-muted, #f5f4ed); box-shadow: 0 1px 2px rgba(0,0,0,.05); overflow: hidden; }",
      ".comment-shell-header { display: flex; align-items: center; gap: 14px; }",
      ".comment-shell-icon { width: 40px; height: 40px; display: grid; place-items: center; flex: 0 0 auto; border: 1px solid rgba(159,79,54,.2); border-radius: 10px; color: #9f4f36; background: #f4e2da; }",
      ".comment-shell-copy { min-width: 0; flex: 1; }",
      ".comment-shell-copy h2 { margin: 0; padding: 0; border: 0; font-size: 20px; line-height: 1.3; color: var(--fgColor-default, #141413); }",
      ".comment-shell-copy p { margin: 4px 0 0; color: var(--fgColor-muted, #73726c); font-size: 14px; }",
      ".comment-shell-badge { flex: 0 0 auto; padding: 4px 9px; border: 1px solid var(--borderColor-default, rgba(31,30,29,.15)); border-radius: 999px; color: var(--fgColor-muted, #73726c); background: #fff; font-size: 12px; }",
      ".comment-shell-note { margin: 18px 0 0; padding-top: 16px; border-top: 1px solid var(--borderColor-muted, rgba(31,30,29,.1)); color: var(--fgColor-muted, #73726c); font-size: 13px; }",
      ".comment-shell #cmButton { min-height: 44px; height: auto; margin: 14px 0 0 !important; border: 1px solid #141413; border-radius: 8px; color: #fff; background: #141413; box-shadow: none; font-weight: 600; letter-spacing: 0; transition: background-color .16s ease, border-color .16s ease; }",
      ".comment-shell #cmButton::after { content: '  ↗'; opacity: .8; }",
      ".comment-shell #cmButton:hover:not(:disabled) { transform: none; border-color: #3d3d3a; background: #3d3d3a; filter: none; }",
      ".comment-shell #cmButton:disabled { cursor: wait; opacity: .72; }",
      ".comment-shell #cmButton .Counter { margin-left: 8px; background: rgba(255,255,255,.2); color: #fff; }",
      ".comment-shell #comments { margin-top: 0 !important; }",
      ".comment-shell #comments:empty { display: none; }",
      ".comment-shell.is-open .comment-shell-header { padding-bottom: 18px; border-bottom: 1px solid var(--borderColor-muted, rgba(31,30,29,.1)); }",
      ".comment-shell.is-open .comment-shell-note { display: none; }",
      ".comment-shell.is-open #comments { margin-top: 18px !important; }",
      ".comment-shell .utterances { max-width: none !important; margin: 0 !important; }",
      "@media (max-width: 600px) { .comment-shell { margin-top: 40px; padding: 18px; border-radius: 12px; } .comment-shell-badge { display: none; } .comment-shell-copy h2 { font-size: 18px; } }"
    ].join("\n");
    document.head.appendChild(style);
  }

  function initPageEnhancements() {
    initCollapsibleTOC();
    initCommentSection();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initPageEnhancements);
  } else {
    initPageEnhancements();
  }
})();
